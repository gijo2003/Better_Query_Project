# optimizer.py
from copy import deepcopy
from relational_algebra import (
    ast_to_relational_algebra,
    Relation,
    Selection,
    Projection,
    Join
)

def optimize_query(parsed_sql):
    """
    Converte parsed_sql em árvore de RA e aplica, em sequência:
      1) push-down de seleção
      2) push-down de projeção

    Retorna (árvore_otimizada, lista_de_passos).
    """
    original = ast_to_relational_algebra(parsed_sql)
    current  = deepcopy(original)
    steps    = []

    # 1) Push-down de seleção (atravessa π e alcança ⋈ em uma passada)
    new = _push_selection_down(current)
    if new is not current:
        steps.append("Push-down de seleção")
        current = new

    # 2) Push-down de projeção (alcança ⋈ em uma passada)
    new = _push_projection_down(current)
    if new is not current:
        steps.append("Push-down de projeção")
        current = new

    return current, steps


def _push_selection_down(expr):
    # Seleção sobre Projeção?
    if isinstance(expr, Selection) and isinstance(expr.child, Projection):
        sel, pr = expr, expr.child
        return Projection(pr.attributes, Selection(sel.condition, pr.child))

    # Seleção sobre Join?
    if isinstance(expr, Selection) and isinstance(expr.child, Join):
        sel, jn = expr, expr.child
        tables   = {c.split('.')[0].lower() for c in sel.condition.columns}
        left_nm  = (_rel_name(jn.left)  or "").lower()
        right_nm = (_rel_name(jn.right) or "").lower()
        if tables == {left_nm}:
            return Join(Selection(sel.condition, jn.left), jn.right, jn.condition)
        if tables == {right_nm}:
            return Join(jn.left, Selection(sel.condition, jn.right), jn.condition)

    # recursão simples (uma camada)
    for attr in ('child','left','right'):
        if hasattr(expr, attr):
            sub = getattr(expr, attr)
            new = _push_selection_down(sub)
            if new is not sub:
                setattr(expr, attr, new)
                return expr

    return expr


def _push_projection_down(expr):
    # Projeção sobre Join?
    if isinstance(expr, Projection) and isinstance(expr.child, Join):
        pr, jn = expr, expr.child
        left_nm  = _rel_name(jn.left)
        right_nm = _rel_name(jn.right)

        left_attrs  = [a for a in pr.attributes if a.split('.')[0] == left_nm]
        right_attrs = [a for a in pr.attributes if a.split('.')[0] == right_nm]

        for tbl, col in (c.split('.') for c in jn.condition.columns):
            full = f"{tbl}.{col}"
            if tbl == left_nm  and full not in left_attrs:
                left_attrs.append(full)
            if tbl == right_nm and full not in right_attrs:
                right_attrs.append(full)

        new_left  = Projection(left_attrs,  jn.left)
        new_right = Projection(right_attrs, jn.right)
        new_join  = Join(new_left, new_right, jn.condition)
        return Projection(pr.attributes, new_join)

    # recursão simples (uma camada)
    for attr in ('child','left','right'):
        if hasattr(expr, attr):
            sub = getattr(expr, attr)
            new = _push_projection_down(sub)
            if new is not sub:
                setattr(expr, attr, new)
                return expr

    return expr


def _rel_name(node):
    # Desce até achar um Relation e ler o nome
    from relational_algebra import Relation
    if isinstance(node, Relation):
        return node.name
    if hasattr(node, 'child'):
        return _rel_name(node.child)
    if hasattr(node, 'left'):
        return _rel_name(node.left)
    return ""
