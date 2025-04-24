# metadata.py
# Definição dos metadados das tabelas

TABLES = {
    "Categoria": ["idCategoria", "Descricao"],
    "Produto": ["idProduto", "Nome", "Descricao", "Preco", "QuantEstoque", "Categoria_idCategoria"],
    "TipoCliente": ["idTipoCliente", "Descricao"],
    "Cliente": ["idCliente", "Nome", "Email", "Nascimento", "Senha", "TipoCliente_idTipoCliente", "DataRegistro"],
    "TipoEndereco": ["idTipoEndereco", "Descricao"],
    "Endereco": ["idEndereco", "EnderecoPadrao", "Logradouro", "Numero", "Complemento", "Bairro", "Cidade", "UF", "CEP", "TipoEndereco_idTipoEndereco", "Cliente_idCliente"],
    "Telefone": ["Numero", "Cliente_idCliente"],
    "Status": ["idStatus", "Descricao"],
    "Pedido": ["idPedido", "Status_idStatus", "DataPedido", "ValorTotalPedido", "Cliente_idCliente"],
    "Pedido_has_Produto": ["idPedidoProduto", "Pedido_idPedido", "Produto_idProduto", "Quantidade", "PrecoUnitario"]
}   

# Função auxiliar para validar se uma tabela existe
def table_exists(table_name):
    return table_name.lower() in [t.lower() for t in TABLES.keys()]

# Função auxiliar para validar se uma coluna existe em uma tabela
def column_exists(table_name, column_name):
    if not table_exists(table_name):
        return False
    
    table_key = next(key for key in TABLES.keys() if key.lower() == table_name.lower())
    return column_name.lower() in [col.lower() for col in TABLES[table_key]]

# Função para obter o nome correto da tabela (respeitando case-sensitivity)
def get_correct_table_name(table_name):
    if not table_exists(table_name):
        return None
    
    return next(key for key in TABLES.keys() if key.lower() == table_name.lower())

# Função para obter o nome correto da coluna (respeitando case-sensitivity)
def get_correct_column_name(table_name, column_name):
    if not table_exists(table_name) or not column_exists(table_name, column_name):
        return None
    
    table_key = get_correct_table_name(table_name)
    return next(col for col in TABLES[table_key] if col.lower() == column_name.lower())

# Função para validar uma coluna com tabela qualificada (formato: tabela.coluna)
def validate_qualified_column(qualified_column):
    parts = qualified_column.split('.')
    if len(parts) != 2:
        return False, None, None
    
    table_name, column_name = parts[0].strip(), parts[1].strip()
    
    if not table_exists(table_name):
        return False, None, None
    
    if not column_exists(table_name, column_name):
        return False, None, None
    
    correct_table = get_correct_table_name(table_name)
    correct_column = get_correct_column_name(table_name, column_name)
    
    return True, correct_table, correct_column