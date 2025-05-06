# execution_plan.py
# Gerador de plano de execução baseado na árvore de Álgebra Relacional

from relational_algebra import Relation, Selection, Join, Projection


def get_execution_steps(original_tree, optimized_tree, graph, optimization_steps=None):
    """
    Gera o plano de execução da árvore de Álgebra Relacional otimizada.

    Args:
        original_tree: nó raiz da árvore de RA original (não usado)
        optimized_tree: nó raiz da árvore de RA otimizada
        graph: grafo de operadores (NetworkX DiGraph)
        optimization_steps (list, opcional): lista de strings com passos de otimização

    Returns:
        list: lista de passos executáveis
    """
    steps = []
    # 1) inserir passos de otimização, se houver
    if optimization_steps:
        steps.extend(optimization_steps)

    # 2) percorrer a árvore otimizada em pós-ordem
    def _walk(node):
        if isinstance(node, Relation):
            steps.append(f"Acesso à tabela base: {node.name}")
        elif isinstance(node, Selection):
            _walk(node.child)
            steps.append(f"Filtro: {node.condition}")
        elif isinstance(node, Join):
            _walk(node.left)
            _walk(node.right)
            steps.append(f"Junção: {node.condition}")
        elif isinstance(node, Projection):
            _walk(node.child)
            attrs = ", ".join(node.attributes)
            steps.append(f"Projeção: {attrs}")
        else:
            # nó desconhecido, ignora
            pass

    _walk(optimized_tree)
    return steps
