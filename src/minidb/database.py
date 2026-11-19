"""Provide the public entry point: a collection of tables with CRUD operations."""

from typing import TYPE_CHECKING

from minidb.errors import SchemaError
from minidb.schema import Check
from minidb.schema import Column
from minidb.schema import TableSchema
from minidb.table import Table

if TYPE_CHECKING:
    from collections.abc import Mapping
    from collections.abc import Sequence

    from minidb.table import Where
    from minidb.values import Row


class Database:
    """Hold tables by name, and run CRUD operations on them."""

    def __init__(self) -> None:
        self.tables: dict[str, Table] = {}

    # -- schema -----------------------------------------------------------
    def create_table(self, name: str, columns: Sequence[Column], checks: Sequence[Check] = ()) -> Table:
        """Create an empty table and return it.

        >>> from minidb.schema import Column
        >>> from minidb.types import Text
        >>> db = Database()
        >>> db.create_table("users", [Column("name", Text())]).columns
        ('name',)

        :param name: the new table's name.
        :param columns: its columns, in order.
        :param checks: its row-level CHECK constraints; none by default.
        :return: the new table.
        :raises SchemaError: if the table already exists, or two columns
            share a name.
        """
        if name in self.tables:
            raise SchemaError(f"table {name!r} already exists")
        schema = TableSchema(name, tuple(columns), tuple(checks))
        table = self.tables[name] = Table(schema)
        return table

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
        """Return the rows of ``table`` that satisfy ``where``.

        :param table: the table's name.
        :param where: decides which rows match; ``None`` matches all.
        :return: copies of the matching rows.
        """
        return self.table(table).select(where)

    def update(self, table: str, changes: Mapping[str, object], where: Where = None) -> int:
        """Update the rows of ``table`` that satisfy ``where``.

        :param table: the table's name.
        :param changes: the new values, by column name.
        :param where: decides which rows change; ``None`` changes all.
        :return: the number of rows changed.
        """
        return self.table(table).update(changes, where)

    def delete(self, table: str, where: Where = None) -> int:
        """Delete the rows of ``table`` that satisfy ``where``.

        :param table: the table's name.
        :param where: decides which rows go; ``None`` deletes all.
        :return: the number of rows deleted.
        """
        return self.table(table).delete(where)
