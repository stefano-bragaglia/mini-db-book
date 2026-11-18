from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Mapping
from types import MappingProxyType

from minidb.errors import SchemaError

type Row = dict[str, object]
type Predicate = Callable[[Mapping[str, object]], bool]


class Table:
    """Rows stored by a hidden, never-reused integer rowid."""

    def __init__(self, name: str, columns: list[str]):
        if len(set(columns)) != len(columns):
            raise SchemaError(f"duplicate column names in {name!r}")
        self._name: str = name
        self._columns: tuple[str] = tuple(columns)
        self._rows: dict[str, dict] = {}
        self._next_row_id: int = 1

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def name(self) -> str:
        return self._name

    @property
    def columns(self) -> Iterator[str]:
        return self._columns

    # -- helpers --------------------------------------------------------
    def _check_columns(self, values: Row) -> None:
        """Check that the values do not contain duplicate columns.

        :param values: the values to check
        :raises SchemaError: if the values have duplicate columns
        """
        unknown = set(values) - set(self.columns)
        if unknown:
            raise SchemaError(
                f"{self.name}: unknown column(s) {', '.join(sorted(unknown))}")

    # -- create ---------------------------------------------------------
    def insert(self, values: Row) -> int:
        """Insert a new row into the table.

        The method checks first that the values don't have duplicate columns, then sets to None
        the value of any missing column, and adds the normalized row to the dictionary using the
        next unique identifier, eventually updating it.

        :param values: the values to populate the row to be inserted
        :return: the incremental unique identifier used for the new row
        """
        self._check_columns(values)
        row = {c: values.get(c) for c in self.columns}  # missing --> None
        row_id = self._next_row_id
        self._next_row_id += 1
        self._rows[row_id] = row
        return row_id

    # -- read -----------------------------------------------------------
    def get(self, row_id: int) -> Row | None:
        """Return the row with the given row id, if any.

        :param row_id: the row id to look up
        :return: the row with the given row id or None if no such row exists
        """
        row = self._rows.get(row_id)
        if row is not None:
            return dict(row)
        return None

    def scan(self) -> Iterator[dict]:
        """Return an iterator over the ids and the rows in the table.

        :return: an iterator over the ids and the rows in the table
        """
        for row_id, row in self._rows.items():
            yield row_id, dict(row)

    def match(self, where: Predicate | None = None) -> list[int]:
        """Return a list of row ids that match the given predicate.

        If no predicate is given, all rows are matched.

        :param where: the optional predicate to match against
        :return: a list of row ids that match the given predicate
        """
        if where is None:
            return list(self._rows.keys())
        return [row_id for row_id, row in self._rows.items() if where(MappingProxyType(row))]

    def select(self, where: Predicate | None = None) -> list[Row]:
        """Return a list of rows that match the given predicate.

        If no predicate is given, all rows are selected.

        :param where: the optional predicate to match against
        :return: a list of rows that match the given predicate
        """
        return [dict(self._rows[row_id]) for row_id in self.match(where)]

    # -- update ---------------------------------------------------------
    def update(self, changes: Row, where: Predicate | None = None) -> int:
        """Update the rows matching the given predicate with the given changes.

        :param changes: the changes to apply
        :param where: the optional predicate to match against
        :return: the number of rows that were updated
        """
        self._check_columns(changes)
        targets = self.match(where)  # 1. decide
        for row_id in targets:  # 2. modify
            self._rows[row_id] = self._rows[row_id] | changes
        return len(targets)

    # -- delete ---------------------------------------------------------
    def delete(self, where: Predicate | None = None) -> int:
        """Delete the rows matching the given predicate.

        :param where: the optional predicate to match against
        :return: the number of rows that were deleted
        """
        targets = self.match(where)
        for row_id in targets:
            self._rows.pop(row_id)
        return len(targets)
