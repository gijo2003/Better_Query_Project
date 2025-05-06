# relational_algebra.py
# Definição de classes para árvore de Álgebra Relacional e conversão de AST

import re

class Relation:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


class Condition:
    def __init__(self, expr: str):
        self.expr = expr
        # Extrai colunas qualificadas no formato tabela.coluna
        self.columns = re.findall(r'\b\w+\.\w+\b', expr)

    def __str__(self):
        return self.expr

    def __repr__(self):
        return self.__str__()


class Join:
    def __init__(self, left, right, condition):
        self.left = left
        self.right = right
        # condition pode ser string ou Condition
        self.condition = condition if isinstance(condition, Condition) else Condition(condition)

    def __str__(self):
        return f"({self.left} ⋈_{{{self.condition}}} {self.right})"

    def __repr__(self):
        return self.__str__()


class Selection:
    def __init__(self, condition, child):
        # condition pode ser string ou Condition
        self.condition = condition if isinstance(condition, Condition) else Condition(condition)
        self.child = child

    def __str__(self):
        return f"σ_{{{self.condition}}}({self.child})"

    def __repr__(self):
        return self.__str__()


class Projection:
    def __init__(self, attributes, child):
        # attributes: lista de strings no formato tabela.coluna
        self.attributes = attributes
        self.child = child

    def __str__(self):
        cols = ", ".join(self.attributes)
        return f"π_{{{cols}}}({self.child})"

    def __repr__(self):
        return self.__str__()


def ast_to_relational_algebra(parsed_sql: dict):
    """
    Converte o dicionário parsed_sql em uma árvore de Álgebra Relacional.

    parsed_sql deve conter as chaves:
      - 'from': lista de tabelas (strings)
      - 'joins': lista de dicts com 'table' e 'condition'
      - 'where': lista de expressões (strings)
      - 'select': lista de atributos (strings no formato tabela.coluna)
    """
    # 1) Inicia com a primeira tabela
    tables = parsed_sql.get('from', [])
    if not tables:
        raise ValueError("parsed_sql['from'] está vazio")
    root = Relation(tables[0])

    # 2) Aplica JOINs de forma associativa à esquerda
    for join in parsed_sql.get('joins', []):
        right = Relation(join['table'])
        root = Join(root, right, join['condition'])

    # 3) Empilha seleções (WHERE)
    for cond in parsed_sql.get('where', []):
        root = Selection(cond, root)

    # 4) Aplica projeção final
    attrs = parsed_sql.get('select', [])
    root = Projection(attrs, root)

    return root
