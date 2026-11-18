"""Declarative table definitions."""
from dataclasses import dataclass
from dataclasses import field
from functools import reduce
from types import MappingProxyType
from typing import Callable
from typing import Mapping

from minidb import DomainError
from minidb import SchemaError
from minidb.errors import CheckViolation
from minidb.errors import NotNullViolation
from minidb.normalizers import Normalizer
from minidb.types import Type

type Row = dict[str, object]

_NO_DEFAULT = object()

type CheckFn = Callable[[object], bool | None]


@dataclass(frozen=True)
class Column:
    name: str
    type: Type
    normalizers: tuple[Normalizer, ...] = field(default_factory=tuple)
    nullable: bool = True
    default: object = None
    check: CheckFn | None = None

    def prepare(self, value: object) -> Type:
        """Normalize, then validate one value. Raises DomainError."""
        value = self.type.normalize(value)
        if value is not None:
            value = reduce(lambda acc, fn: fn(acc), self.normalizers, value)
        self.type.validate(value)
        return value


@dataclass(frozen=True)
class Check:
    """A named row-level CHECK. `predicate(row)` returns True, False or None."""
    name: str
    predicate: Callable[[Mapping[str, object]], bool | None]


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[Column, ...]
    checks: tuple[Check, ...] = ()
    by_name: Mapping[str, Column] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, 'columns', tuple(self.columns))
        object.__setattr__(self, "checks", tuple(self.checks))
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise SchemaError(f"duplicate column names in {self.name!r}")
        object.__setattr__(self, 'by_name', {c.name: c for c in self.columns})

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns)

    def column(self, name: str) -> Column:
        try:
            return self.by_name[name]
        except KeyError:
            raise SchemaError(f"{self.name}: no such column {name!r}") from None

    def prepare_row(self, values: Mapping[str, object], base: Row | None = None) -> Row:
        """Return a complete, normalized, validated row.

        `values` are the user's input; `base` is the existing row for an
        update (None for an insert). Neither argument is modified.
        """
        for name in values:
            self.column(name)  # unknown column?
        if base is None:  # insert
            row = {c.name: values[c.name] if c.name in values else c.make_default()
                   for c in self.columns}
            touched = self.column_names
        else:  # update
            row = dict(base) | dict(values)
            touched = tuple(values)
        for name in touched:
            try:
                row[name] = self.by_name[name].prepare(row[name])
            except DomainError as e:
                raise DomainError(f"{self.name}.{name}: {e}") from None
        self._check_not_null(row)
        self._check_columns(row)
        self._check_rows(row)
        return row

    # -- stages ---------------------------------------------------------------
    def _check_not_null(self, row: Row) -> None:
        for c in self.columns:
            if not c.nullable and row[c.name] is None:
                raise NotNullViolation(f"{self.name}.{c.name} may not be NULL")

    def _check_columns(self, row: Row) -> None:
        for c in self.columns:
            value = row[c.name]
            if c.check is not None and value is not None and c.check(value) is False:
                raise CheckViolation(f"{self.name}.{c.name}: check failed for {value!r}")

    def _check_rows(self, row: Row) -> None:
        view = MappingProxyType(row)
        for check in self.checks:
            if check.predicate(view) is False:
                raise CheckViolation(f"{self.name}: check {check.name!r} failed")
