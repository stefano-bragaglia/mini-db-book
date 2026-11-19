"""Plan writes: turn operations into validated lists of :class:`Change`.

Planners read from a *state*, anything satisfying :class:`State`, and never
modify it. Applying the changes they return is someone else's job.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Literal
from typing import Protocol

from minidb.errors import ForeignKeyError
from minidb.errors import UniqueError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from collections.abc import Sequence

    from minidb.schema import ForeignKey
    from minidb.schema import TableSchema
    from minidb.table import Where
    from minidb.values import Row
    from minidb.values import Value

type RowRef = tuple[str, int]  # (table name, rowid)
type ChangeKind = Literal["insert", "update", "delete"]


class TableLike(Protocol):
    """Describe the table interface that planners use: a table, or a view of one."""

    name: str
    schema: TableSchema

    def row(self, rowid: int) -> Row:
        """Return the stored row itself; raise ``KeyError`` if it doesn't exist."""
        ...

    def match(self, where: Where = None) -> list[int]:
        """Return the rowids of the rows matching ``where``."""
        ...

    def lookup(self, key: Mapping[str, Value | None]) -> set[int]:
        """Return the rowids whose columns equal ``key``, through an index."""
        ...

    def unique_keys(self) -> list[tuple[str, ...]]:
        """Return the column tuples of every unique index."""
        ...

    def new_rowid(self) -> int:
        """Hand out a rowid that has never been used."""
        ...


class State(Protocol):
    """Describe what planners read from: a database, or a transaction's view of one."""

    @property
    def foreign_keys(self) -> Sequence[ForeignKey]:
        """Return every foreign key between the tables."""
        ...

    def table(self, name: str) -> TableLike:
        """Return the table called ``name``."""
        ...


@dataclass(frozen=True)
class Change:
    """Record that, in ``table``, row ``rowid`` went from ``before`` to ``after``.

    ``before=None`` describes an insert and ``after=None`` a delete.

    >>> c = Change("t", 7, None, {"n": 1})
    >>> c.kind, c.inverted().kind
    ('insert', 'delete')

    :param table: the table's name.
    :param rowid: the row's rowid.
    :param before: the row before the change, or ``None`` if it didn't exist.
    :param after: the row after the change, or ``None`` if it no longer exists.
    """

    table: str
    rowid: int
    before: Row | None
    after: Row | None

    @property
    def kind(self) -> ChangeKind:
        """Return ``"insert"``, ``"update"`` or ``"delete"``."""
        if self.before is None:
            return "insert"
        return "delete" if self.after is None else "update"

    def inverted(self) -> Change:
        """Return the change that undoes this one.

        :return: the same change with ``before`` and ``after`` swapped.
        """
        return Change(self.table, self.rowid, self.after, self.before)


# -- the three operations ----------------------------------------------------------------
def plan_insert(state: State, table: str, values: Mapping[str, object], *, check: bool = True) -> list[Change]:
    """Plan inserting one row.

    :param state: where to read the current data.
    :param table: the table's name.
    :param values: the new row's values, by column name.
    :param check: whether to check uniqueness and references now;
        ``True`` by default. Single-row constraints are always checked.
    :return: the single insert change, with a newly allocated rowid.
    :raises ConstraintError: if the row breaks a constraint.
    """
    t = state.table(table)
    row = t.schema.prepare_row(values)
    if check:
        check_unique(t, [(None, row)])
        check_parents_exist(state, t, [row])
    return [Change(table, t.new_rowid(), None, row)]


def plan_update(
    state: State,
    table: str,
    changes: Mapping[str, object],
    where: Where = None,
    *,
    rowids: Iterable[int] | None = None,
    check: bool = True,
) -> list[Change]:
    """Plan setting ``changes`` on some rows.

    :param state: where to read the current data.
    :param table: the table's name.
    :param changes: the new values, by column name.
    :param where: which rows change; ``None`` (the default) for all.
    :param rowids: the exact rows to change, instead of ``where``; ``None``
        (the default) to use ``where``.
    :param check: whether to check uniqueness and references now;
        ``True`` by default.
    :return: one update change per row.
    :raises ConstraintError: if a new row breaks a constraint.
    """
    t = state.table(table)
    targets = t.match(where) if rowids is None else rowids
    old = {rid: t.row(rid) for rid in targets}
    new = {rid: t.schema.prepare_row(changes, base=row) for rid, row in old.items()}
    if check:
        check_unique(t, list(new.items()))
        check_parents_exist(state, t, new.values())
        check_no_orphans(state, t, old, new)
    return [Change(table, rid, old[rid], new[rid]) for rid in new]


