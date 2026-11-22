"""Group writes into all-or-nothing transactions: the Unit of Work.

Version 3: optimistic concurrency control. A read-write unit of work holds
no lock while it runs. It records what it read (its *read set*), and at
commit, under the exclusive lock, checks that all of it is still true.
"""

from contextlib import nullcontext
from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Self

from minidb import changes as ch
from minidb.errors import ConflictError
from minidb.errors import DatabaseError
from minidb.query import Query
from minidb.values import ordered

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from contextlib import AbstractContextManager
    from types import TracebackType

    from minidb.changes import Change
    from minidb.database import Database
    from minidb.schema import ForeignKey
    from minidb.table import Table
    from minidb.table import Where
    from minidb.values import Row
    from minidb.values import Value

type ReadKey = tuple[str, tuple[tuple[str, Value | None], ...]]  # ("lookup" | "match", frozen key)
type RangeRead = tuple[str, Value | None, Value | None, bool, bool]  # column, lo, hi, inclusive?


def _in_range(value: Value | None, bounds: RangeRead) -> bool:
    """Tell whether ``value`` lies within ``bounds``; NULL never does."""
    _, lo, hi, lo_inclusive, hi_inclusive = bounds
    if value is None:
        return False
    v = ordered(value)
    if lo is not None and (v < ordered(lo) or (value == lo and not lo_inclusive)):
        return False
    return not (hi is not None and (v > ordered(hi) or (value == hi and not hi_inclusive)))


class TransactionError(DatabaseError):
    """Signal that a unit of work was used in the wrong state, e.g. after commit."""


