"""Provide the public entry point: tables, cross-table constraints and CRUD.

Every write is planned first (:mod:`minidb.changes`) and then applied by
:meth:`Database.apply`, the only method that modifies tables.
"""

import random
import threading
import time
from contextlib import contextmanager
from dataclasses import replace
from typing import TYPE_CHECKING

from minidb import changes as ch
from minidb.errors import ConflictError
from minidb.errors import DatabaseError
from minidb.errors import SchemaError
from minidb.locks import FairRWLock
from minidb.query import Query
from minidb.schema import TableSchema
from minidb.schema import as_key
from minidb.storage import decode_row
from minidb.storage import encode_row
from minidb.storage import schema_fingerprint
from minidb.table import Table
from minidb.uow import TransactionError
from minidb.uow import UnitOfWork

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from contextlib import AbstractContextManager

    from minidb.changes import Change
    from minidb.locks import RWLock
    from minidb.schema import Check
    from minidb.schema import Column
    from minidb.schema import ForeignKey
    from minidb.storage import LogRecord
    from minidb.storage import Snapshot
    from minidb.storage import Storage
    from minidb.storage import TableData
    from minidb.table import Where
    from minidb.values import Primitive
    from minidb.values import Row


class Database:
    """Hold tables and the foreign keys between them, and run CRUD on them."""

    def __init__(self, *, lock: RWLock | None = None) -> None:
        self.tables: dict[str, Table] = {}
        self.foreign_keys: list[ForeignKey] = []
        self.commit_seq = 0
        self.storage: Storage | None = None
        self._lock: RWLock = lock if lock is not None else FairRWLock()
        self._local = threading.local()

    def shared_lock(self) -> AbstractContextManager[None]:
        """Return a context manager that holds the database lock in shared mode.

        :return: the context manager.
        """
        return self._lock.read()

    def exclusive_lock(self) -> AbstractContextManager[None]:
        """Return a context manager that holds the database lock exclusively.

        :return: the context manager.
        """
        return self._lock.write()

    # -- schema --------------------------------------------------------------------
    def create_table(
        self,
        name: str,
        columns: Sequence[Column],
        *,
        primary_key: str | Sequence[str] = (),
        unique: Sequence[str | Sequence[str]] = (),
        checks: Sequence[Check] = (),
        foreign_keys: Sequence[ForeignKey] = (),
    ) -> Table:
        """Create an empty table and return it; all or nothing.

        >>> from minidb.schema import Column
        >>> from minidb.types import Integer
        >>> db = Database()
        >>> db.create_table("t", [Column("id", Integer())], primary_key="id").name
        't'

        :param name: the new table's name.
        :param columns: its columns, in order.
        :param primary_key: the primary-key column or columns; none by default.
        :param unique: the columns of each UNIQUE constraint; none by default.
        :param checks: its row-level CHECK constraints; none by default.
        :param foreign_keys: its references to other tables; none by default.
        :return: the new table.
        :raises SchemaError: if the table already exists, or the definition
            is invalid.
        """
        if name in self.tables:
            raise SchemaError(f"table {name!r} already exists")
        schema = TableSchema(name, tuple(columns), tuple(checks), as_key(primary_key), tuple(as_key(u) for u in unique))
        table = self.tables[name] = Table(schema)
        try:
            for fk in foreign_keys:
                self._add_foreign_key(replace(fk, table=name))
        except DatabaseError:
            self._forget_table(name)
            raise
        return table

    def _forget_table(self, name: str) -> None:
        del self.tables[name]
        self.foreign_keys = [f for f in self.foreign_keys if f.table != name]

    def _add_foreign_key(self, fk: ForeignKey) -> None:
        """Validate ``fk`` against both tables and the existing data, then register it."""
        child, parent = self.table(fk.table), self.table(fk.ref_table)
        if not fk.ref_columns:
            if not parent.schema.primary_key:
                raise SchemaError(f"{parent.name} has no primary key to reference")
            fk = replace(fk, ref_columns=parent.schema.primary_key)
        self._check_fk_columns(fk, child, parent)
        if child.index_on(fk.columns) is None:
            child.create_index(fk.name, fk.columns)
        ch.check_parents_exist(self, child, child.rows.values(), [fk])
        self.foreign_keys.append(fk)

    @staticmethod
    def _check_fk_columns(fk: ForeignKey, child: Table, parent: Table) -> None:
        """Check that ``fk`` pairs columns of the same types and targets a key."""
        if len(fk.columns) != len(fk.ref_columns):
            raise SchemaError(f"{fk.name}: column count mismatch")
        for c, r in zip(fk.columns, fk.ref_columns, strict=True):
            if type(child.schema.column(c).type) is not type(parent.schema.column(r).type):
                raise SchemaError(f"{fk.name}: {c} and {parent.name}.{r} differ in type")
        target = parent.index_on(fk.ref_columns)
        if target is None or not target.unique:
            raise SchemaError(f"{fk.name}: {parent.name}{fk.ref_columns} is not a key")

    def drop_table(self, name: str) -> None:
        """Delete a table that no other table references.

        :param name: the table to delete.
        :raises SchemaError: if there is no such table, or another table
            references it.
        """
        self.table(name)
        if any(fk.ref_table == name and fk.table != name for fk in self.foreign_keys):
            raise SchemaError(f"{name!r} is referenced by a foreign key")
        self._forget_table(name)

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

    def create_index(
        self, table: str, name: str, columns: Sequence[str], *, unique: bool = False, kind: str = "hash"
    ) -> None:
        """Create an index on ``table``, while no transaction commits.

        :param table: the table's name.
        :param name: the index's name.
        :param columns: the indexed columns, in key order.
        :param unique: whether to refuse duplicate keys; ``False`` by default.
        :param kind: the kind of index, ``"hash"`` by default; see
            :data:`minidb.table.INDEX_KINDS`.
        """
        with self.exclusive_lock():
            self.table(table).create_index(name, columns, unique=unique, kind=kind)

    # -- reads ---------------------------------------------------------------------
    def get(self, table: str, rowid: int) -> Row | None:
        """Return a copy of one row, or ``None``; see :meth:`Table.get`.

        :param table: the table's name.
        :param rowid: the row to fetch.
        :return: the row, or ``None``.
        """
        with self.reading():
            return self.table(table).get(rowid)

    def select(self, table: str, where: Where = None) -> list[Row]:
        """Return the rows of ``table`` matching ``where``; see :meth:`Table.match`.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: copies of the matching rows.
        """
        with self.reading():
            return self.table(table).select(where)

    def query(self, table: str, alias: str | None = None) -> Query:
        """Start a query on ``table``; see :class:`Query`.

        :param table: the first table.
        :param alias: its alias; ``None`` (the default) uses its name.
        :return: a query to extend and run.
        """
        return Query(self, table, alias)

    # -- writes ----------------------------------------------------------------------
    def insert(self, table: str, values: Mapping[str, object]) -> int:
        """Insert a row, in a transaction of its own.

        :param table: the table's name.
        :param values: the new row's values, by column name.
        :return: the new rowid.
        :raises ConstraintError: if the row breaks a constraint.
        """
        return self.transaction(lambda uow: uow.insert(table, values))

    def update(self, table: str, changes: Mapping[str, object], where: Where = None) -> int:
        """Update rows, in a transaction of its own.

        :param table: the table's name.
        :param changes: the new values, by column name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: the number of rows changed.
        :raises ConstraintError: if a new row breaks a constraint.
        """
        return self.transaction(lambda uow: uow.update(table, changes, where))

    def delete(self, table: str, where: Where = None) -> int:
        """Delete rows and their cascades, in a transaction of its own.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: the number of rows deleted from ``table`` itself.
        :raises ForeignKeyError: if a ``restrict`` reference forbids it.
        """
        return self.transaction(lambda uow: uow.delete(table, where))

    def apply(self, changes: Sequence[Change]) -> None:
        """Write validated changes as one commit: log first, then memory.

        The caller holds the exclusive lock.

        :param changes: the changes to write.
        """
        seq = self.commit_seq + 1
        if self.storage is not None:  # the write-ahead rule
            self.storage.append({"seq": seq, "changes": [self._encode(c) for c in changes]})
        self.commit_seq = seq
        for c in changes:
            self._apply_one(c.table, c.rowid, c.after, seq)

    def _encode(self, c: Change) -> tuple[str, int, list[Primitive] | None]:
        values = None if c.after is None else encode_row(self.tables[c.table].schema, c.after)
        return (c.table, c.rowid, values)

    def _apply_one(self, table: str, rowid: int, row: Row | None, seq: int) -> None:
        t = self.tables[table]
        if row is None:
            if rowid in t.rows:
                t.remove(rowid)
            t.row_versions.pop(rowid, None)
        else:
            t.put(rowid, row)
            t.row_versions[rowid] = seq
            t.reserve_rowid(rowid)
        t.version = seq

    def unit_of_work(self, *, deferred: bool = False, readonly: bool = False, exclusive: bool = False) -> UnitOfWork:
        """Start a transaction; see :class:`UnitOfWork`.

        :param deferred: whether to check multi-row constraints only at
            commit; ``False`` by default.
        :param readonly: whether the transaction only reads; it then holds
            the lock in shared mode and never conflicts; ``False`` by default.
        :param exclusive: whether to hold the lock alone for the whole
            transaction, so it can't conflict; ``False`` by default.
        :return: a new, active unit of work.
        """
        return UnitOfWork(self, deferred=deferred, readonly=readonly, exclusive=exclusive)

    def transaction[T](self, fn: Callable[[UnitOfWork], T], *, retries: int = 5, deferred: bool = False) -> T:
        """Run ``fn(uow)`` and commit, retrying when another transaction conflicts.

        ``fn`` may run several times, so it must not have effects outside
        the database. After ``retries`` optimistic attempts, the final
        attempt runs exclusively and can't conflict: every transaction
        finishes.

        >>> from minidb.schema import Column
        >>> from minidb.types import Integer
        >>> db = Database()
        >>> _ = db.create_table("t", [Column("n", Integer())])
        >>> db.transaction(lambda uow: uow.insert("t", {"n": 1}))
        1

        :param fn: the work to do, given a fresh unit of work each time.
        :param retries: the optimistic attempts before the exclusive one; 5 by default.
        :param deferred: whether to defer multi-row checks to commit; ``False`` by default.
        :return: whatever ``fn`` returned on the attempt that committed.
        :raises DatabaseError: whatever ``fn`` or the commit raised, other
            than a conflict.
        """
        for attempt in range(retries):
            try:
                return self._attempt(self.unit_of_work(deferred=deferred), fn)
            except ConflictError:
                time.sleep(random.uniform(0, 0.0005 * 2**attempt))  # noqa: S311 - back-off jitter, not cryptography
        return self._attempt(self.unit_of_work(deferred=deferred, exclusive=True), fn)

    @staticmethod
    def _attempt[T](uow: UnitOfWork, fn: Callable[[UnitOfWork], T]) -> T:
        try:
            result = fn(uow)
            uow.commit()
        except BaseException:
            if uow.state == "active":
                uow.rollback()
            raise
        return result

    # -- concurrency control ------------------------------------------------------------
    def active_unit_of_work(self) -> UnitOfWork | None:
        """Return the calling thread's active unit of work, if it has one.

        :return: the unit of work, or ``None``.
        """
        uow: UnitOfWork | None = getattr(self._local, "uow", None)
        return uow

    def begin(self, uow: UnitOfWork) -> None:
        """Register a new unit of work, taking the lock it needs for its lifetime.

        Optimistic units of work take no lock at all; read-only ones share
        it; exclusive ones hold it alone. Units of work call this
        themselves; applications don't need to.

        :param uow: the unit of work that is starting.
        :raises TransactionError: if the thread already has an active one.
        """
        if self.active_unit_of_work() is not None:
            raise TransactionError("this thread already has an active unit of work")
        if uow.readonly:
            self._lock.acquire_read()
        elif uow.exclusive:
            self._lock.acquire_write()
        self._local.uow = uow

    def end(self, uow: UnitOfWork) -> None:
        """Unregister a finishing unit of work, releasing any lock it held.

        :param uow: the unit of work that is finishing.
        """
        self._local.uow = None
        if uow.readonly:
            self._lock.release_read()
        elif uow.exclusive:
            self._lock.release_write()

    @contextmanager
    def reading(self) -> Iterator[Database]:
        """Hold the lock in shared mode for one read outside any unit of work.

        :return: a context manager that yields the database.
        :raises TransactionError: if the thread has an active unit of work.
        """
        if self.active_unit_of_work() is not None:
            raise TransactionError("inside a unit of work, read through the unit of work")
        with self._lock.read():
            yield self

    # -- persistence ---------------------------------------------------------------------
    def attach(self, storage: Storage) -> None:
        """Load the saved data, and log every future commit to ``storage``.

        Declare the tables first, then attach.

        :param storage: where the data lives.
        :raises SchemaError: if storage is already attached, data was
            inserted before attaching, or the stored data was written with a
            different schema.
        """
        with self.exclusive_lock():
            self._check_attachable()
            state = storage.read_snapshot()
            if state is not None:
                self._load_state(state)
            for record in storage.read_log():
                if record["seq"] > self.commit_seq:  # else it is in the snapshot already
                    self._replay(record)
            self.storage = storage

    def _check_attachable(self) -> None:
        if self.storage is not None:
            raise SchemaError("storage already attached")
        if any(len(t) for t in self.tables.values()):
            raise SchemaError("attach storage before inserting data")

    def _replay(self, record: LogRecord) -> None:
        for table, rowid, values in record["changes"]:
            row = None if values is None else decode_row(self.tables[table].schema, values)
            self._apply_one(table, rowid, row, record["seq"])
        self.commit_seq = record["seq"]

    def checkpoint(self) -> None:
        """Write a snapshot and empty the log. Writers wait; readers don't.

        :raises SchemaError: if no storage is attached.
        """
        if self.storage is None:
            raise SchemaError("no storage attached")
        with self.shared_lock():
            tables: dict[str, TableData] = {
                name: {
                    "next_rowid": t.next_rowid,
                    "rows": [(rid, encode_row(t.schema, row)) for rid, row in t.rows.items()],
                }
                for name, t in self.tables.items()
            }
            self.storage.write_snapshot(
                {"format": 1, "fingerprint": self._fingerprint(), "commit_seq": self.commit_seq, "tables": tables}
            )
            self.storage.truncate_log()

    def _fingerprint(self) -> str:
        return schema_fingerprint(self.tables, self.foreign_keys)

    def _load_state(self, state: Snapshot) -> None:
        if state["fingerprint"] != self._fingerprint():
            raise SchemaError("stored data was written with a different schema")
        self.commit_seq = state["commit_seq"]
        for name, data in state["tables"].items():
            t = self.tables[name]
            for rowid, values in data["rows"]:
                t.put(rowid, decode_row(t.schema, values))
                t.row_versions[rowid] = self.commit_seq
            t.reserve_rowid(data["next_rowid"] - 1)
            t.version = self.commit_seq

    def close(self) -> None:
        """Close the attached storage's files, if any."""
        if self.storage is not None:
            self.storage.close()

    def analyze(self) -> None:
        """Count the distinct values of every column, for the planner (like SQL's ANALYZE)."""
        with self.reading():
            for t in self.tables.values():
                t.stats = {c: len({row[c] for row in t.rows.values()} - {None}) for c in t.columns}
