# optimizer.py
# Otimizador de consultas baseado em heurísticas

import copy
from metadata import TABLES

def optimize_query(parsed_sql):
    """
    Aplica heurísticas de otimização na consulta SQL parseada.
    
    Args:
        parsed_sql (dict): Consulta SQL parseada
        
    Returns:
        tuple: (consulta otimizada, lista de etapas de otimização)
    """
    if not parsed_sql:
        return None, []
        
    optimized_sql = copy.deepcopy(parsed_sql)
    optimization_steps = []
        
    # Heurística 1: Aplicar primeiro as operações de seleção mais restritivas
    if optimized_sql['where']:
        # Obter as condições WHERE
        where_conditions = optimized_sql['where']
        
        # Classificar as condições por "restritividade" (uma abordagem simples)
        # Priorizar condições de igualdade (=) sobre desigualdade (>, <, >=, <=)
        # Dentro de cada grupo, priorizar condições sobre chaves primárias e estrangeiras
        restrictive_conditions = []
        less_restrictive_conditions = []
        
        for condition in where_conditions:
            # Verificar se é uma condição de igualdade
            if '=' in condition and '<>' not in condition and '<=' not in condition and '>=' not in condition:
                # Verificar se envolve uma chave primária ou estrangeira
                if 'id' in condition.lower():
                    restrictive_conditions.insert(0, condition)  # Inserir no início (maior prioridade)
                else:
                    restrictive_conditions.append(condition)  # Inserir no final
            else:
                less_restrictive_conditions.append(condition)
        
        # Reorganizar as condições WHERE
        optimized_sql['where'] = restrictive_conditions + less_restrictive_conditions
        
        if where_conditions != optimized_sql['where']:
            optimization_steps.append("Otimização: Reordenadas as condições WHERE para aplicar primeiro as operações de seleção mais restritivas.")
    
    # Heurística 2: Reordenar os JOINs para aplicar primeiro os mais restritivos
    if len(optimized_sql['joins']) > 1:
        # Calcular o "peso" de cada JOIN com base no número de condições de seleção sobre cada tabela
        join_weights = {}
        
        for i, join in enumerate(optimized_sql['joins']):
            table_name = join['table']
            table_alias = join['alias'] if join['alias'] else table_name
            
            # Contar condições WHERE que envolvem esta tabela
            table_conditions = 0
            for condition in optimized_sql['where']:
                if f"{table_name}." in condition.lower() or f"{table_alias}." in condition.lower():
                    table_conditions += 1
            
            # O peso é baseado no número de condições (mais condições = mais restritivo)
            join_weights[i] = table_conditions
        
        # Ordenar os JOINs pelo peso (mais restritivos primeiro)
        sorted_joins = sorted(
            [(i, join) for i, join in enumerate(optimized_sql['joins'])],
            key=lambda x: join_weights[x[0]],
            reverse=True  # Ordem decrescente (mais restritivos primeiro)
        )
        
        # Verificar se a ordem dos JOINs foi alterada
        if [i for i, _ in sorted_joins] != list(range(len(optimized_sql['joins']))):
            # A ordem foi alterada, então re-ordenar os JOINs
            optimized_sql['joins'] = [join for _, join in sorted_joins]
            optimization_steps.append("Otimização: Reordenados os JOINs para aplicar primeiro os mais restritivos.")
    
    # Heurística 3: Evitar produtos cartesianos
    # Isso é implicitamente garantido ao usar JOIN ... ON ao invés de vírgulas no FROM
    
    # Heurística 4: Aplicar projeções antecipadas para reduzir o número de atributos
    # Identificar apenas os campos que são necessários para a consulta final
    needed_columns = set()
    
    # Colunas no SELECT
    for col in optimized_sql['select']:
        if '.' in col:
            needed_columns.add(col.lower())
        else:
            # Coluna sem qualificação de tabela (verificar em todas as tabelas)
            for table in optimized_sql['from']:
                if f"{table}.{col}".lower() in [f"{t}.{c}".lower() for t in optimized_sql['from'] for c in TABLES[t]]:
                    needed_columns.add(f"{table}.{col}".lower())
    
    # Colunas nas condições WHERE
    for condition in optimized_sql['where']:
        # Simplificação: apenas extrair possíveis nomes de coluna
        # Na prática, precisaríamos de um parser mais sofisticado
        for part in re.split(r'[=<>!]+', condition):
            part = part.strip()
            if '.' in part:
                needed_columns.add(part.lower())
    
    # Colunas nas condições JOIN
    for join in optimized_sql['joins']:
        condition = join['condition']
        for part in re.split(r'[=<>!]+', condition):
            part = part.strip()
            if '.' in part:
                needed_columns.add(part.lower())
    
    # Adicionar informação de colunas necessárias para otimização
    optimized_sql['needed_columns'] = list(needed_columns)
    optimization_steps.append(f"Otimização: Identificadas {len(needed_columns)} colunas necessárias para a consulta.")
    
    return optimized_sql, optimization_steps

import re  # Adicionando import necessário para o módulo re