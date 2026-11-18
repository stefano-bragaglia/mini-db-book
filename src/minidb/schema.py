"""Declarative table definitions."""
from dataclasses import dataclass
from dataclasses import field
from functools import reduce
from typing import Mapping

from minidb import SchemaError
from minidb.normalizers import Normalizer
from minidb.types import Type

type Row = dict[str, object]


@dataclass(frozen=True)
class Column[T: Type]:
    name: str
    type: T
    normalizers: tuple[Normalizer, ...] = field(default_factory=tuple)

    def prepare(self, value: object) -> T:
        """Normalize, then validate one value. Raises DomainError."""
        value = self.type.normalize(value)
        if value is not None:
            value = reduce(lambda acc, fn: fn(acc), self.normalizers, value)
        self.type.validate(value)
        return value


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[Column, ...]
    by_name: Mapping[str, Column] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, 'columns', tuple(self.columns))
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
        row = dict(base) if base is not None else dict.fromkeys(self.column_names)
        for name, value in values.items():
            from minidb.errors import DomainError
            try:
                row[name] = self.by_name[name].prepare(value)
            except DomainError as e:
                raise DomainError(f"{self.name}.{name}: {e}") from None
        return row
