# src/minidb/table.py
"""Store the rows of one table in memory.

Rows live in a dict keyed by a hidden *rowid*: an integer from a counter that
only goes up, so a rowid is never reused, even after its row is deleted.
Every insert and update goes through the table's schema.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Mapping

    from minidb.schema import TableSchema
    from minidb.values import Row
    from minidb.values import Value

type Predicate = Callable[[Mapping[str, Value | None]], object]
type Where = Predicate | None


class Table:
    """Hold the rows of one table, keyed by a hidden, never-reused rowid.

    Rows are *values*: the table hands out copies, and replaces stored rows
    instead of mutating them, so no caller can change a row behind its back.

    >>> from minidb.schema import Column, TableSchema
    >>> from minidb.types import Integer
    >>> numbers = Table(TableSchema("numbers", (Column("n", Integer()),)))
    >>> numbers.insert({"n": "7"})
    1
    >>> numbers.get(1)
    {'n': 7}

    :param schema: the table's declaration.
    """

    def __init__(self, schema: TableSchema) -> None:
        self.schema = schema
        self.name = schema.name
        self.columns = schema.column_names
        self.rows: dict[int, Row] = {}
        self._next_rowid = 1

    def __len__(self) -> int:
        return len(self.rows)

    # -- create ---------------------------------------------------------
    def insert(self, values: Mapping[str, object]) -> int:
        """Prepare a row through the schema, store it, and return its rowid.

        :param values: the new row's values, by column name; missing
            columns are stored as ``None``.
        :return: the rowid of the new row.
        :raises SchemaError: if ``values`` names an unknown column.
        :raises DomainError: if a value doesn't belong to its column's type.
        """
        row = self.schema.prepare_row(values)
        rowid = self._next_rowid
        self._next_rowid += 1
        self.rows[rowid] = row
        return rowid

    # -- read -----------------------------------------------------------
    def get(self, rowid: int) -> Row | None:
        """Return a copy of the row with ``rowid``.

        :param rowid: the row to fetch.
        :return: a copy of the row, or ``None`` if there is no such row.
        """
        row = self.rows.get(rowid)
        return dict(row) if row is not None else None

    def scan(self) -> Iterator[tuple[int, Row]]:
        """Yield every ``(rowid, row)`` pair, each row a fresh copy.

        :return: an iterator over the table, in insertion order.
        """
        for rowid, row in self.rows.items():
            yield rowid, dict(row)

    def match(self, where: Where = None) -> list[int]:
        """Return the rowids of the rows that satisfy ``where``.

        The predicate sees each row through a read-only view.

        :param where: decides which rows match; ``None`` (the default)
            matches every row.
        :return: the matching rowids.
        """
        if where is None:
            return list(self.rows)
        return [rid for rid, row in self.rows.items() if where(MappingProxyType(row))]

    def select(self, where: Where = None) -> list[Row]:
        """Return copies of the rows that satisfy ``where``.

        :param where: decides which rows match; ``None`` (the default)
            matches every row.
        :return: the matching rows.
        """
        return [dict(self.rows[rid]) for rid in self.match(where)]

    # -- update ---------------------------------------------------------
    def update(self, changes: Mapping[str, object], where: Where = None) -> int:
        """Set the columns in ``changes`` on every row that satisfies ``where``.

        Every new row is prepared before any is stored, so a value that fails
        validation leaves the whole table unchanged.

        :param changes: the new values, by column name.
        :param where: decides which rows change; ``None`` (the default)
            changes every row.
        :return: the number of rows changed.
        :raises SchemaError: if ``changes`` names an unknown column.
        :raises DomainError: if a value doesn't belong to its column's type.
        """
        targets = self.match(where)  # 1. decide
        new_rows = {rid: self.schema.prepare_row(changes, base=self.rows[rid]) for rid in targets}  # 2. validate
        self.rows.update(new_rows)  # 3. modify
        return len(targets)

    # -- delete ---------------------------------------------------------
    def delete(self, where: Where = None) -> int:
        """Remove every row that satisfies ``where``.

        :param where: decides which rows go; ``None`` (the default) removes
            every row.
        :return: the number of rows removed.
        """
        targets = self.match(where)
        for rowid in targets:
            del self.rows[rowid]
        return len(targets)
