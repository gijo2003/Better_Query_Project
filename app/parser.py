# parser.py
# Módulo para análise de consultas SQL

import re
from metadata import (
    validate_qualified_column,
    get_correct_table_name,
    get_correct_column_name
)

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
    # 1) Remover comentários
    sql = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    sql = re.sub(r'#.*$', '', sql, flags=re.MULTILINE)
    
    # 2) Normalizar espaços em branco
    sql = re.sub(r'\s+', ' ', sql).strip()
    
    # 3) Deve começar com SELECT
    if not sql.lower().startswith('select '):
        raise SQLParseError("A consulta deve começar com SELECT")
    
    # Estrutura de resultado
    result = {
        'original_query': sql,
        'select': [],
        'from': [],
        'where': [],
        'joins': [],
        'aliases': {}
    }
    
    # 4) Extrair lista de colunas do SELECT
    select_match = re.search(r'select\s+(.*?)\s+from\s+', sql, re.IGNORECASE)
    if not select_match:
        raise SQLParseError("Formato inválido: não foi possível encontrar a cláusula FROM")
    
    raw_cols = [c.strip() for c in select_match.group(1).split(',')]
    # Guardo as colunas, mas a validação completa só depois de saber a tabela
    for col in raw_cols:
        if '.' in col:
            # coluna qualificada: tabela.coluna
            ok, tbl, c = validate_qualified_column(col)
            if not ok:
                raise SQLParseError(f"Coluna inválida: {col}")
            result['select'].append(f"{tbl}.{c}")
        else:
            # coluna sem tabela, validaremos depois
            result['select'].append(col)
    
    # 5) Extrair cláusula FROM + JOINs
    fj_match = re.search(r'from\s+(.*?)(?:where|$)', sql, re.IGNORECASE | re.DOTALL)
    if not fj_match:
        raise SQLParseError("Formato inválido: não foi possível analisar a cláusula FROM")
    fj_clause = fj_match.group(1).strip()
    
    # 5.1) Primeira tabela antes de qualquer JOIN
    first_match = re.match(r'^(.*?)(?:\s+join\b|$)', fj_clause, re.IGNORECASE)
    if first_match:
        segment = first_match.group(1).strip()
        # detectar alias
        if re.search(r'\s+as\s+', segment, re.IGNORECASE):
            tbl, alias = re.split(r'\s+as\s+', segment, flags=re.IGNORECASE)
            tbl, alias = tbl.strip(), alias.strip()
        else:
            parts = segment.split()
            tbl = parts[0].strip()
            alias = parts[1].strip() if len(parts) > 1 else None
        
        # lookup case-insensitive
        correct_tbl = get_correct_table_name(tbl)
        if correct_tbl is None:
            raise SQLParseError(f"Tabela não encontrada: {tbl}")
        tbl = correct_tbl
        
        result['from'].append(tbl)
        if alias:
            result['aliases'][alias.lower()] = tbl
    
    # 5.2) Extrair todos os JOINs
    for jm in re.finditer(r'join\s+(.*?)\s+on\s+(.*?)(?=\s+join\b|\s*$)', fj_clause, re.IGNORECASE):
        join_tbl_clause = jm.group(1).strip()
        join_cond       = jm.group(2).strip()
        
        if re.search(r'\s+as\s+', join_tbl_clause, re.IGNORECASE):
            jtbl, alias = re.split(r'\s+as\s+', join_tbl_clause, flags=re.IGNORECASE)
            jtbl, alias = jtbl.strip(), alias.strip()
        else:
            parts = join_tbl_clause.split()
            jtbl = parts[0].strip()
            alias = parts[1].strip() if len(parts) > 1 else None
        
        correct_jtbl = get_correct_table_name(jtbl)
        if correct_jtbl is None:
            raise SQLParseError(f"Tabela não encontrada: {jtbl}")
        jtbl = correct_jtbl
        
        result['from'].append(jtbl)
        if alias:
            result['aliases'][alias.lower()] = jtbl
        
        result['joins'].append({
            'table':    jtbl,
            'condition': join_cond,
            'alias':     alias
        })
    
    # 6) Revalidar colunas não-qualificadas do SELECT (usando a primeira tabela)
    default_table = result['from'][0] if result['from'] else None
    resolved_select = []
    for col in result['select']:
        if '.' in col:
            resolved_select.append(col)
        else:
            # coluna simples: auto-qualifica na tabela principal
            c = get_correct_column_name(default_table, col)
            if c is None:
                raise SQLParseError(f"Coluna inválida: {col} na tabela {default_table}")
            resolved_select.append(f"{default_table}.{c}")
    result['select'] = resolved_select
    
    # 7) Extrair cláusula WHERE (simplificado, só AND)
    where_match = re.search(r'where\s+(.*?)$', sql, re.IGNORECASE)
    if where_match:
        raw_conds = re.split(r'\s+and\s+', where_match.group(1), flags=re.IGNORECASE)
        result['where'] = [c.strip() for c in raw_conds]
    
    return result
