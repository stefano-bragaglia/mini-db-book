"""Store the rows of one table in memory, together with its indexes.

A table does no validation: see :mod:`minidb.changes` for that. It offers
the two write primitives, :meth:`Table.put` and :meth:`Table.remove`, and
reads.
"""

import threading
from types import MappingProxyType
from typing import TYPE_CHECKING

from minidb.btree import BTreeIndex
from minidb.errors import SchemaError
from minidb.errors import UniqueError
from minidb.index import HashIndex
from minidb.index import OrderedIndex
from minidb.index import SortedIndex

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Iterator
    from collections.abc import Mapping

    from minidb.index import Index
    from minidb.index import IndexFactory
    from minidb.schema import TableSchema
    from minidb.values import Row
    from minidb.values import Value

type Predicate = Callable[[Mapping[str, Value | None]], object]
type Where = Predicate | Mapping[str, object] | None

INDEX_KINDS: dict[str, IndexFactory] = {"hash": HashIndex, "sorted": SortedIndex}

INDEX_KINDS["btree"] = BTreeIndex


class Table:
    """Hold the rows of one table, keyed by rowid, and keep its indexes in step.

    >>> from minidb.schema import Column, TableSchema
    >>> from minidb.types import Integer
    >>> t = Table(TableSchema("t", (Column("id", Integer()),), primary_key=("id",)))
    >>> t.put(t.new_rowid(), {"id": 5})
    >>> t.lookup({"id": 5})
    {1}

    :param schema: the table's declaration.
    """

    def __init__(self, schema: TableSchema) -> None:
        self.schema = schema
        self.name = schema.name
        self.columns = schema.column_names
        self.rows: dict[int, Row] = {}
        self.indexes: dict[str, Index] = {}
        self.stats: dict[str, int] = {}  # column -> number of distinct values
        self.version = 0
        self.row_versions: dict[int, int] = {}
        self._next_rowid = 1
        self._rowid_latch = threading.Lock()
        if schema.primary_key:
            self.create_index("pk", schema.primary_key, unique=True)
        for cols in schema.unique:
            self.create_index("unique_" + "_".join(cols), cols, unique=True)

    def __len__(self) -> int:
        return len(self.rows)

    # -- indexes ------------------------------------------------------------------

    def _fill(self, index: Index) -> None:
        """Add every existing row to a new index, refusing duplicates if it is unique."""
        for rowid, row in self.rows.items():
            key = index.key_of(row)
            if index.unique and key is not None and index.lookup(key):
                raise UniqueError(f"{self.name}: cannot create unique index {index.name!r}: duplicate key {key}")
            index.add(rowid, row)

    def committed(self) -> Table:
        """Return the table itself: a table is its own committed state.

        :return: ``self``.
        """
        return self

    def create_index(self, name: str, columns: Iterable[str], *, unique: bool = False, kind: str = "hash") -> Index:
        """Create an index over the existing rows, and maintain it from now on.

        :param name: the index's name.
        :param columns: the indexed columns, in key order.
        :param unique: whether to refuse duplicate keys; ``False`` by default.
        :param kind: ``"hash"`` (the default) or ``"sorted"``; see :data:`INDEX_KINDS`.
        :return: the new index.
        :raises SchemaError: if the name is taken, a column is unknown, or
            the kind is unknown.
        :raises UniqueError: if ``unique`` and existing rows share a key.
        """
        if name in self.indexes:
            raise SchemaError(f"{self.name}: index {name!r} already exists")
        if kind not in INDEX_KINDS:
            raise SchemaError(f"unknown index kind {kind!r}")
        columns = tuple(columns)
        for c in columns:
            self.schema.column(c)
        index = INDEX_KINDS[kind](name, columns, unique=unique)
        self._fill(index)
        self.indexes[name] = index
        return index

    def index_on(self, columns: Iterable[str]) -> Index | None:
        """Return an index on exactly these columns, in any order, or ``None``.

        :param columns: the columns the index must cover.
        :return: such an index, or ``None``.
        """
        wanted = set(columns)
        return next((i for i in self.indexes.values() if set(i.columns) == wanted), None)

    def range(
        self,
        column: str,
        lo: Value | None = None,
        hi: Value | None = None,
        *,
        lo_inclusive: bool = True,
        hi_inclusive: bool = True,
    ) -> list[int]:
        """Return the rowids with ``lo <= column <= hi``, through an ordered index.

        :param column: the column.
        :param lo: the lower bound; ``None`` (the default) for none.
        :param hi: the upper bound; ``None`` (the default) for none.
        :param lo_inclusive: whether ``lo`` itself matches; ``True`` by default.
        :param hi_inclusive: whether ``hi`` itself matches; ``True`` by default.
        :return: the matching rowids, in key order.
        :raises SchemaError: if no ordered index covers exactly ``column``.
        """
        index = next((i for i in self.indexes.values() if i.columns == (column,) and isinstance(i, OrderedIndex)), None)
        if index is None:
            raise SchemaError(f"{self.name}: no ordered index on {column!r}")
        return index.range(
            None if lo is None else (lo,),
            None if hi is None else (hi,),
            lo_inclusive=lo_inclusive,
            hi_inclusive=hi_inclusive,
        )

    def unique_keys(self) -> list[tuple[str, ...]]:
        """Return the column tuples of every unique index.

        :return: one tuple of column names per unique index.
        """
        return [i.columns for i in self.indexes.values() if i.unique]

    # -- primitives: no validation ---------------------------------------------------

    def new_rowid(self) -> int:
        """Hand out the next rowid; rowids are never reused.

        Planning happens outside the exclusive lock, so the counter has a
        small latch of its own.

        :return: a rowid no row has ever had.
        """
        with self._rowid_latch:
            rowid = self._next_rowid
            self._next_rowid += 1
            return rowid

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

    # -- reads -------------------------------------------------------------------------

    @property
    def next_rowid(self) -> int:
        """Return the rowid the next insert will get."""
        return self._next_rowid

    def _match_equal(self, equal: Mapping[str, object]) -> list[int]:
        """Find rows by equalities, through the index covering most of the columns."""
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

    def get(self, rowid: int) -> Row | None:
        """Return a copy of the row with ``rowid``, or ``None`` if there is none.

        :param rowid: the row to fetch.
        :return: a copy of the row, or ``None``.
        """
        row = self.rows.get(rowid)
        return dict(row) if row is not None else None

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

    def reserve_rowid(self, rowid: int) -> None:
        """Make sure the counter never hands out ``rowid``, or anything below it.

        :param rowid: a rowid that is in use.
        """
        with self._rowid_latch:
            self._next_rowid = max(self._next_rowid, rowid + 1)

    def row(self, rowid: int) -> Row:
        """Return the stored row itself; callers must never mutate it.

        :param rowid: the row to fetch.
        :return: the stored row.
        :raises KeyError: if there is no such row.
        """
        return self.rows[rowid]

    def scan(self) -> Iterator[tuple[int, Row]]:
        """Yield every ``(rowid, row)`` pair, each row a fresh copy.

        :return: an iterator over the table, in insertion order.
        """
        for rowid, row in self.rows.items():
            yield rowid, dict(row)

    def select(self, where: Where = None) -> list[Row]:
        """Return copies of the rows matching ``where``; see :meth:`match`.

        :param where: which rows to return; ``None`` (the default) for all.
        :return: the matching rows.
        """
        return [dict(self.rows[rid]) for rid in self.match(where)]
