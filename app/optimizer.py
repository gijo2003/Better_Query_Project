# optimizer.py
import re
from copy import deepcopy
from relational_algebra import (
    ast_to_relational_algebra,
    Relation,
    Selection,
    Projection,
    Join,
    Condition
)


def build_ra_with_early_selection(parsed_sql):
    """
    Constrói a árvore de RA aplicando filtros de tabela única antes dos JOINs,
    depois filtros multi-tabela e projeção final.
    """
    # 1) Criar relações base
    base_rel = {tbl.lower(): Relation(tbl) for tbl in parsed_sql.get('from', [])}

    # 2) Seleções de tabela única
    for cond_str in parsed_sql.get('where', []):
        cond = Condition(cond_str)
        tables = {col.split('.')[0].lower() for col in cond.columns}
        if len(tables) == 1:
            tbl = tables.pop()
            if tbl in base_rel:
                base_rel[tbl] = Selection(cond, base_rel[tbl])

    # 3) Executar JOINs em ordem
    root = None
    for tbl in parsed_sql.get('from', []):
        key = tbl.lower()
        if root is None:
            root = base_rel[key]
        else:
            # encontrar join correspondente
            join_info = next(j for j in parsed_sql.get('joins', []) if j['table'].lower() == key)
            join_cond = Condition(join_info['condition'])
            root = Join(root, base_rel[key], join_cond)

    # 4) Seleções multi-tabela
    for cond_str in parsed_sql.get('where', []):
        cond = Condition(cond_str)
        tables = {col.split('.')[0].lower() for col in cond.columns}
        if len(tables) > 1:
            root = Selection(cond, root)

    # 5) Projeção final
    return Projection(parsed_sql.get('select', []), root)


def push_projection_tree(expr):
    """
    Empurra a projeção final para baixo da árvore de joins e seleções.
    """
    if not isinstance(expr, Projection):
        return expr
    proj_attrs = set(expr.attributes)

    def push(node, required):
        # Base: relação
        if isinstance(node, Relation):
            return Projection(list(required), node)
        # Seleção: mantém condição e empurra abaixo
        if isinstance(node, Selection):
            inner = push(node.child, required)
            return Selection(node.condition, inner)
        # Join: distribui atributos e chaves de junção
        if isinstance(node, Join):
            cond = node.condition
            # determina requisitos por lado
            left_req = set()
            right_req = set()
            for attr in required:
                tbl = attr.split('.')[0].lower()
                if tbl in _rel_names(node.left): left_req.add(attr)
                if tbl in _rel_names(node.right): right_req.add(attr)
            # adiciona colunas de join
            for col in cond.columns:
                tbl = col.split('.')[0].lower()
                if tbl in _rel_names(node.left): left_req.add(col)
                if tbl in _rel_names(node.right): right_req.add(col)
            left = push(node.left, left_req)
            right = push(node.right, right_req)
            return Join(left, right, cond)
        # Qualquer outro: retorna original
        return node

    new_root = push(expr.child, proj_attrs)
    return Projection(expr.attributes, new_root)


def optimize_query(parsed_sql):
    """
    1) Early selection push-down ao construir RA
    2) Push-down de projeção

    Retorna (árvore_otimizada, passos).
    """
    # Árvore otimizada com seleção antecipada
    ra = build_ra_with_early_selection(parsed_sql)
    steps = ["Early single-table selection push-down"]
    # Empurra projeção de forma única e segura
    optimized = push_projection_tree(ra)
    steps.append("Projection push-down")
    return optimized, steps


def _rel_names(node):
    """Retorna o conjunto de nomes de todas as relações no subtree."""
    if isinstance(node, Relation):
        return {node.name.lower()}
    if hasattr(node, 'child'):
        return _rel_names(node.child)
    if hasattr(node, 'left') and hasattr(node, 'right'):
        return _rel_names(node.left) | _rel_names(node.right)
    return set()
