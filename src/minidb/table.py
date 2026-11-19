# src/minidb/table.py
"""Store the rows of one table in memory, together with its indexes.

Writes are split in two layers. The primitives :meth:`Table.put` and
:meth:`Table.remove` store and delete rows and keep every index in step, but
check nothing. The operations (:meth:`Table.insert`, :meth:`Table.update_rows`,
:meth:`Table.delete_rows`) validate everything first, then call the primitives.
"""

from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Mapping
from types import MappingProxyType
from typing import Iterable
from typing import TYPE_CHECKING

from minidb.errors import UniqueError
from minidb.index import HashIndex

if TYPE_CHECKING:
    from minidb import SchemaError
    from minidb.index import Key
    from minidb.index import Index
    from minidb.schema import TableSchema
    from minidb.values import Row
    from minidb.values import Value

type Predicate = Callable[[Mapping[str, Value | None]], object]
type Where = Predicate | Mapping[str, object] | None


class Table:
    """Hold the rows of one table, keyed by rowid, and keep its indexes in step.

    A primary key and each UNIQUE constraint of the schema get a unique hash
    index automatically.

    >>> from minidb.schema import Column, TableSchema
    >>> from minidb.types import Integer
    >>> t = Table(TableSchema("t", (Column("id", Integer()),), primary_key=("id",)))
    >>> t.insert({"id": 1})
    1
    >>> t.insert({"id": 1})
    Traceback (most recent call last):
      ...
    minidb.errors.UniqueError: t: duplicate key (id=1) violates 'pk'

    :param schema: the table's declaration.
    """

    def __init__(self, schema: TableSchema) -> None:
        self.schema = schema
        self.name = schema.name
        self.columns = schema.column_names
        self.rows: dict[int, Row] = {}
        self.indexes: dict[str, Index] = {}
        self._next_rowid = 1
        if schema.primary_key:
            self.create_index("pk", schema.primary_key, unique=True)
        for cols in schema.unique:
            self.create_index("unique_" + "_".join(cols), cols, unique=True)

    def __len__(self) -> int:
        return len(self.rows)

    # -- indexes ------------------------------------------------------------
    def create_index(self, name: str, columns: Iterable[str], *, unique: bool = False) -> Index:
        """Create an index over the existing rows, and maintain it from now on.

        :param name: the index's name.
        :param columns: the indexed columns, in key order.
        :param unique: whether to refuse duplicate keys; ``False`` by default.
        :return: the new index.
        :raises SchemaError: if the name is taken or a column is unknown.
        :raises UniqueError: if ``unique`` and existing rows share a key.
        """
        if name in self.indexes:
            from minidb import SchemaError
            raise SchemaError(f"{self.name}: index {name!r} already exists")
        columns = tuple(columns)
        for c in columns:
            self.schema.column(c)
        index = HashIndex(name, columns, unique=unique)
        for rowid, row in self.rows.items():
            key = index.key_of(row)
            if unique and key is not None and index.lookup(key):
                raise UniqueError(f"{self.name}: cannot create unique index {name!r}: duplicate key {key}")
            index.add(rowid, row)
        self.indexes[name] = index
        return index

    def index_on(self, columns: Iterable[str]) -> Index | None:
        """Return an index on exactly these columns, in any order.

        :param columns: the columns the index must cover.
        :return: such an index, or ``None`` if there is none.
        """
        wanted = set(columns)
        return next((i for i in self.indexes.values() if set(i.columns) == wanted), None)

    # -- primitives: no validation -------------------------------------------
    def put(self, rowid: int, row: Row) -> None:
        """Store ``row`` at ``rowid``, replacing any old row, and update every index.

        :param rowid: where to store the row.
        :param row: the row, already validated.
        """
        old = self.rows.get(rowid)
        for index in self.indexes.values():
            if old is not None:
                index.remove(rowid, old)
            index.add(rowid, row)
        self.rows[rowid] = row

    def remove(self, rowid: int) -> None:
        """Delete the row at ``rowid`` and its index entries.

        :param rowid: the row to delete.
        :raises KeyError: if there is no such row.
        """
        old = self.rows.pop(rowid)
        for index in self.indexes.values():
            index.remove(rowid, old)

    def new_rowid(self) -> int:
        """Hand out the next rowid; rowids are never reused.

        :return: a rowid no row has ever had.
        """
        rowid = self._next_rowid
        self._next_rowid += 1
        return rowid

    # -- checks ---------------------------------------------------------------
    def check_unique(self, batch: list[tuple[int | None, Row]]) -> None:
        """Check that applying ``batch`` would leave every unique key unique.

        Rows in the batch are compared with each other, and with every row
        *outside* the batch, so swapping two keys in one batch is allowed.

        :param batch: pairs of a rowid (``None`` for a new row) and the row
            it will hold.
        :raises UniqueError: if two rows would share a unique key.
        """
        changing = {rid for rid, _ in batch if rid is not None}
        for index in self.indexes.values():
            if index.unique:
                self._check_unique_index(index, batch, changing)

    def _check_unique_index(self, index: Index, batch: list[tuple[int | None, Row]], changing: set[int]) -> None:
        seen: set[Key] = set()
        for _, row in batch:
            key = index.key_of(row)
            if key is None:
                continue
            if key in seen or index.lookup(key) - changing:
                shown = ", ".join(f"{c}={v!r}" for c, v in zip(index.columns, key, strict=True))
                raise UniqueError(f"{self.name}: duplicate key ({shown}) violates {index.name!r}")
            seen.add(key)

    # -- read -----------------------------------------------------------------
    def get(self, rowid: int) -> Row | None:
        """Return a copy of the row with ``rowid``, or ``None`` if there is none.

        :param rowid: the row to fetch.
        :return: a copy of the row, or ``None``.
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
        """Return the rowids of the rows matching ``where``.

        :param where: ``None`` (the default) for every row; a predicate,
            which sees each row through a read-only view; or a dict of
            ``column: value`` equalities, which can use an index.
        :return: the matching rowids.
        :raises SchemaError: if a dict names an unknown column.
        :raises DomainError: if a dict value doesn't fit its column's type.
        """
        if where is None:
            return list(self.rows)
        if callable(where):
            return [rid for rid, row in self.rows.items() if where(MappingProxyType(row))]
        return self._match_equal(where)

    def _match_equal(self, equal: Mapping[str, object]) -> list[int]:
        """Find rows by equalities, through the index covering most of the columns.

        Values are prepared like stored values first, so they match however
        the user wrote them; a NULL value matches nothing.
        """
        wanted = {c: self.schema.column(c).prepare(v) for c, v in equal.items()}
        best = max(
            (i for i in self.indexes.values() if set(i.columns) <= set(wanted)),
            key=lambda i: len(i.columns),
            default=None,
        )
        if best is not None:
            candidates: Iterable[int] = best.lookup(tuple(wanted[c] for c in best.columns))
        else:
            candidates = self.rows.keys()
        return [rid for rid in candidates if all(self.rows[rid][c] == v and v is not None for c, v in wanted.items())]

    def select(self, where: Where = None) -> list[Row]:
        """Return copies of the rows matching ``where``; see :meth:`match`.

        :param where: which rows to return; ``None`` (the default) for all.
        :return: the matching rows.
        """
        return [dict(self.rows[rid]) for rid in self.match(where)]

    # -- write operations: validate everything, then apply ----------------------
    def insert(self, values: Mapping[str, object]) -> int:
        """Validate a new row, store it, and return its rowid.

        :param values: the new row's values, by column name.
        :return: the new rowid.
        :raises ConstraintError: if the row breaks a constraint.
        """
        row = self.schema.prepare_row(values)
        self.check_unique([(None, row)])
        rowid = self.new_rowid()
        self.put(rowid, row)
        return rowid

    def update_rows(self, changes: Mapping[int, Mapping[str, object]]) -> int:
        """Apply per-row changes atomically: all of them, or none.

        :param changes: ``{rowid: {column: value}}``.
        :return: the number of rows changed.
        :raises ConstraintError: if any new row breaks a constraint.
        """
        new_rows = {rid: self.schema.prepare_row(ch, base=self.rows[rid]) for rid, ch in changes.items()}
        self.check_unique(list(new_rows.items()))
        for rid, row in new_rows.items():
            self.put(rid, row)
        return len(new_rows)

    def delete_rows(self, rowids: Iterable[int]) -> int:
        """Delete the given rows.

        :param rowids: the rows to delete.
        :return: the number of rows deleted.
        :raises KeyError: if a rowid doesn't exist.
        """
        targets = list(rowids)
        for rid in targets:
            self.remove(rid)
        return len(targets)

    def update(self, changes: Mapping[str, object], where: Where = None) -> int:
        """Apply the same ``changes`` to every row matching ``where``.

        :param changes: the new values, by column name.
        :param where: which rows change; ``None`` (the default) for all.
        :return: the number of rows changed.
        :raises ConstraintError: if any new row breaks a constraint.
        """
        return self.update_rows(dict.fromkeys(self.match(where), changes))

    def delete(self, where: Where = None) -> int:
        """Delete every row matching ``where``.

        :param where: which rows go; ``None`` (the default) for all.
        :return: the number of rows deleted.
        """
        return self.delete_rows(self.match(where))

    def lookup(self, key: Mapping[str, Value | None]) -> set[int]:
        """Return the rowids whose columns equal ``key``, through an index.

        :param key: ``{column: value}``; the order of the columns doesn't matter.
        :return: the matching rowids, as a new set.
        :raises SchemaError: if no index covers exactly these columns.
        """
        index = self.index_on(key)
        if index is None:
            raise SchemaError(f"{self.name}: no index on {sorted(key)}")
        return index.lookup(tuple(key[c] for c in index.columns))