def plan_delete(
    state: State, table: str, where: Where = None, *, rowids: Iterable[int] | None = None, check: bool = True
) -> list[Change]:
    """Plan a delete and everything it implies: cascades and SET NULL updates.

    :param state: where to read the current data.
    :param table: the table's name.
    :param where: which rows go; ``None`` (the default) for all.
    :param rowids: the exact rows to delete, instead of ``where``; ``None``
        (the default) to use ``where``.
    :param check: whether to refuse ``restrict``-ed deletes now; ``True``
        by default. Cascades and SET NULL are actions, so they always run.
    :return: the delete changes, followed by any SET NULL updates.
    :raises ForeignKeyError: if ``check`` and a ``restrict`` reference
        forbids the delete.
    """
    t = state.table(table)
    deleted = _cascade(state, table, t.match(where) if rowids is None else rowids)
    nulled = _nulled_children(state, deleted, check=check)
    return [Change(n, rid, row, None) for (n, rid), row in deleted.items()] + [
        Change(n, rid, b, a) for (n, rid), (b, a) in nulled.items()
    ]


def _cascade(state: State, table: str, rowids: Iterable[int]) -> dict[RowRef, Row]:
    """Collect the rows to delete, following ON DELETE CASCADE transitively."""
    deleted: dict[RowRef, Row] = {}
    stack = [(table, rid) for rid in rowids]
    while stack:
        ref = stack.pop()
        if ref in deleted:
            continue  # cycles and diamonds
        row = deleted[ref] = state.table(ref[0]).row(ref[1])
        for fk in references_to(state, ref[0]):
            if fk.on_delete == "cascade":
                stack.extend((fk.table, c) for c in children(state, fk, row))
    return deleted


def _nulled_children(state: State, deleted: dict[RowRef, Row], *, check: bool) -> dict[RowRef, tuple[Row, Row]]:
    """Restrict or null every child that survives the cascade."""
    nulled: dict[RowRef, tuple[Row, Row]] = {}
    for (name, _), row in deleted.items():
        for fk in references_to(state, name):
            survivors = [c for c in children(state, fk, row) if (fk.table, c) not in deleted]
            if survivors:
                _restrict_or_null(state, fk, row, survivors, nulled, check=check)
    return nulled


def _restrict_or_null(
    state: State,
    fk: ForeignKey,
    parent_row: Row,
    survivors: list[int],
    nulled: dict[RowRef, tuple[Row, Row]],
    *,
    check: bool,
) -> None:
    if fk.on_delete == "restrict":
        if check:
            raise ForeignKeyError(
                f"{fk.name}: {fk.ref_table} row {fk.child_key(parent_row)} is still "
                f"referenced by {len(survivors)} {fk.table} row(s)"
            )
        return
    if fk.on_delete == "set null":
        child = state.table(fk.table)
        for c in survivors:
            before = child.row(c)
            base = nulled.get((fk.table, c), (before, before))[1]
            nulled[fk.table, c] = (before, child.schema.prepare_row(dict.fromkeys(fk.columns), base=base))


# -- constraint checks ---------------------------------------------------------------------
def check_unique(t: TableLike, batch: list[tuple[int | None, Row]]) -> None:
    """Check that no two rows would share a unique key after applying ``batch``.

    :param t: the table.
    :param batch: pairs of a rowid (``None`` for a new row) and the row it
        will hold.
    :raises UniqueError: if two rows would share a unique key.
    """
    changing = {rid for rid, _ in batch if rid is not None}
    for columns in t.unique_keys():
        _check_unique_key(t, columns, batch, changing)


def _check_unique_key(
    t: TableLike, columns: tuple[str, ...], batch: list[tuple[int | None, Row]], changing: set[int]
) -> None:
    seen: set[tuple[Value | None, ...]] = set()
    for _, row in batch:
        key = tuple(row[c] for c in columns)
        if any(v is None for v in key):
            continue
        if key in seen or t.lookup(dict(zip(columns, key, strict=True))) - changing:
            shown = ", ".join(f"{c}={v!r}" for c, v in zip(columns, key, strict=True))
            raise UniqueError(f"{t.name}: duplicate key ({shown})")
        seen.add(key)


def references_from(state: State, table: str) -> list[ForeignKey]:
    """Return the foreign keys of ``table`` (where it is the child).

    :param state: the database or view.
    :param table: the table's name.
    :return: the foreign keys declared on ``table``.
    """
    return [fk for fk in state.foreign_keys if fk.table == table]


