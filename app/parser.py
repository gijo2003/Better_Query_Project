# parser.py
# Módulo para análise de consultas SQL

import re
from metadata import table_exists, column_exists, validate_qualified_column

class SQLParseError(Exception):
    """Exceção para erros de parse do SQL"""
    pass

def parse_sql(sql_query):
    """
    Analisa uma consulta SQL e a converte em um dicionário com suas partes componentes.
    
    Args:
        sql_query (str): A consulta SQL a ser analisada
        
    Returns:
        dict: Um dicionário contendo as partes componentes da consulta
        
    Raises:
        SQLParseError: Se ocorrer algum erro durante a análise
    """
    # Remover comentários
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    sql_query = re.sub(r'#.*$', '', sql_query, flags=re.MULTILINE)
    
    # Normalizar espaços em branco
    sql_query = re.sub(r'\s+', ' ', sql_query).strip()
    
    # Converter para minúsculas (facilitar o parsing)
    sql_lower = sql_query.lower()
    
    # Verificar se é uma consulta SELECT
    if not sql_lower.startswith('select '):
        raise SQLParseError("A consulta deve começar com SELECT")
    
    # Inicializar estrutura de resultado
    result = {
        'original_query': sql_query,
        'select': [],
        'from': [],
        'where': [],
        'joins': [],
        'aliases': {}
    }
    
    # Extrair cláusula SELECT
    select_pattern = r'select\s+(.*?)\s+from\s+'
    select_match = re.search(select_pattern, sql_lower, re.IGNORECASE)
    
    if not select_match:
        raise SQLParseError("Formato inválido: Não foi possível encontrar a cláusula FROM")
    
    select_columns = select_match.group(1).split(',')
    select_columns = [col.strip() for col in select_columns]
    
    # Verificar e validar as colunas selecionadas
    for col in select_columns:
        if '.' in col:
            # Coluna qualificada (tabela.coluna)
            is_valid, table, column = validate_qualified_column(col)
            if not is_valid:
                raise SQLParseError(f"Coluna inválida: {col}")
            result['select'].append(f"{table}.{column}")
        else:
            # Coluna não qualificada (será validada depois de identificar as tabelas)
            result['select'].append(col)
    
    # Extrair cláusulas FROM e JOIN
    from_join_pattern = r'from\s+(.*?)(?:where|$)'
    from_join_match = re.search(from_join_pattern, sql_lower, re.IGNORECASE | re.DOTALL)
    
    if not from_join_match:
        raise SQLParseError("Formato inválido: Não foi possível analisar a cláusula FROM")
    
    from_join_clause = from_join_match.group(1).strip()
    
    # Identificar JOINs
    join_pattern = r'join\s+(.*?)\s+on\s+(.*?)(?=\s+join|\s*$)'
    join_matches = re.finditer(join_pattern, from_join_clause, re.IGNORECASE)
    
    # Primeiro, extrair a primeira tabela (antes de qualquer JOIN)
    first_table_pattern = r'^(.*?)(?:join|$)'
    first_table_match = re.search(first_table_pattern, from_join_clause, re.IGNORECASE)
    
    if first_table_match:
        first_table = first_table_match.group(1).strip()
        # Verificar se há alias
        if ' as ' in first_table.lower():
            table_parts = re.split(r'\s+as\s+', first_table, flags=re.IGNORECASE)
            table_name = table_parts[0].strip()
            alias = table_parts[1].strip()
        else:
            table_parts = first_table.split()
            table_name = table_parts[0].strip()
            alias = table_parts[1].strip() if len(table_parts) > 1 else None

        # Validar a tabela - AQUI É O PROBLEMA
        if not table_exists(table_name):
            raise SQLParseError(f"Tabela não encontrada: {table_name}")
        
        result['from'].append(table_name)
        if alias:
            result['aliases'][alias.lower()] = table_name
    
    # Extrair as junções
    for match in join_matches:
        join_table = match.group(1).strip()
        join_condition = match.group(2).strip()
        
        # Verificar se há alias
        if ' as ' in join_table.lower():
            table_parts = re.split(r'\s+as\s+', join_table, flags=re.IGNORECASE)
            table_name = table_parts[0].strip()
            alias = table_parts[1].strip()
        else:
            table_parts = join_table.split()
            table_name = table_parts[0].strip()
            alias = table_parts[1].strip() if len(table_parts) > 1 else None
        
        # Validar a tabela
        if not table_exists(table_name):
            raise SQLParseError(f"Tabela não encontrada: {table_name}")
        
        result['from'].append(table_name)
        if alias:
            result['aliases'][alias.lower()] = table_name
        
        result['joins'].append({
            'table': table_name,
            'condition': join_condition,
            'alias': alias
        })
    
    # Extrair cláusula WHERE
    where_pattern = r'where\s+(.*?)$'
    where_match = re.search(where_pattern, sql_lower, re.IGNORECASE)
    
    if where_match:
        where_clause = where_match.group(1).strip()
        
        # Separar condições por AND
        # Nota: Esta é uma abordagem simplificada, lidar com operadores OR e parênteses exigiria um parser mais complexo
        conditions = re.split(r'\s+and\s+', where_clause, flags=re.IGNORECASE)
        result['where'] = [condition.strip() for condition in conditions]
    
    return result