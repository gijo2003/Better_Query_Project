import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image
import io
import os

# Importar módulos do nosso projeto
from parser import parse_sql, SQLParseError
from relational_algebra import sql_to_relational_algebra
from optimizer import optimize_query
from graph_generator import generate_operator_graph
from execution_plan import get_execution_steps
from metadata import TABLES

# Configuração da página
st.set_page_config(
    page_title="Processador de Consultas SQL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("Processador de Consultas SQL")
st.markdown("### Visualizador e Otimizador de Consultas SQL")

# Inicializar estado da sessão
if 'parsed_sql' not in st.session_state:
    st.session_state.parsed_sql = None
if 'optimized_sql' not in st.session_state:
    st.session_state.optimized_sql = None
if 'relational_algebra' not in st.session_state:
    st.session_state.relational_algebra = None
if 'optimized_algebra' not in st.session_state:
    st.session_state.optimized_algebra = None
if 'operator_graph' not in st.session_state:
    st.session_state.operator_graph = None
if 'execution_plan' not in st.session_state:
    st.session_state.execution_plan = None

# Sidebar com informações sobre o banco de dados
with st.sidebar:
    st.header("Metadados do Banco")
    st.markdown("### Tabelas Disponíveis")
    
    # Exibir tabelas e colunas
    for table_name, columns in TABLES.items():
        with st.expander(f"{table_name}"):
            st.write(", ".join(columns))
    
    st.markdown("### Consultas de Exemplo")
    example_queries = {
        "Consulta Simples": "SELECT Nome, Email FROM cliente WHERE idCliente > 5",
        "Consulta com JOIN": "SELECT produto.Nome, categoria.Descricao FROM Produto produto JOIN Categoria categoria ON produto.Categoria_idCategoria = categoria.idCategoria",
        "Consulta Complexa": "SELECT cliente.nome, pedido.idPedido, pedido.DataPedido, Status.descricao, pedido.ValorTotalPedido, produto.QuantEstoque FROM Cliente JOIN pedido ON cliente.idcliente = pedido.Cliente_idCliente JOIN Status ON Status.idstatus = Pedido.status_idstatus JOIN pedido_has_produto ON pedido.idPedido = pedido_has_produto.Pedido_idPedido JOIN produto ON produto.idProduto = pedido_has_produto.Produto_idProduto WHERE Status.descricao = 'Aberto' AND cliente.TipoCliente_idTipoCliente = 1 AND pedido.ValorTotalPedido = 0 AND produto.QuantEstoque > 0"
    }
    
    selected_example = st.selectbox("Selecione um exemplo:", list(example_queries.keys()))
    
    if st.button("Carregar Exemplo"):
        # Inserir exemplo na área de texto principal
        st.session_state.sql_query = example_queries[selected_example]

# Área principal
# Entrada da consulta SQL
default_query = st.session_state.get('sql_query', '')
sql_query = st.text_area("Digite sua consulta SQL:", value=default_query, height=100)

# Botão para processar consulta
if st.button("Processar Consulta"):
    if sql_query:
        try:
            # Limpar estados anteriores
            st.session_state.parsed_sql = None
            st.session_state.optimized_sql = None
            st.session_state.relational_algebra = None
            st.session_state.optimized_algebra = None
            st.session_state.operator_graph = None
            st.session_state.execution_plan = None
            
            # Processar a consulta SQL
            with st.spinner("Analisando SQL..."):
                # 1. Parsear a consulta
                parsed_sql = parse_sql(sql_query)
                st.session_state.parsed_sql = parsed_sql
                
                # 2. Converter para álgebra relacional
                relational_algebra = sql_to_relational_algebra(parsed_sql)
                st.session_state.relational_algebra = relational_algebra
                
                # 3. Otimizar a consulta
                optimized_sql, optimization_steps = optimize_query(parsed_sql)
                if optimized_sql is None:
                    # Se a otimização falhar, use a consulta original como fallback
                    optimized_sql = copy.deepcopy(parsed_sql)
                    optimization_steps = ["Nenhuma otimização aplicada."]
                    
                optimized_sql['optimization_steps'] = optimization_steps
                st.session_state.optimized_sql = optimized_sql
                
                # 4. Converter a consulta otimizada para álgebra relacional
                optimized_algebra = sql_to_relational_algebra(optimized_sql)
                st.session_state.optimized_algebra = optimized_algebra
                
                # 5. Gerar o grafo de operadores
                G, graph_img_path = generate_operator_graph(parsed_sql, optimized_sql)
                st.session_state.operator_graph = (G, graph_img_path)
                
                # 6. Gerar o plano de execução
                execution_plan = get_execution_steps(parsed_sql, optimized_sql, G)
                st.session_state.execution_plan = execution_plan
            
            st.success("Consulta processada com sucesso!")
        
        except SQLParseError as e:
            st.error(f"Erro ao analisar SQL: {str(e)}")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
    else:
        st.warning("Por favor, digite uma consulta SQL")

# Exibir resultados do processamento
if st.session_state.parsed_sql:
    # Layout em abas para organizar as informações
    tab1, tab2, tab3, tab4 = st.tabs(["Álgebra Relacional", "Grafo de Operadores", "Plano de Execução", "Detalhes da Consulta"])
    
    with tab1:
        # Exibir a álgebra relacional
        st.subheader("Álgebra Relacional Original")
        st.code(st.session_state.relational_algebra)
        
        st.subheader("Álgebra Relacional Otimizada")
        st.code(st.session_state.optimized_algebra)
        
        # Explicação das otimizações
        st.subheader("Otimizações Aplicadas")
        for step in st.session_state.optimized_sql['optimization_steps']:
            st.info(step)
    
    with tab2:
        # Exibir o grafo de operadores
        st.subheader("Grafo de Operadores da Consulta")
        
        # Carregar a imagem do grafo
        if os.path.exists(st.session_state.operator_graph[1]):
            image = Image.open(st.session_state.operator_graph[1])
            st.image(image, caption="Grafo de Operadores", use_column_width=True)
        else:
            st.error("Erro ao gerar o grafo de operadores")
        
        st.markdown("""
        **Legenda:**
        - **Vermelho claro**: Tabelas base
        - **Amarelo claro**: Operações de junção (JOIN)
        - **Verde claro**: Operações de seleção (WHERE)
        - **Azul claro**: Operações de projeção (SELECT)
        """)
    
    with tab3:
        # Exibir o plano de execução
        st.subheader("Plano de Execução da Consulta")
        for i, step in enumerate(st.session_state.execution_plan, 1):
            if "Otimização:" in step:
                st.info(f"Passo {i}: {step}")
            else:
                st.write(f"Passo {i}: {step}")
    
    with tab4:
        # Exibir detalhes do parsing
        st.subheader("Detalhes da Consulta Parseada")
        
        # SELECT
        st.write("**Colunas selecionadas:**")
        st.code(", ".join(st.session_state.parsed_sql['select']))
        
        # FROM
        st.write("**Tabelas:**")
        st.code(", ".join(st.session_state.parsed_sql['from']))
        
        # WHERE
        if st.session_state.parsed_sql['where']:
            st.write("**Condições WHERE:**")
            for condition in st.session_state.parsed_sql['where']:
                st.code(condition)
        
        # JOIN
        if st.session_state.parsed_sql['joins']:
            st.write("**Junções:**")
            for join in st.session_state.parsed_sql['joins']:
                st.code(f"JOIN {join['table']} ON {join['condition']}")

# Rodapé
st.markdown("---")
st.markdown("Processador de Consultas SQL - Trabalho Acadêmico")

# Função para limpar arquivos temporários quando o aplicativo for fechado
def cleanup():
    # Remover arquivos temporários
    if 'operator_graph' in st.session_state and st.session_state.operator_graph:
        try:
            os.remove(st.session_state.operator_graph[1])
        except:
            pass

# Registrar função de limpeza
import atexit
atexit.register(cleanup)

if __name__ == "__main__":
    # Este bloco é executado quando o script é executado diretamente
    pass