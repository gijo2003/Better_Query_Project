# execution_plan.py
# Gerador de plano de execução

def get_execution_steps(parsed_sql, optimized_sql, graph):
    """
    Gera o plano de execução da consulta SQL.
    
    Args:
        parsed_sql (dict): Consulta SQL parseada original
        optimized_sql (dict): Consulta SQL otimizada
        graph (networkx.DiGraph): Grafo de operadores
        
    Returns:
        list: Lista de passos de execução
    """
    steps = []
    
    # Adicionar passos de otimização
    if 'optimization_steps' in optimized_sql:
        steps.extend(optimized_sql['optimization_steps'])
    
    # Acessar tabelas base
    for table in optimized_sql['from']:
        steps.append(f"Acesso à tabela base: {table}")
    
    # Aplicar junções
    for i, join in enumerate(optimized_sql['joins']):
        steps.append(f"Junção: {join['table']} ON {join['condition']}")
    
    # Aplicar filtros WHERE
    for i, condition in enumerate(optimized_sql['where']):
        steps.append(f"Filtro: {condition}")
    
    # Projeção final
    columns = ", ".join(optimized_sql['select'])
    steps.append(f"Projeção: {columns}")
    
    return steps