def references_to(state: State, table: str) -> list[ForeignKey]:
    """Return the foreign keys that reference ``table`` (where it is the parent).

    :param state: the database or view.
    :param table: the table's name.
    :return: the foreign keys pointing at ``table``.
    """
    return [fk for fk in state.foreign_keys if fk.ref_table == table]


def children(state: State, fk: ForeignKey, parent_row: Row) -> set[int]:
    """Return the rowids of the rows that reference ``parent_row`` through ``fk``.

    :param state: the database or view.
    :param fk: the foreign key.
    :param parent_row: a row of the referenced table.
    :return: the referencing rowids in the child table.
    """
    return state.table(fk.table).lookup(fk.child_key(parent_row))


def check_parents_exist(
    state: State, child: TableLike, rows: Iterable[Row], fks: Sequence[ForeignKey] | None = None
) -> None:
    """Check, from the child side, that every non-NULL reference finds its parent.

    :param state: the database or view.
    :param child: the referencing table.
    :param rows: the rows to check.
    :param fks: the foreign keys to check; ``None`` (the default) for all of
        ``child``'s.
    :raises ForeignKeyError: if a reference points at nothing.
    """
    for fk in fks if fks is not None else references_from(state, child.name):
        parent = state.table(fk.ref_table)
        for row in rows:
            key = fk.parent_key(row)
            if key is not None and not parent.lookup(key):
                raise ForeignKeyError(f"{fk.name}: no {parent.name} row with {key}")


def check_no_orphans(state: State, parent: TableLike, old: dict[int, Row], new: dict[int, Row]) -> None:
    """Check, from the parent side of an update, that no referenced key changes.

    :param state: the database or view.
    :param parent: the table being updated.
    :param old: the rows before the update, by rowid.
    :param new: the rows after the update, by rowid.
    :raises ForeignKeyError: if a changed key is still referenced.
    """
    for fk in references_to(state, parent.name):
        for rid, before in old.items():
            if fk.child_key(before) != fk.child_key(new[rid]) and children(state, fk, before):
                raise ForeignKeyError(
                    f"{fk.name}: cannot change {parent.name} key {fk.child_key(before)}, it is still referenced"
                )


def net_changes(changes: Iterable[Change]) -> list[Change]:
    """Collapse a sequence of changes to one per row: its first before, its last after.

    A row inserted and then deleted becomes "nothing happened", and is dropped.

    >>> net_changes([Change("t", 1, None, {"n": 1}), Change("t", 1, {"n": 1}, {"n": 2})])
    [Change(table='t', rowid=1, before=None, after={'n': 2})]

    :param changes: the changes, in the order they were made.
    :return: the net changes, in order of each row's first change.
    """
    net: dict[RowRef, Change] = {}
    for c in changes:
        key = (c.table, c.rowid)
        net[key] = Change(c.table, c.rowid, net[key].before, c.after) if key in net else c
    return [c for c in net.values() if c.before is not None or c.after is not None]


def check_deferred(state: State, changes: Iterable[Change]) -> None:
    """Check multi-row constraints over a transaction's net effect, in its final state.

    :param state: the transaction's view, which already includes ``changes``.
    :param changes: everything the transaction did.
    :raises UniqueError: if two rows share a unique key.
    :raises ForeignKeyError: if a reference points at nothing.
    """
    by_table: dict[str, list[Change]] = {}
    for c in net_changes(changes):
        by_table.setdefault(c.table, []).append(c)
    for name, cs in by_table.items():
        t = state.table(name)
        written = [(c.rowid, c.after) for c in cs if c.after is not None]
        check_unique(t, [(rid, row) for rid, row in written])
        check_parents_exist(state, t, [row for _, row in written])
        for c in cs:
            if c.before is not None:
                check_not_dangling(state, t, c.before)


def check_not_dangling(state: State, parent: TableLike, old_row: Row) -> None:
    """Check that, if ``old_row``'s key is gone, nothing still references it.

    :param state: the transaction's view.
    :param parent: the table ``old_row`` was in.
    :param old_row: a row that was deleted, or whose key may have changed.
    :raises ForeignKeyError: if children still reference the vanished key.
    """
    for fk in references_to(state, parent.name):
        key = {r: old_row[r] for r in fk.ref_columns}
        if any(v is None for v in key.values()) or parent.lookup(key):
            continue  # NULL key, or a row still has it
        if children(state, fk, old_row):
            raise ForeignKeyError(f"{fk.name}: {parent.name} row {key} is gone but still referenced")
