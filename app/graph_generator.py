# graph_generator.py
# Gerador de grafo de operadores

import networkx as nx
import matplotlib.pyplot as plt
import tempfile
import os

def generate_operator_graph(parsed_sql, optimized_sql):
    """
    Gera um grafo de operadores para a consulta SQL.
    
    Args:
        parsed_sql (dict): Consulta SQL parseada original
        optimized_sql (dict): Consulta SQL otimizada
        
    Returns:
        tuple: (grafo NetworkX, caminho para a imagem do grafo)
    """
    # Criar um grafo direcionado
    G = nx.DiGraph()
    
    # Nós para as tabelas base
    table_nodes = []
    for table in optimized_sql['from']:
        node_id = f"table_{table}"
        G.add_node(node_id, label=table, type="table")
        table_nodes.append(node_id)
    
    # Nós para as junções
    last_node = table_nodes[0]
    for i, join in enumerate(optimized_sql['joins']):
        join_table = join['table']
        join_condition = join['condition']
        
        # Nó da tabela de junção
        join_table_node = f"table_{join_table}"
        if join_table_node not in G:
            G.add_node(join_table_node, label=join_table, type="table")
        
        # Nó da operação de junção
        join_node = f"join_{i}"
        G.add_node(join_node, label=f"JOIN ON\n{join_condition}", type="join")
        
        # Conexões
        G.add_edge(last_node, join_node)
        G.add_edge(join_table_node, join_node)
        
        last_node = join_node
    
    # Nó para as condições WHERE (se houver)
    if optimized_sql['where']:
        where_conditions = " AND ".join(optimized_sql['where'])
        where_node = "where"
        G.add_node(where_node, label=f"WHERE\n{where_conditions}", type="where")
        G.add_edge(last_node, where_node)
        last_node = where_node
    
    # Nó para a projeção (SELECT)
    select_columns = ", ".join(optimized_sql['select'])
    select_node = "select"
    G.add_node(select_node, label=f"SELECT\n{select_columns}", type="select")
    G.add_edge(last_node, select_node)
    
    # Desenhar o grafo
    plt.figure(figsize=(12, 8))
    
    # Definir posições dos nós
    pos = nx.spring_layout(G, seed=42)
    
    # Cores para os diferentes tipos de nós
    node_colors = {
        "table": "lightcoral",
        "join": "lightyellow",
        "where": "lightgreen",
        "select": "lightblue"
    }
    
    # Desenhar nós
    for node_type in node_colors:
        node_list = [node for node in G.nodes() if G.nodes[node].get("type") == node_type]
        nx.draw_networkx_nodes(G, pos, nodelist=node_list, node_color=node_colors[node_type], node_size=2000, alpha=0.8)
    
    # Desenhar arestas
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=20, width=1.5)
    
    # Desenhar rótulos
    labels = {node: G.nodes[node]["label"] for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_family="sans-serif", font_weight="bold")
    
    # Salvar a imagem
    temp_dir = tempfile.gettempdir()
    image_path = os.path.join(temp_dir, "operator_graph.png")
    plt.tight_layout()
    plt.axis("off")
    plt.savefig(image_path, format="PNG", dpi=200, bbox_inches="tight")
    plt.close()
    
    return G, image_path