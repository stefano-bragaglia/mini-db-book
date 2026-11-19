"""Provide the public entry point: tables, cross-table constraints and CRUD."""

from dataclasses import replace
from typing import TYPE_CHECKING

from minidb.errors import DatabaseError
from minidb.errors import ForeignKeyError
from minidb.errors import SchemaError
from minidb.schema import as_key
from minidb.schema import TableSchema
from minidb.table import Table

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from collections.abc import Sequence

    from minidb.schema import Check
    from minidb.schema import Column
    from minidb.schema import ForeignKey
    from minidb.table import Where
    from minidb.values import Row

type RowRef = tuple[str, int]  # (table name, rowid)


class Database:
    """Hold tables and the foreign keys between them, and run CRUD on them.

    Each write runs the table's own checks *and* the cross-table checks
    before anything is written, so every statement is atomic.
    """

    def __init__(self) -> None:
        self.tables: dict[str, Table] = {}
        self.foreign_keys: list[ForeignKey] = []

    # -- schema -----------------------------------------------------------------
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
        """Create an empty table and return it.

        Creating the table and its foreign keys is all or nothing.

        >>> from minidb.schema import Column, ForeignKey
        >>> from minidb.types import Integer
        >>> db = Database()
        >>> _ = db.create_table("users", [Column("id", Integer())], primary_key="id")
        >>> orders = db.create_table(
        ...     "orders", [Column("user_id", Integer())], foreign_keys=[ForeignKey("user_id", "users")]
        ... )
        >>> sorted(orders.indexes)
        ['fk_orders_user_id']

        :param name: the new table's name.
        :param columns: its columns, in order.
        :param primary_key: the primary-key column or columns; none by default.
        :param unique: the columns of each UNIQUE constraint; none by default.
        :param checks: its row-level CHECK constraints; none by default.
        :param foreign_keys: its references to other tables (or to itself);
            none by default.
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
            self._forget_table(name)  # all or nothing
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
        if child.index_on(fk.columns) is None:  # for parent -> child lookups
            child.create_index(fk.name, fk.columns)
        self._check_parents_exist(child, child.rows.values(), [fk])
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

    def create_index(self, table: str, name: str, columns: Sequence[str], *, unique: bool = False) -> None:
        """Create an index on ``table``; see :meth:`Table.create_index`.

        :param table: the table's name.
        :param name: the index's name.
        :param columns: the indexed columns, in key order.
        :param unique: whether to refuse duplicate keys; ``False`` by default.
        """
        self.table(table).create_index(name, columns, unique=unique)

    # -- reads ------------------------------------------------------------------
    def get(self, table: str, rowid: int) -> Row | None:
        """Return a copy of one row, or ``None``; see :meth:`Table.get`.

        :param table: the table's name.
        :param rowid: the row to fetch.
        :return: the row, or ``None``.
        """
        return self.table(table).get(rowid)

    def select(self, table: str, where: Where = None) -> list[Row]:
        """Return the rows of ``table`` matching ``where``; see :meth:`Table.match`.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: copies of the matching rows.
        """
        return self.table(table).select(where)

    # -- writes: check everything, then apply -------------------------------------
    def insert(self, table: str, values: Mapping[str, object]) -> int:
        """Insert a row after checking its own constraints and its references.

        :param table: the table's name.
        :param values: the new row's values, by column name.
        :return: the new rowid.
        :raises ConstraintError: if the row breaks a constraint.
        """
        t = self.table(table)
        row = t.schema.prepare_row(values)
        t.check_unique([(None, row)])
        self._check_parents_exist(t, [row])
        rowid = t.new_rowid()
        t.put(rowid, row)
        return rowid

    def update(self, table: str, changes: Mapping[str, object], where: Where = None) -> int:
        """Update rows, refusing changes that break references in either direction.

        :param table: the table's name.
        :param changes: the new values, by column name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: the number of rows changed.
        :raises ConstraintError: if a new row breaks a constraint.
        :raises ForeignKeyError: if a changed key is still referenced.
        """
        t = self.table(table)
        old = {rid: t.rows[rid] for rid in t.match(where)}
        new = {rid: t.schema.prepare_row(changes, base=row) for rid, row in old.items()}
        t.check_unique(list(new.items()))
        self._check_parents_exist(t, new.values())
        self._check_no_orphans(t, old, new)
        for rid, row in new.items():
            t.put(rid, row)
        return len(new)

    def delete(self, table: str, where: Where = None) -> int:
        """Delete rows and everything their deletion implies, or nothing at all.

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: the number of rows deleted from ``table`` itself, not
            counting cascades.
        :raises ForeignKeyError: if a ``restrict`` reference forbids the delete.
        :raises ConstraintError: if a ``set null`` makes a row invalid.
        """
        t = self.table(table)
        deleted, nulled = self._plan_delete(t, t.match(where))
        for name, rid in deleted:
            self.tables[name].remove(rid)
        for (name, rid), row in nulled.items():
            self.tables[name].put(rid, row)
        return sum(1 for name, _ in deleted if name == table)

    # -- referential integrity ------------------------------------------------------
    def _references_from(self, table: str) -> list[ForeignKey]:
        return [fk for fk in self.foreign_keys if fk.table == table]

    def _references_to(self, table: str) -> list[ForeignKey]:
        return [fk for fk in self.foreign_keys if fk.ref_table == table]

    def _check_parents_exist(self, child: Table, rows: Iterable[Row], fks: list[ForeignKey] | None = None) -> None:
        """Check, from the child side, that every non-NULL reference finds its parent."""
        for fk in fks if fks is not None else self._references_from(child.name):
            parent = self.tables[fk.ref_table]
            for row in rows:
                key = fk.parent_key(row)
                if key is not None and not parent.lookup(key):
                    raise ForeignKeyError(f"{fk.name}: no {parent.name} row with {key}")

    def _children(self, fk: ForeignKey, parent_row: Row) -> set[int]:
        return self.tables[fk.table].lookup(fk.child_key(parent_row))

    def _check_no_orphans(self, parent: Table, old: dict[int, Row], new: dict[int, Row]) -> None:
        """Check, from the parent side of an update, that no referenced key changes."""
        for fk in self._references_to(parent.name):
            for rid, before in old.items():
                if fk.child_key(before) != fk.child_key(new[rid]) and self._children(fk, before):
                    raise ForeignKeyError(
                        f"{fk.name}: cannot change {parent.name} key {fk.child_key(before)}, it is still referenced"
                    )

    def _plan_delete(self, table: Table, rowids: Iterable[int]) -> tuple[dict[RowRef, Row], dict[RowRef, Row]]:
        """Work out everything a delete implies, without changing anything.

        Pass 1 follows ``ON DELETE CASCADE`` transitively; only then does
        pass 2 ask which children *survive*, and restrict or null them.

        :return: ``(deleted, nulled)``: the rows to remove, and the new rows
            for the children that ``ON DELETE SET NULL`` changes.
        """
        deleted = self._cascade(table, rowids)
        nulled: dict[RowRef, Row] = {}
        for (name, _), row in deleted.items():
            for fk in self._references_to(name):
                survivors = [c for c in self._children(fk, row) if (fk.table, c) not in deleted]
                if survivors:
                    self._restrict_or_null(fk, row, survivors, nulled)
        return deleted, nulled

    def _cascade(self, table: Table, rowids: Iterable[int]) -> dict[RowRef, Row]:
        """Collect the rows to delete, following cascades with an explicit stack."""
        deleted: dict[RowRef, Row] = {}
        stack = [(table.name, rid) for rid in rowids]
        while stack:
            ref = stack.pop()
            if ref in deleted:
                continue  # cycles and diamonds
            row = deleted[ref] = self.tables[ref[0]].rows[ref[1]]
            for fk in self._references_to(ref[0]):
                if fk.on_delete == "cascade":
                    stack.extend((fk.table, c) for c in self._children(fk, row))
        return deleted

    def _restrict_or_null(
            self, fk: ForeignKey, parent_row: Row, survivors: list[int], nulled: dict[RowRef, Row]
    ) -> None:
        """Refuse the delete for ``restrict``, or plan the updates for ``set null``."""
        if fk.on_delete == "restrict":
            raise ForeignKeyError(
                f"{fk.name}: {fk.ref_table} row {fk.child_key(parent_row)} is still "
                f"referenced by {len(survivors)} {fk.table} row(s)"
            )
        child = self.tables[fk.table]
        for c in survivors:
            base = nulled.get((fk.table, c), child.rows[c])
            nulled[fk.table, c] = child.schema.prepare_row(dict.fromkeys(fk.columns), base=base)
