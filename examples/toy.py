"""Implement relational algebra over lists of dicts: a toy to learn from.

The toy is not part of minidb. It exists to show, in a few lines, both the
idea of relational operators and everything a real database must add.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

type Row = dict[str, object]
type Relation = list[Row]


def select(relation: Relation, predicate: Callable[[Row], bool]) -> Relation:
    """Keep the rows of ``relation`` for which ``predicate`` is true (*selection*).

    >>> select([{"a": 1}, {"a": 2}], lambda row: row["a"] == 2)
    [{'a': 2}]

    :param relation: the input relation.
    :param predicate: decides whether a row is kept.
    :return: the kept rows, in input order.
    """
    return [row for row in relation if predicate(row)]


def project(relation: Relation, *attributes: str) -> Relation:
    """Keep only ``attributes`` of each row, dropping duplicate results (*projection*).

    Relations are sets, so two rows that become equal after projection are
    kept only once.

    >>> project([{"a": 1, "b": 1}, {"a": 1, "b": 2}], "a")
    [{'a': 1}]

    :param relation: the input relation.
    :param attributes: the names of the attributes to keep.
    :return: the projected rows, without duplicates.
    :raises KeyError: if a row lacks one of ``attributes``.
    """
    seen: set[tuple[tuple[str, object], ...]] = set()
    out: Relation = []
    for row in relation:
        projected = {a: row[a] for a in attributes}
        key = tuple(projected.items())
        if key not in seen:
            seen.add(key)
            out.append(projected)
    return out


def join(left: Relation, right: Relation, on: Callable[[Row, Row], bool]) -> Relation:
    """Combine every pair of rows from ``left`` and ``right`` that matches (*join*).

    >>> join([{"a": 1}], [{"b": 1}, {"b": 2}], lambda x, y: x["a"] == y["b"])
    [{'a': 1, 'b': 1}]

    :param left: the outer relation.
    :param right: the inner relation.
    :param on: decides whether a pair of rows matches.
    :return: the merged pairs, ordered by ``left`` and then by ``right``.
    """
    return [lrow | rrow for lrow in left for rrow in right if on(lrow, rrow)]


USERS: Relation = [
    {"id": 1, "name": "Ada", "age": 36},
    {"id": 2, "name": "Alan", "age": 41},
    {"id": 3, "name": "Grace", "age": None},
]
ORDERS: Relation = [
    {"order_id": 10, "user_id": 1, "total": 25},
    {"order_id": 11, "user_id": 2, "total": 40},
    {"order_id": 12, "user_id": 1, "total": 15},
]
