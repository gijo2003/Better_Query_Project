# graph_generator.py
# Gerador de grafo de operadores a partir da árvore de Álgebra Relacional otimizada

import networkx as nx
import matplotlib.pyplot as plt
import tempfile
import os
import textwrap
from relational_algebra import Relation, Selection, Projection, Join
import matplotlib.patches as mpatches


def resumir_label(node, max_len=30):
    # Projeção: mostra π e as primeiras colunas
    if isinstance(node, Projection):
        cols = ', '.join(node.attributes[:2])
        if len(node.attributes) > 2:
            cols += ', ...'
        return f"π{{{cols}}}"
    # Seleção: mostra σ e condição resumida
    elif isinstance(node, Selection):
        cond = str(node.condition)
        if len(cond) > 15:
            cond = cond[:12] + '...'
        return f"σ{{{cond}}}"
    # Junção: mostra ⋈ e condição resumida
    elif isinstance(node, Join):
        cond = str(node.condition)
        if len(cond) > 15:
            cond = cond[:12] + '...'
        return f"⋈{{{cond}}}"
    # Tabela: nome
    elif isinstance(node, Relation):
        return node.name
    else:
        label = str(node)
        return label[:max_len] + ("..." if len(label) > max_len else "")


def generate_operator_graph(original_tree, optimized_tree):
    """
    Gera um grafo hierárquico para a árvore de Álgebra Relacional otimizada,
    com layout bottom-up, espaçamento controlado, labels quebrados em múltiplas linhas,
    e estilos distintos por tipo de nó, incluindo legenda de cores.

    Args:
        original_tree: raiz da árvore original (não usado)
        optimized_tree: raiz da árvore otimizada

    Returns:
        Tuple[DiGraph, str]: grafo NetworkX e caminho da imagem gerada
    """
    tree = optimized_tree
    G = nx.DiGraph()

    # 1) Construção recursiva de nós e arestas
    def _add(node, is_root=False):
        nid = id(node)
        if nid in G:
            return
        # Label informativo e quebra de linha
        short_label = resumir_label(node, 30)
        wrapped_label = textwrap.fill(short_label, width=18)
        # Determina tipo e forma de nó
        if isinstance(node, Relation):
            ntype, shape = 'table', 'o'
        elif isinstance(node, Join):
            ntype, shape = 'join', 'D'
        elif isinstance(node, Selection):
            ntype, shape = 'where', 's'
        elif isinstance(node, Projection):
            ntype, shape = 'select', 's'
        else:
            ntype, shape = 'other', 'o'
        # Destaca o nó raiz (projeção final)
        border = 4.0 if is_root else 1.0
        G.add_node(nid, label=wrapped_label, type=ntype, shape=shape, tooltip=str(node), border=border)
        # Adiciona arestas para filhos
        if hasattr(node, 'child'):
            _add(node.child)
            G.add_edge(nid, id(node.child))
        if hasattr(node, 'left') and hasattr(node, 'right'):
            for sub in (node.left, node.right):
                _add(sub)
                G.add_edge(nid, id(sub))

    _add(tree, is_root=True)

    # 2) Posicionamento com Graphviz 'dot' (rankdir bottom-to-top)
    try:
        pos = nx.nx_agraph.graphviz_layout(
            G,
            prog='dot',
            args='-Grankdir=BT -Gnodesep=3.0 -Granksep=5.0 -Gmargin=1.5'
        )
    except Exception:
        pos = nx.spring_layout(G, seed=42)

    # 3) Desenho do grafo
    fig, ax = plt.subplots(figsize=(18, 12))  # Aumenta ainda mais o tamanho do grafo
    color_map = {
        'table':  'lightcoral',
        'join':   'lightgoldenrodyellow',
        'where':  'lightgreen',
        'select': 'lightskyblue',
        'other':  'lightgrey'
    }
    # Desenha nós por formato e cor
    for shape in set(nx.get_node_attributes(G, 'shape').values()):
        nodes = [n for n, d in G.nodes(data=True) if d['shape'] == shape]
        colors = [color_map[G.nodes[n]['type']] for n in nodes]
        borders = [G.nodes[n].get('border', 1.0) for n in nodes]
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=nodes,
            node_color=colors,
            node_shape=shape,
            node_size=2200,  # aumenta o tamanho dos nós
            linewidths=borders,
            edgecolors='black',
            alpha=0.95,
            ax=ax
        )
    # Desenha arestas e rótulos
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=18, width=1.6, ax=ax)
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(
        G,
        pos,
        labels=labels,
        font_size=12,  # aumenta a fonte
        font_family='sans-serif',
        font_weight='bold',
        ax=ax
    )

    # Adiciona legenda de cores
    legend_handles = [
        mpatches.Patch(color=color, label=ntype.capitalize())
        for ntype, color in color_map.items()
    ]
    ax.legend(
        handles=legend_handles,
        title='Tipos de Operadores',
        loc='lower left',
        fontsize=8,
        title_fontsize=9,
        frameon=True
    )

    ax.set_axis_off()
    plt.tight_layout()

    # 4) Salva imagem em diretório temporário
    tmp = tempfile.gettempdir()
    path = os.path.join(tmp, 'operator_graph.png')
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)

    return G, path