class TableView:
    """Show a table as one unit of work sees it, recording every read of committed data.

    Each read of the committed table happens under a short shared latch,
    and is remembered in the view's read set, so that commit can check it
    is still true.

    :param uow: the unit of work this view belongs to.
    :param table: the committed table.
    """

    def __init__(self, uow: UnitOfWork, table: Table) -> None:
        self.uow, self.base = uow, table
        self.name, self.schema, self.columns = table.name, table.schema, table.columns
        self.overlay: dict[int, Row | None] = {}  # rowid -> row, None = deleted
        # -- the read set -------------------------------------------------------------
        self.scanned_version: int | None = None  # table version at the first scan
        self.row_reads: dict[int, int | None] = {}  # rowid -> row version read
        self.key_reads: dict[ReadKey, frozenset[int]] = {}  # equality read -> rowids seen
        self.range_reads: dict[RangeRead, frozenset[int]] = {}  # range read -> rowids seen

    # -- reads of committed data, latched and recorded ----------------------------------
    def _base_row(self, rowid: int) -> Row | None:
        with self.uow.latch():
            row = self.base.rows.get(rowid)
            self.row_reads.setdefault(rowid, self.base.row_versions.get(rowid))
        return row

    def _base_items(self) -> list[tuple[int, Row]]:
        with self.uow.latch():
            items = list(self.base.rows.items())
            if self.scanned_version is None:
                self.scanned_version = self.base.version
        return items

    def _base_equal(self, kind: str, key: Mapping[str, Value | None]) -> set[int]:
        with self.uow.latch():
            found = self.base.lookup(key) if kind == "lookup" else set(self.base.match(key))
        self.key_reads.setdefault((kind, _freeze(key)), frozenset(found))
        return found

    # -- the interface used by planners and queries ------------------------------------
    def row(self, rowid: int) -> Row:
        """Return the row as this transaction sees it.

        :param rowid: the row to fetch.
        :return: the row; callers must never mutate it.
        :raises KeyError: if the row doesn't exist here.
        """
        row = self.overlay[rowid] if rowid in self.overlay else self._base_row(rowid)
        if row is None:
            raise KeyError(rowid)
        return row

    def get(self, rowid: int) -> Row | None:
        """Return a copy of the row, or ``None`` if it doesn't exist here.

        :param rowid: the row to fetch.
        :return: a copy of the row, or ``None``.
        """
        try:
            return dict(self.row(rowid))
        except KeyError:
            return None

    def scan(self) -> Iterator[tuple[int, Row]]:
        """Yield every ``(rowid, row)`` pair this transaction sees, rows copied.

        The committed rows are copied under the latch, and iterated without
        it: a lock must never be held across a ``yield``.

        :return: committed rows (as changed here), then rows inserted here.
        """
        items = self._base_items()
        seen: set[int] = set()
        for rowid, row in items:
            seen.add(rowid)
            current = self.overlay.get(rowid, row)
            if current is not None:
                yield rowid, dict(current)
        for rowid, row in list(self.overlay.items()):  # rows inserted here
            if row is not None and rowid not in seen:
                yield rowid, dict(row)

    def match(self, where: Where = None) -> list[int]:
        """Return the rowids matching ``where``; see :meth:`Table.match`.

        :param where: a predicate, a dict of equalities, or ``None`` for all.
        :return: the matching rowids.
        """
        if where is None or callable(where):
            return [rid for rid, row in self.scan() if where is None or where(MappingProxyType(row))]
        wanted = {c: self.schema.column(c).prepare(v) for c, v in where.items()}
        found = [rid for rid in self._base_equal("match", wanted) if rid not in self.overlay]
        found += [rid for rid, row in self.overlay.items() if row is not None and _equal(row, wanted)]
        return found

    def lookup(self, key: Mapping[str, Value | None]) -> set[int]:
        """Return the rowids whose columns equal ``key``, as the index would.

        :param key: ``{column: value}``.
        :return: the matching rowids.
        :raises SchemaError: if no index covers exactly these columns.
        """
        found = {rid for rid in self._base_equal("lookup", key) if rid not in self.overlay}
        found |= {rid for rid, row in self.overlay.items() if row is not None and _equal(row, key)}
        return found

    def select(self, where: Where = None) -> list[Row]:
        """Return copies of the rows matching ``where``.

        :param where: a predicate, a dict of equalities, or ``None`` for all.
        :return: the matching rows.
        """
        return [dict(self.row(rid)) for rid in self.match(where)]

    def unique_keys(self) -> list[tuple[str, ...]]:
        """Return the column tuples of every unique index of the table.

        :return: one tuple of column names per unique index.
        """
        return self.base.unique_keys()

    def new_rowid(self) -> int:
        """Hand out a new rowid from the table's counter.

        :return: a rowid nobody has ever had.
        """
        return self.base.new_rowid()

    def __len__(self) -> int:
        return sum(1 for _ in self.scan())

    # -- validation; the caller holds the exclusive lock ----------------------------------
    def conflicts(self) -> str | None:
        """Describe the first recorded read that is no longer true.

        :return: a description of the conflict, or ``None`` if every read
            still holds.
        """
        return self._scan_conflict() or self._row_conflict() or self._key_conflict() or self._range_conflict()

    def _range_conflict(self) -> str | None:
        for (column, lo, hi, lo_inclusive, hi_inclusive), seen in self.range_reads.items():
            now = self.base.range(column, lo, hi, lo_inclusive=lo_inclusive, hi_inclusive=hi_inclusive)
            if frozenset(now) != seen:
                return f"{self.name} rows with {column} in range changed"
        return None

    def _scan_conflict(self) -> str | None:
        if self.scanned_version is not None and self.base.version != self.scanned_version:
            return f"{self.name} changed since it was scanned"
        return None

    def _row_conflict(self) -> str | None:
        for rowid, version in self.row_reads.items():
            if self.base.row_versions.get(rowid) != version:
                return f"{self.name} row {rowid} changed since it was read"
        return None

    def _key_conflict(self) -> str | None:
        for (kind, key), seen in self.key_reads.items():
            now = self.base.lookup(dict(key)) if kind == "lookup" else set(self.base.match(dict(key)))
            if frozenset(now) != seen:
                return f"{self.name} rows matching {dict(key)} changed"
        return None

    def range(
        self,
        column: str,
        lo: Value | None = None,
        hi: Value | None = None,
        *,
        lo_inclusive: bool = True,
        hi_inclusive: bool = True,
    ) -> list[int]:
        """Return the rowids with ``lo <= column <= hi``, as this transaction sees them.

        The committed part of the answer is recorded in the read set.

        :param column: the column.
        :param lo: the lower bound; ``None`` (the default) for none.
        :param hi: the upper bound; ``None`` (the default) for none.
        :param lo_inclusive: whether ``lo`` itself matches; ``True`` by default.
        :param hi_inclusive: whether ``hi`` itself matches; ``True`` by default.
        :return: the matching rowids: committed ones in key order, then this
            transaction's.
        :raises SchemaError: if no ordered index covers exactly ``column``.
        """
        bounds: RangeRead = (column, lo, hi, lo_inclusive, hi_inclusive)
        with self.uow.latch():
            found = self.base.range(column, lo, hi, lo_inclusive=lo_inclusive, hi_inclusive=hi_inclusive)
        self.range_reads.setdefault(bounds, frozenset(found))
        found = [rid for rid in found if rid not in self.overlay]
        found += [rid for rid, row in self.overlay.items() if row is not None and _in_range(row[column], bounds)]
        return found

    def committed(self) -> Table:
        """Return the committed table behind this view, for statistics and indexes.

        :return: the table.
        """
        return self.base


