"""Declare tables: their columns, and the pipeline that prepares rows."""

from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Literal

from minidb.errors import CheckError
from minidb.errors import DomainError
from minidb.errors import NotNullError
from minidb.errors import SchemaError

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Mapping

    from minidb.types import Type
    from minidb.values import Row
    from minidb.values import Value

type Normalizer = Callable[[Value], Value]

type OnDelete = Literal["restrict", "cascade", "set null"]

type RowCheck = Callable[[Mapping[str, Value | None]], object]

ON_DELETE_ACTIONS: tuple[OnDelete, ...] = ("restrict", "cascade", "set null")


@dataclass(frozen=True)
class Check:
    """Declare a named row-level CHECK constraint.

    >>> positive = Check("positive", lambda row: row["n"] > 0)
    >>> positive.predicate({"n": 3})
    True

    :param name: names the constraint in error messages.
    :param predicate: a function of the whole row returning ``True``,
        ``False`` or ``None`` (UNKNOWN); only ``False`` rejects the row.
    """

    name: str
    predicate: RowCheck


@dataclass(frozen=True)
class Column:
    """Declare a column: its name, type, normalizers and single-column constraints.

    >>> from minidb.types import Integer
    >>> qty = Column("qty", Integer(), nullable=False, default=0, check=lambda q: q >= 0)
    >>> qty.make_default(), qty.prepare("5")
    (0, 5)

    :param name: the column's name.
    :param type: the column's type.
    :param normalizers: functions applied to every non-NULL value after the
        type has normalized it; none by default.
    :param nullable: whether the column may hold NULL; ``True`` by default.
    :param default: the value for inserts that omit the column: a value,
        or a function of no arguments that returns one; ``None`` by default.
    :param check: a CHECK on non-NULL values, returning ``True``, ``False``
        or ``None`` (UNKNOWN); ``None`` (the default) for no check.
    """

    name: str
    type: Type[Value]
    normalizers: tuple[Normalizer, ...] = ()
    nullable: bool = True
    default: Value | Callable[[], Value | None] | None = None
    check: Callable[[Value], bool | None] | None = None

    def make_default(self) -> Value | None:
        """Return the default value, calling the default if it is a function.

        :return: the value an insert should use when it omits this column.
        """
        return self.default() if callable(self.default) else self.default

    def prepare(self, value: object) -> Value | None:
        """Normalize, then validate one value for this column.

        :param value: the input value, or ``None``.
        :return: the value to store.
        :raises DomainError: if the value doesn't belong to the column's type.
        """
        prepared = self.type.normalize(value)
        if prepared is not None:
            for fn in self.normalizers:
                prepared = fn(prepared)
        self.type.validate(prepared)
        return prepared


@dataclass(frozen=True)
class ForeignKey:
    """Declare that ``table.columns`` must match ``ref_table.ref_columns``, or be NULL.

    >>> fk = ForeignKey(("user_id",), "users", ("id",), table="orders")
    >>> fk.name, fk.parent_key({"user_id": 7}), fk.child_key({"id": 7})
    ('fk_orders_user_id', {'id': 7}, {'user_id': 7})

    :param columns: the referencing columns of the child table; a single
        name is also accepted.
    :param ref_table: the referenced (parent) table.
    :param ref_columns: the referenced columns, which must form a key;
        ``()`` (the default) means the parent's primary key.
    :param on_delete: what deleting a referenced row does: ``"restrict"``
        (the default) refuses, ``"cascade"`` deletes the children too, and
        ``"set null"`` sets their foreign-key columns to NULL.
    :param table: the child table; :meth:`Database.create_table` fills it in.
    :raises SchemaError: if ``on_delete`` is not one of the three actions.
    """

    columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...] = ()
    on_delete: OnDelete = "restrict"
    table: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", as_key(self.columns))
        object.__setattr__(self, "ref_columns", as_key(self.ref_columns))
        if self.on_delete not in ON_DELETE_ACTIONS:
            raise SchemaError(f"on_delete must be one of {ON_DELETE_ACTIONS}")

    @property
    def name(self) -> str:
        """Return the constraint's name, derived from the child table and columns."""
        return f"fk_{self.table}_{'_'.join(self.columns)}"

    def child_key(self, parent_row: Mapping[str, Value | None]) -> dict[str, Value | None]:
        """Return ``{column: value}`` that the children of ``parent_row`` have.

        :param parent_row: a row of the parent table.
        :return: the key to look up in the child table.
        """
        return {c: parent_row[r] for c, r in zip(self.columns, self.ref_columns, strict=True)}

    def parent_key(self, child_row: Mapping[str, Value | None]) -> dict[str, Value | None] | None:
        """Return ``{ref_column: value}`` for the parent ``child_row`` points at.

        :param child_row: a row of the child table.
        :return: the parent's key, or ``None`` if any referencing value is
            NULL: such a row references nothing (SQL's ``MATCH SIMPLE``).
        """
        values = [child_row[c] for c in self.columns]
        if any(v is None for v in values):
            return None
        return dict(zip(self.ref_columns, values, strict=True))


