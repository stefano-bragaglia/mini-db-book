"""Declare tables: their columns, and the pipeline that prepares rows."""

from dataclasses import dataclass
from dataclasses import field
from types import MappingProxyType
from typing import TYPE_CHECKING

from minidb.errors import CheckError
from minidb.errors import DomainError
from minidb.errors import NotNullError
from minidb.errors import SchemaError

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

    from minidb.types import Type
    from minidb.values import Row
    from minidb.values import Value

type Normalizer = Callable[[Value], Value]
type RowCheck = Callable[[Mapping[str, Value | None]], object]


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


# src/minidb/schema.py (replace TableSchema)
@dataclass(frozen=True)
class TableSchema:
    """Declare a table and run the constraint pipeline that prepares its rows.

    >>> from minidb.types import Integer
    >>> schema = TableSchema("t", (Column("n", Integer(), nullable=False, default=1),))
    >>> schema.prepare_row({})
    {'n': 1}
    >>> schema.prepare_row({"n": None})
    Traceback (most recent call last):
      ...
    minidb.errors.NotNullError: t.n may not be NULL

    :param name: the table's name.
    :param columns: its columns, in order.
    :param checks: its row-level CHECK constraints; none by default.
    :raises SchemaError: if two columns share a name.
    """

    name: str
    columns: tuple[Column, ...]
    checks: tuple[Check, ...] = ()
    by_name: Mapping[str, Column] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise SchemaError(f"duplicate column names in {self.name!r}")
        object.__setattr__(self, "by_name", {c.name: c for c in self.columns})

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
    def _pending(self, values: Mapping[str, object], base: Row | None) -> dict[str, object]:
        """Return the raw values that still need preparing, by column.

        An insert prepares every column, using defaults for missing ones; an
        update prepares only the columns it changes.
        """
        if base is not None:
            return dict(values)
        return {c.name: values[c.name] if c.name in values else c.make_default() for c in self.columns}

    def _check_not_null(self, row: Row) -> None:
        for c in self.columns:
            if not c.nullable and row[c.name] is None:
                raise NotNullError(f"{self.name}.{c.name} may not be NULL")

    def _check_columns(self, row: Row) -> None:
        for c in self.columns:
            value = row[c.name]
            if c.check is not None and value is not None and c.check(value) is False:
                raise CheckError(f"{self.name}.{c.name}: check failed for {value!r}")

    def _check_rows(self, row: Row) -> None:
        view = MappingProxyType(row)
        for check in self.checks:
            if check.predicate(view) is False:
                raise CheckError(f"{self.name}: check {check.name!r} failed")