def _equal(row: Mapping[str, Value | None], key: Mapping[str, Value | None]) -> bool:
    """Compare like SQL on every column of ``key``: NULL never equals anything."""
    return all(v is not None and row[c] == v for c, v in key.items())


def _freeze(key: Mapping[str, Value | None]) -> tuple[tuple[str, Value | None], ...]:
    return tuple(sorted(key.items(), key=lambda kv: kv[0]))


class Record(dict[str, "Value | None"]):
    """Hold a row loaded through a unit of work; mutate it, and commit saves it.

    :param table: the table the row is in.
    :param rowid: the row's rowid.
    :param row: its current values.
    """

    def __init__(self, table: str, rowid: int, row: Row) -> None:
        super().__init__(row)
        self.table, self.rowid = table, rowid

    def __repr__(self) -> str:
        return f"Record({self.table}#{self.rowid}, {dict.__repr__(self)})"


_MISSING = object()


class UnitOfWork:
    """Plan writes into a private workspace; validate and apply them at commit.

    There are three modes. By default the unit of work is *optimistic*: it
    holds no lock while running, and validates its read set at commit. With
    ``readonly=True`` it holds the lock in shared mode for its whole life,
    and may not write. With ``exclusive=True`` it holds the lock alone for
    its whole life, so it never conflicts.

    :param db: the database to write to.
    :param deferred: whether to check uniqueness and references only at
        commit; ``False`` by default.
    :param readonly: whether the transaction only reads; ``False`` by default.
    :param exclusive: whether to hold the lock throughout; ``False`` by default.
    :raises ValueError: if both ``readonly`` and ``exclusive`` are set.
    """

    def __init__(
        self, db: Database, *, deferred: bool = False, readonly: bool = False, exclusive: bool = False
    ) -> None:
        if readonly and exclusive:
            raise ValueError("a unit of work cannot be both readonly and exclusive")
        self.db = db
        self.deferred = deferred
        self.readonly = readonly
        self.exclusive = exclusive
        self.state = "active"
        self._views: dict[str, TableView] = {}
        self._changes: list[Change] = []
        self._identity: dict[tuple[str, int], Record] = {}
        self._snapshots: dict[tuple[str, int], Row] = {}
        self._committing = False
        db.begin(self)

    def latch(self) -> AbstractContextManager[None]:
        """Return the short lock to hold around each read of committed data.

        It does nothing when the unit of work already holds the lock: being
        read-only or exclusive, or in the middle of committing.

        :return: a context manager.
        """
        if self.readonly or self.exclusive or self._committing:
            return nullcontext()
        return self.db.shared_lock()

    def reading(self) -> nullcontext[Self]:
        """Return a context manager for queries, which does nothing: views latch each read.

        :return: a context manager that yields the unit of work.
        """
        return nullcontext(self)

    # -- the planner "state" interface ---------------------------------------------------
    @property
    def foreign_keys(self) -> Sequence[ForeignKey]:
        """Return the database's foreign keys."""
        return self.db.foreign_keys

    def table(self, name: str) -> TableView:
        """Return this transaction's view of the table called ``name``.

        :param name: the table's name.
        :return: the view, created on first use.
        :raises SchemaError: if there is no such table.
        """
        view = self._views.get(name)
        if view is None:
            view = self._views[name] = TableView(self, self.db.table(name))
        return view

    # -- writes: plan now, against the workspace -------------------------------------------
    def insert(self, table: str, values: Mapping[str, object]) -> int:
        """Insert a row into the workspace.

        :param table: the table's name.
        :param values: the new row's values, by column name.
        :return: the new rowid.
        :raises ConstraintError: if the row breaks a constraint.
        :raises TransactionError: if the unit of work is no longer active,
            or is read-only.
        """
        self._require_active(writing=True)
        self.flush()
        changes = ch.plan_insert(self, table, values, check=not self.deferred)
        self._record(changes)
        return changes[0].rowid

    def update(self, table: str, changes: Mapping[str, object], where: Where = None) -> int:
        """Update rows in the workspace.

        :param table: the table's name.
        :param changes: the new values, by column name.
        :param where: which rows change; ``None`` (the default) for all.
        :return: the number of rows changed.
        :raises ConstraintError: if a new row breaks a constraint.
        :raises TransactionError: if the unit of work is no longer active,
            or is read-only.
        """
        self._require_active(writing=True)
        self.flush()
        planned = ch.plan_update(self, table, changes, where, check=not self.deferred)
        self._record(planned)
        return len(planned)

    def delete(self, table: str, where: Where = None) -> int:
        """Delete rows, and their cascades, from the workspace.

        :param table: the table's name.
        :param where: which rows go; ``None`` (the default) for all.
        :return: the number of rows deleted from ``table`` itself.
        :raises ForeignKeyError: if a ``restrict`` reference forbids it.
        :raises TransactionError: if the unit of work is no longer active,
            or is read-only.
        """
        self._require_active(writing=True)
        self.flush()
        planned = ch.plan_delete(self, table, where, check=not self.deferred)
        self._record(planned)
        return sum(1 for c in planned if c.table == table and c.kind == "delete")

    def _record(self, changes: list[Change]) -> None:
        """Put planned changes into the overlays, and keep loaded records current."""
        for c in changes:
            self.table(c.table).overlay[c.rowid] = c.after
            self._changes.append(c)
            key = (c.table, c.rowid)
            if key in self._identity:
                self._refresh(key, c.after)

    def _refresh(self, key: tuple[str, int], after: Row | None) -> None:
        if after is None:
            del self._identity[key], self._snapshots[key]
            return
        record = self._identity[key]
        record.clear()
        record.update(after)
        self._snapshots[key] = dict(after)

    # -- reads -------------------------------------------------------------------------
    def get(self, table: str, rowid: int) -> Record | None:
        """Return the row as a tracked :class:`Record`; one object per row.

        :param table: the table's name.
        :param rowid: the row to load.
        :return: the record, or ``None`` if the row doesn't exist here.
        :raises TransactionError: if the unit of work is no longer active.
        """
        self._require_active()
        key = (table, rowid)
        if key in self._identity:
            return self._identity[key]
        row = self.table(table).get(rowid)
        if row is None:
            return None
        record = self._identity[key] = Record(table, rowid, row)
        self._snapshots[key] = dict(row)
        return record

    def find(self, table: str, where: Where = None) -> list[Record]:
        """Return the matching rows as tracked records.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all.
        :return: one record per matching row.
        """
        self.flush()
        records = [self.get(table, rid) for rid in self.table(table).match(where)]
        return [r for r in records if r is not None]

    def select(self, table: str, where: Where = None) -> list[Row]:
        """Return copies of the matching rows, as this transaction sees them.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all.
        :return: the matching rows.
        """
        self.flush()
        return self.table(table).select(where)

    def query(self, table: str, alias: str | None = None) -> Query:
        """Start a query that sees this transaction's changes.

        :param table: the first table.
        :param alias: its alias; ``None`` (the default) uses its name.
        :return: a query to extend and run.
        """
        self.flush()
        return Query(self, table, alias)

    # -- dirty checking ---------------------------------------------------------------------
    def flush(self) -> None:
        """Turn modifications of loaded records into planned updates.

        :raises ConstraintError: if a modified record breaks a constraint.
        :raises TransactionError: if a record was modified in a read-only
            unit of work.
        """
        for key, record in list(self._identity.items()):
            before = self._snapshots[key]
            if record != before:
                self._require_active(writing=True)
                diff = {c: v for c, v in record.items() if before.get(c, _MISSING) != v}
                self._record(ch.plan_update(self, key[0], diff, rowids=[key[1]], check=not self.deferred))

    # -- finishing ---------------------------------------------------------------------
    def commit(self) -> None:
        """Flush, then validate and apply, in the way this unit of work's mode requires.

        :raises ConflictError: if an optimistic unit of work read something
            that has changed since; it then stays active, for a rollback.
        :raises ConstraintError: if a deferred check fails.
        :raises TransactionError: if the unit of work is no longer active.
        """
        self._require_active()
        self.flush()
        if self.exclusive:
            self._apply()  # nobody else ran: nothing to validate
        elif not self.readonly:
            with self.db.exclusive_lock():  # the only exclusive section
                self._committing = True
                try:
                    self._validate()
                    self._apply()
                finally:
                    self._committing = False
        self.state = "committed"
        self.db.end(self)

    def _validate(self) -> None:
        for view in self._views.values():
            problem = view.conflicts()
            if problem:
                raise ConflictError(problem)

    def _apply(self) -> None:
        if self.deferred:
            ch.check_deferred(self, self._changes)
        self.db.apply(ch.net_changes(self._changes))

    def rollback(self) -> None:
        """Forget every change and release any lock held.

        :raises TransactionError: if the unit of work is no longer active.
        """
        self._require_active()
        self._views.clear()
        self._changes.clear()
        self._identity.clear()
        self.state = "rolled back"
        self.db.end(self)

    def _require_active(self, *, writing: bool = False) -> None:
        if self.state != "active":
            raise TransactionError(f"unit of work is already {self.state}")
        if writing and self.readonly:
            raise TransactionError("cannot write in a read-only unit of work")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        if self.state != "active":
            return
        if exc_type is not None:
            self.rollback()
            return
        try:
            self.commit()
        except BaseException:
            self.rollback()
            raise
