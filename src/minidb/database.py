"""The public entry point: a collection of tables with CRUD operations."""
from minidb.errors import SchemaError
from minidb.schema import Check
from minidb.schema import Column
from minidb.schema import TableSchema
from minidb.table import Predicate
from minidb.table import Row
from minidb.table import Table


class Database:

    def __init__(self) -> None:
        self._tables: dict[str, Table] = {}

    # -- schema -----------------------------------------------------------
    def create_table(self, name: str, columns: list[Column],
                     checks: list[Check] = ()) -> Table:
        """Create a table with the given name and columns.

        :param name: the name of the table to create
        :param columns: the columns of the table to create
        :param checks: the check to perform
        :return: the table with the given name and columns
        """
        if name in self._tables:
                raise SchemaError(f"table {name!r} already exists")
        schema = TableSchema(name, tuple(columns), tuple(checks))
        table = self._tables[name] = Table(schema)
        return table

    def drop_table(self, name: str) -> None:
        """Drop a table with the given name.

        :param name: the name of the table to drop
        """
        self.table(name)  # raises if missing
        self._tables.pop(name)

    def table(self, name: str) -> Table:
        try:
            return self._tables[name]
        except KeyError:
            raise SchemaError(f"no such table: {name!r}") from None

    # -- CRUD -------------------------------------------------------------
    def insert(self, table: str, values: Row) -> int:
        """Insert a row into a given table.

        :param table: the name of the table to insert into
        :param values: the row values to insert
        :return: the inserted row id
        """
        return self.table(table).insert(values)

    def get(self, table: str, row_id: int) -> Row | None:
        """Return the row with given row id from the given table, if any.

        :param table: the name of the table to look up
        :param row_id: the row id to look up
        :return: the row with the given row id, or None
        """
        return self.table(table).get(row_id)

    def select(self, table: str, where: Predicate | None = None) -> list[Row]:
        """Select the rows from a table with the given name matching the given predicate.

        :param table: the name of the table to select from
        :param where: the optional predicate to match the rows to select
        :return: the rows from the table with the given name matching the given predicate
        """
        return self.table(table).select(where)

    def update(self, table: str, changes: Row, where: Predicate | None = None) -> int:
        """Update the rows from the table with the given name matching the given predicate with the given changes.

        :param table: the name of the table to update
        :param changes: the new row to update
        :param where: the optional predicate to match the rows to update
        :return: the number of rows that were updated
        """
        return self.table(table).update(changes, where)

    def delete(self, table: str, where: Predicate | None = None) -> int:
        """Delete the rows from the table with the given name matching the given predicate.

        :param table: the name of the table to delete
        :param where: the optional predicate to match the rows to delete
        :return: the number of rows that were deleted
        """
        return self.table(table).delete(where)
