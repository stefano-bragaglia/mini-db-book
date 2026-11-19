"""Provide the public entry point: a collection of tables with CRUD operations."""

from collections.abc import Mapping
from collections.abc import Sequence
from typing import TYPE_CHECKING

from minidb.schema import as_key
from minidb.schema import TableSchema
from minidb.table import Table

if TYPE_CHECKING:
    from minidb.errors import SchemaError
    from minidb.schema import Check
    from minidb.schema import Column

    from minidb.table import Where
    from minidb.values import Row


class Database:
    """Hold tables by name, and run CRUD operations on them."""

    def __init__(self) -> None:
        self.tables: dict[str, Table] = {}

    # -- schema -----------------------------------------------------------
    def create_table(
            self,
            name: str,
            columns: Sequence[Column],
            *,
            primary_key: str | Sequence[str] = (),
            unique: Sequence[str | Sequence[str]] = (),
            checks: Sequence[Check] = (),
    ) -> Table:
        """Create an empty table and return it.

        >>> from minidb.schema import Column
        >>> from minidb.types import Integer
        >>> db = Database()
        >>> sorted(db.create_table("t", [Column("id", Integer())], primary_key="id").indexes)
        ['pk']

        :param name: the new table's name.
        :param columns: its columns, in order.
        :param primary_key: the primary-key column or columns; none by default.
        :param unique: the columns of each UNIQUE constraint; none by default.
        :param checks: its row-level CHECK constraints; none by default.
        :return: the new table.
        :raises SchemaError: if the table already exists, or the definition
            is invalid.
        """
        if name in self.tables:
            raise SchemaError(f"table {name!r} already exists")
        schema = TableSchema(name, tuple(columns),
                             tuple(checks), as_key(primary_key),
                             tuple(as_key(u) for u in unique))
        table = self.tables[name] = Table(schema)
        return table

    def create_index(self, table: str, name: str, columns: Sequence[str], *, unique: bool = False) -> None:
        """Create an index on ``table``; see :meth:`Table.create_index`.

        :param table: the table's name.
        :param name: the index's name.
        :param columns: the indexed columns, in key order.
        :param unique: whether to refuse duplicate keys; ``False`` by default.
        """
        self.table(table).create_index(name, columns, unique=unique)

    def drop_table(self, name: str) -> None:
        """Delete a table and all its rows.

        :param name: the table to delete.
        :raises SchemaError: if there is no such table.
        """
        self.table(name)  # raises if missing
        del self.tables[name]

    def table(self, name: str) -> Table:
        """Return the table called ``name``.

        :param name: the table's name.
        :return: the table.
        :raises SchemaError: if there is no such table.
        """
        try:
            return self.tables[name]
        except KeyError:
            raise SchemaError(f"no such table: {name!r}") from None

    # -- CRUD -------------------------------------------------------------
    def insert(self, table: str, values: Mapping[str, object]) -> int:
        """Insert a row into ``table``; see :meth:`Table.insert`.

        :param table: the table's name.
        :param values: the new row's values, by column name.
        :return: the rowid of the new row.
        """
        return self.table(table).insert(values)

    def get(self, table: str, rowid: int) -> Row | None:
        """Return a copy of one row; see :meth:`Table.get`.

        :param table: the table's name.
        :param rowid: the row to fetch.
        :return: the row, or ``None`` if there is no such row.
        """
        return self.table(table).get(rowid)

    def select(self, table: str, where: Where = None) -> list[Row]:
        """Return the rows of ``table`` matching ``where``; see :meth:`Table.match`.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: copies of the matching rows.
        """
        return self.table(table).select(where)

    def update(self, table: str, changes: Mapping[str, object], where: Where = None) -> int:
        """Update the rows of ``table`` matching ``where``.

        :param table: the table's name.
        :param changes: the new values, by column name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: the number of rows changed.
        """
        return self.table(table).update(changes, where)

    def delete(self, table: str, where: Where = None) -> int:
        """Delete the rows of ``table`` matching ``where``.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: the number of rows deleted.
        """
        return self.table(table).delete(where)
