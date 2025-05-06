# app/main.py

import streamlit as st
import os
from PIL import Image

# Importar nossos módulos
from parser import parse_sql, SQLParseError
from relational_algebra import ast_to_relational_algebra
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

st.title("Processador de Consultas SQL")
st.markdown("### Visualizador e Otimizador de Árvores de Álgebra Relacional")

# --- Inicializa o estado da sessão ---
for key in (
    'sql_query',
    'parsed_sql',
    'relational_algebra',
    'optimized_algebra',
    'ra_optimization_steps',
    'operator_graph',
    'execution_plan'
):
    if key not in st.session_state:
        # ra_optimization_steps deve ser lista vazia por padrão
        st.session_state[key] = [] if key == 'ra_optimization_steps' else None

# --- Sidebar: metadados e exemplos ---
with st.sidebar:
    st.header("Metadados do Banco")
    st.markdown("**Tabelas Disponíveis**")
    for tbl, cols in TABLES.items():
        with st.expander(tbl):
            st.write(", ".join(cols))

    st.markdown("**Consultas de Exemplo**")
    example_queries = {
        "Consulta Simples":       "SELECT Nome, Email FROM cliente WHERE idCliente > 5",
        "Consulta com JOIN":      "SELECT produto.Nome, categoria.Descricao FROM Produto produto JOIN Categoria categoria ON produto.Categoria_idCategoria = categoria.idCategoria",
        "Consulta Complexa":      (
            "SELECT cliente.Nome, pedido.idPedido, pedido.DataPedido, Status.Descricao, pedido.ValorTotalPedido, produto.QuantEstoque "
            "FROM Cliente "
            "JOIN pedido ON cliente.idCliente = pedido.Cliente_idCliente "
            "JOIN Status ON Status.idStatus = pedido.Status_idStatus "
            "JOIN pedido_has_produto ON pedido.idPedido = pedido_has_produto.Pedido_idPedido "
            "JOIN produto ON produto.idProduto = pedido_has_produto.Produto_idProduto "
            "WHERE Status.Descricao = 'Aberto' AND cliente.TipoCliente_idTipoCliente = 1 "
            "AND pedido.ValorTotalPedido = 0 AND produto.QuantEstoque > 0"
        )
    }
    escolha = st.selectbox("Selecione um exemplo:", list(example_queries.keys()))
    if st.button("Carregar Exemplo"):
        st.session_state.sql_query = example_queries[escolha]

# --- Área principal: entrada SQL ---
sql_query = st.text_area(
    "Digite sua consulta SQL:",
    value=st.session_state.sql_query or "",
    height=100
)

if st.button("Processar Consulta"):
    if not sql_query.strip():
        st.warning("Por favor, digite uma consulta SQL.")
    else:
        try:
            # Limpar estados anteriores (exceto sql_query)
            for k in (
                'parsed_sql',
                'relational_algebra',
                'optimized_algebra',
                'operator_graph',
                'execution_plan'
            ):
                st.session_state[k] = None
            # Zera as otimizações para lista vazia
            st.session_state.ra_optimization_steps = []

            # 1) Parse SQL
            parsed = parse_sql(sql_query)
            st.session_state.parsed_sql = parsed

            # 2) Converter para árvore de Álgebra Relacional original
            orig_ra = ast_to_relational_algebra(parsed)
            st.session_state.relational_algebra = orig_ra

            # 3) Aplicar otimizações sobre a árvore de RA
            # ...
            opt_ra, steps = optimize_query(parsed)
            # Se por algum motivo não houve retorno, caia no original
            if opt_ra is None:
                opt_ra = orig_ra
                steps  = ["Nenhuma otimização aplicada."]
            st.session_state.optimized_algebra     = opt_ra
            st.session_state.ra_optimization_steps = steps

            # 4) Gere sempre um grafo, mesmo que otimizado == original
            G, path = generate_operator_graph(orig_ra, opt_ra)
            st.session_state.operator_graph = (G, path)
            # ...


            # 5) Gerar o plano de execução (incluindo passos de otimização)
            plan = get_execution_steps(orig_ra, opt_ra, G, st.session_state.ra_optimization_steps)
            st.session_state.execution_plan = plan

            st.success("Consulta processada com sucesso!")

        except SQLParseError as e:
            st.error(f"Erro ao analisar SQL: {e}")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")

# --- Aba de resultados ---
if st.session_state.parsed_sql:
    tab1, tab2, tab3, tab4 = st.tabs([
        "Árvore de Álgebra Relacional",
        "Grafo de Operadores",
        "Plano de Execução",
        "Detalhes da Consulta"
    ])

    # 1) Árvore de Álgebra Relacional
    with tab1:
        st.subheader("Árvore de Álgebra Relacional Original")
        st.code(str(st.session_state.relational_algebra))

        st.subheader("Árvore de Álgebra Relacional Otimizada")
        for s in st.session_state.ra_optimization_steps or []:
            st.info(s)
        st.code(str(st.session_state.optimized_algebra))

    # 2) Grafo de Operadores
   # Aba 2: Grafo de Operadores
    with tab2:
        st.subheader("Grafo de Operadores")
        if st.session_state.operator_graph:
            G, path = st.session_state.operator_graph
            if os.path.exists(path):
                st.image(Image.open(path), use_column_width=True)
            else:
                st.error("Erro ao carregar o grafo.")
        else:
            st.error("Grafo não disponível.")


    # 3) Plano de Execução
    with tab3:
        st.subheader("Plano de Execução")
        for i, step in enumerate(st.session_state.execution_plan or [], start=1):
            st.write(f"Passo {i}: {step}")

    # 4) Detalhes do Parse
    with tab4:
        st.subheader("Detalhes da Consulta Parseada")
        st.markdown("**SELECT**")
        st.code(", ".join(st.session_state.parsed_sql['select']))
        st.markdown("**FROM**")
        st.code(", ".join(st.session_state.parsed_sql['from']))
        if st.session_state.parsed_sql.get('joins'):
            st.markdown("**JOINs**")
            for j in st.session_state.parsed_sql['joins']:
                st.code(f"JOIN {j['table']} ON {j['condition']}")
        if st.session_state.parsed_sql.get('where'):
            st.markdown("**WHERE**")
            for cond in st.session_state.parsed_sql['where']:
                st.code(cond)

# --- Limpeza de arquivos temporários ---
def cleanup():
    if st.session_state.operator_graph:
        try:
            os.remove(st.session_state.operator_graph[1])
        except FileNotFoundError:
            pass

import atexit
atexit.register(cleanup)