@dataclass(frozen=True)
class TableSchema:
    """Declare a table, its keys, and the constraint pipeline for its rows.

    Primary-key columns are made NOT NULL automatically.

    >>> from minidb.types import Integer
    >>> schema = TableSchema("t", (Column("id", Integer()),), primary_key=("id",))
    >>> schema.column("id").nullable
    False

    :param name: the table's name.
    :param columns: its columns, in order.
    :param checks: its row-level CHECK constraints; none by default.
    :param primary_key: the primary-key columns; ``()`` (the default) for none.
    :param unique: the column tuples of its UNIQUE constraints; none by default.
    :raises SchemaError: if two columns share a name, or a key names an
        unknown column.
    """

    name: str
    columns: tuple[Column, ...]
    checks: tuple[Check, ...] = ()
    primary_key: tuple[str, ...] = ()
    unique: tuple[tuple[str, ...], ...] = ()
    by_name: Mapping[str, Column] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise SchemaError(f"duplicate column names in {self.name!r}")
        for key in (self.primary_key, *self.unique):
            if missing := set(key) - set(names):
                raise SchemaError(f"{self.name}: key uses unknown column(s) {sorted(missing)}")
        # entity integrity: primary-key columns are implicitly NOT NULL
        pk = set(self.primary_key)
        columns = tuple(replace(c, nullable=False) if c.name in pk else c for c in self.columns)
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "by_name", {c.name: c for c in columns})

    @property
    def column_names(self) -> tuple[str, ...]:
        """Return the column names, in order."""
        return tuple(c.name for c in self.columns)

    def column(self, name: str) -> Column:
        """Return the column called ``name``.

        :param name: the column's name.
        :return: the column.
        :raises SchemaError: if there is no such column.
        """
        try:
            return self.by_name[name]
        except KeyError:
            raise SchemaError(f"{self.name}: no such column {name!r}") from None

    def prepare_row(self, values: Mapping[str, object], base: Row | None = None) -> Row:
        """Run the constraint pipeline and return a complete, valid row.

        The stages run in a fixed order: defaults (for inserts), types,
        NOT NULL, column checks, row checks. Neither argument is modified.

        :param values: the user's input, by column name.
        :param base: the existing row, for an update; ``None`` (the default)
            for an insert.
        :return: the row to store.
        :raises SchemaError: if ``values`` names an unknown column.
        :raises DomainError: if a value doesn't belong to its column's type.
        :raises NotNullError: if a NOT NULL column would hold NULL.
        :raises CheckError: if a CHECK constraint is false.
        """
        for name in values:
            self.column(name)  # unknown column?
        row: Row = dict(base) if base is not None else {}
        for name, value in self._pending(values, base).items():
            try:
                row[name] = self.by_name[name].prepare(value)
            except DomainError as e:
                raise DomainError(f"{self.name}.{name}: {e}") from None
        self._check_not_null(row)
        self._check_columns(row)
        self._check_rows(row)
        return row

    # -- stages ---------------------------------------------------------------

    def _check_columns(self, row: Row) -> None:
        for c in self.columns:
            value = row[c.name]
            if c.check is not None and value is not None and c.check(value) is False:
                raise CheckError(f"{self.name}.{c.name}: check failed for {value!r}")

    def _check_not_null(self, row: Row) -> None:
        for c in self.columns:
            if not c.nullable and row[c.name] is None:
                raise NotNullError(f"{self.name}.{c.name} may not be NULL")

    def _check_rows(self, row: Row) -> None:
        view = MappingProxyType(row)
        for check in self.checks:
            if check.predicate(view) is False:
                raise CheckError(f"{self.name}: check {check.name!r} failed")

    def _pending(self, values: Mapping[str, object], base: Row | None) -> dict[str, object]:
        """Return the raw values that still need preparing, by column.

        An insert prepares every column, using defaults for missing ones; an
        update prepares only the columns it changes.
        """
        if base is not None:
            return dict(values)
        return {c.name: values[c.name] if c.name in values else c.make_default() for c in self.columns}


def as_key(columns: str | Iterable[str]) -> tuple[str, ...]:
    """Turn one column name or several into a tuple of names.

    >>> as_key("id"), as_key(["a", "b"])
    (('id',), ('a', 'b'))

    :param columns: a column name, or an iterable of them.
    :return: the names as a tuple.
    """
    return (columns,) if isinstance(columns, str) else tuple(columns)
