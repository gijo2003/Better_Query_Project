# relational_algebra.py
# Conversor SQL para álgebra relacional

def sql_to_relational_algebra(parsed_sql):
    """
    Converte uma consulta SQL parseada para notação de álgebra relacional.
    
    Args:
        parsed_sql (dict): Consulta SQL parseada
        
    Returns:
        str: Expressão em álgebra relacional
    """
    # Construir a expressão de álgebra relacional
    result = ""
    
    # Tabelas base
    tables = parsed_sql['from']
    
    # Iniciar com as tabelas base e junções
    if len(tables) == 1:
        base_expr = tables[0]
    else:
        # Construir junções
        base_expr = tables[0]
        
        for join in parsed_sql['joins']:
            join_table = join['table']
            join_condition = join['condition']
            base_expr = f"({base_expr} ⋈_{{{join_condition}}} {join_table})"
    
    # Adicionar seleções (WHERE)
    if parsed_sql['where']:
        conditions = " ∧ ".join([f"({cond})" for cond in parsed_sql['where']])
        base_expr = f"σ_{{{conditions}}}({base_expr})"
    
    # Adicionar projeções (SELECT)
    columns = ", ".join(parsed_sql['select'])
    result = f"π_{{{columns}}}({base_expr})"
    
    return result