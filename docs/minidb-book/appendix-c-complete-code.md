[🏠 Contents](index.md) · [← Previous: Appendix B — Testing a Database](appendix-b-testing.md)

# Appendix C — The Complete Code

This is minidb as it stands at the end of the book: the package (6,242 lines in 19 modules), the example programs and the test suite, 7,176 lines in all, plus `pyproject.toml`. It is exactly the code the book's examples were run against, assembled chapter by chapter from the listings. It passes `ruff format --check`, `ruff check` and `pyrefly check` with the configuration below, and all of its doctests and tests pass on Python 3.14, both the regular and the free-threaded build. Nothing outside the standard library is needed to run it.

```text
minidb-project/
├── pyproject.toml
├── examples/
│   ├── __init__.py
│   ├── toy.py
│   ├── index_speed.py
│   ├── transfers.py
│   ├── starvation.py
│   ├── shared_reads.py
│   ├── counter.py
│   ├── crash_child.py
│   ├── crash_test.py
│   ├── planner_speed.py
│   ├── index_benchmark.py
│   ├── run_tests.py
├── src/
│   └── minidb/
│       ├── __init__.py
│       ├── errors.py
│       ├── values.py
│       ├── types.py
│       ├── normalizers.py
│       ├── schema.py
│       ├── index.py
│       ├── btree.py
│       ├── table.py
│       ├── changes.py
│       ├── operators.py
│       ├── expr.py
│       ├── query.py
│       ├── planner.py
│       ├── locks.py
│       ├── uow.py
│       ├── storage.py
│       ├── database.py
│       ├── sql.py
└── tests/
    ├── __init__.py
    └── test_minidb.py
```

The two package `__init__.py` files under `examples/` and `tests/` contain only a docstring: `"""Examples for the book."""` and `"""Tests for the book."""`.

| File | Contents | Main chapter | Lines |
|---|---|---|---|
| [`src/minidb/__init__.py`](#srcminidb__init__py) | Package exports | – | 89 |
| [`src/minidb/errors.py`](#srcminidberrorspy) | Exceptions | [Ch. 2](02-tables-and-crud.md) | 41 |
| [`src/minidb/values.py`](#srcminidbvaluespy) | Value types and typing helpers | [Ch. 3](03-types-and-normalization.md) | 52 |
| [`src/minidb/types.py`](#srcminidbtypespy) | Column types | [Ch. 3](03-types-and-normalization.md) | 351 |
| [`src/minidb/normalizers.py`](#srcminidbnormalizerspy) | Value normalizers | [Ch. 3](03-types-and-normalization.md) | 73 |
| [`src/minidb/schema.py`](#srcminidbschemapy) | Columns, checks, keys, foreign keys | [Ch. 4](04-constraints.md) | 281 |
| [`src/minidb/index.py`](#srcminidbindexpy) | Index protocols, hash and sorted indexes | [Ch. 5](05-keys-and-indexes.md) | 250 |
| [`src/minidb/btree.py`](#srcminidbbtreepy) | B+ tree and B-tree index | [Ch. 15](15-b-trees.md) | 263 |
| [`src/minidb/table.py`](#srcminidbtablepy) | Table storage | [Ch. 8](08-unit-of-work-i.md) | 283 |
| [`src/minidb/changes.py`](#srcminidbchangespy) | Planning and validating changes | [Ch. 8](08-unit-of-work-i.md) | 381 |
| [`src/minidb/operators.py`](#srcminidboperatorspy) | Query operators | [Ch. 7](07-query-primitives.md) | 528 |
| [`src/minidb/expr.py`](#srcminidbexprpy) | Expression trees | [Ch. 14](14-query-planning.md) | 480 |
| [`src/minidb/query.py`](#srcminidbquerypy) | The query builder | [Ch. 7](07-query-primitives.md) | 225 |
| [`src/minidb/planner.py`](#srcminidbplannerpy) | The cost-based planner | [Ch. 14](14-query-planning.md) | 451 |
| [`src/minidb/locks.py`](#srcminidblockspy) | Readers–writer locks | [Ch. 11](11-readers-writer-locks.md) | 220 |
| [`src/minidb/uow.py`](#srcminidbuowpy) | The Unit of Work | [Ch. 12](12-isolation.md) | 561 |
| [`src/minidb/storage.py`](#srcminidbstoragepy) | Formats, snapshot and write-ahead log | [Ch. 13](13-persistence.md) | 253 |
| [`src/minidb/database.py`](#srcminidbdatabasepy) | The Database façade | [Ch. 13](13-persistence.md) | 456 |
| [`src/minidb/sql.py`](#srcminidbsqlpy) | The SQL front end | [App. A](appendix-a-sql-parser.md) | 1004 |
| [`examples/toy.py`](#examplestoypy) | A toy relational algebra | [Ch. 1](01-relational-model.md) | 77 |
| [`examples/index_speed.py`](#examplesindex_speedpy) | Scan vs index lookup | [Ch. 5](05-keys-and-indexes.md) | 24 |
| [`examples/transfers.py`](#examplestransferspy) | Concurrent transfers | [Ch. 10](10-concurrency-i.md) | 81 |
| [`examples/starvation.py`](#examplesstarvationpy) | Starvation under three locks | [Ch. 11](11-readers-writer-locks.md) | 84 |
| [`examples/shared_reads.py`](#examplesshared_readspy) | Shared vs exclusive reads | [Ch. 11](11-readers-writer-locks.md) | 85 |
| [`examples/counter.py`](#examplescounterpy) | A contended counter | [Ch. 12](12-isolation.md) | 57 |
| [`examples/crash_child.py`](#examplescrash_childpy) | Transfers until killed | [Ch. 13](13-persistence.md) | 63 |
| [`examples/crash_test.py`](#examplescrash_testpy) | Kill, recover, check | [Ch. 13](13-persistence.md) | 40 |
| [`examples/planner_speed.py`](#examplesplanner_speedpy) | Naive vs planned join | [Ch. 14](14-query-planning.md) | 61 |
| [`examples/index_benchmark.py`](#examplesindex_benchmarkpy) | Index kinds compared | [Ch. 15](15-b-trees.md) | 51 |
| [`examples/run_tests.py`](#examplesrun_testspy) | Run the test suite | [App. B](appendix-b-testing.md) | 14 |
| [`tests/test_minidb.py`](#teststest_minidbpy) | The test suite | [App. B](appendix-b-testing.md) | 297 |

## `pyproject.toml`

The project file, with the ruff and pyrefly configuration from [§1.4](01-relational-model.md#14-how-to-read-the-code-in-this-book).

```toml
[project]
name = "minidb"
version = "1.0.0"
description = "A small relational database, built in the book"
requires-python = ">=3.14"

# ---------------------------------------------------------------------------
# Ruff — linter + formatter
# ---------------------------------------------------------------------------
[tool.ruff]
line-length = 120
target-version = "py314"
src = ["src"]
extend-exclude = [".idea"]

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D105",     # docstring in magic methods (dunders are not documented)
    "D107",     # docstring in __init__ (the class docstring covers it)
    "EM",       # exception message must not be a string literal
    "TRY003",   # long messages outside the exception class
    "CPY",      # copyright header
    "COM812",   # trailing comma (conflicts with the formatter)
    "T201",     # print
    "S101",     # assert
    "PLR2004",  # magic values in comparisons
    "PLR0913",  # too many arguments
    "E501",     # line too long (the formatter handles it)
]

[tool.ruff.lint.isort]
force-single-line = true

[tool.ruff.lint.pydocstyle]
convention = "pep257" # Standard reStructuredText-compatible docstring style

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D"]

[tool.ruff.lint.mccabe]
# Grade A complexity corresponds to a score of 1 to 5
max-complexity = 5

[tool.ruff.lint.pep8-naming]
# Qt virtual overrides are camelCase (mousePressEvent, sizeHint, ...)
extend-ignore-names = ["*Event", "sizeHint", "minimumSizeHint", "boundingRect", "paint", "itemChange", "shape"]

[tool.ruff.format]
docstring-code-format = true

# ---------------------------------------------------------------------------
# Pyrefly — type checker
# ---------------------------------------------------------------------------
[tool.pyrefly]
preset = "strict"           # ~ basedpyright typeCheckingMode = "all"
project-includes = ["src"]
python-version = "3.14"
search-path = ["src"]

[tool.pyrefly.errors]
unused-call-result = false  # ~ reportUnusedCallResult = false
```

## `src/minidb/__init__.py`

Package exports.

```python
"""Build a small relational database, one chapter at a time."""

from minidb import normalizers
from minidb.changes import Change
from minidb.database import Database
from minidb.errors import CheckError
from minidb.errors import ConflictError
from minidb.errors import ConstraintError
from minidb.errors import DatabaseError
from minidb.errors import DomainError
from minidb.errors import ForeignKeyError
from minidb.errors import NotNullError
from minidb.errors import SchemaError
from minidb.errors import UniqueError
from minidb.expr import Expr
from minidb.expr import col
from minidb.expr import lit
from minidb.locks import FairRWLock
from minidb.operators import Avg
from minidb.operators import Count
from minidb.operators import Max
from minidb.operators import Min
from minidb.operators import Sum
from minidb.query import Query
from minidb.schema import Check
from minidb.schema import Column
from minidb.schema import ForeignKey
from minidb.schema import TableSchema
from minidb.sql import Connection
from minidb.sql import SQLError
from minidb.sql import connect
from minidb.storage import Format
from minidb.storage import JsonFormat
from minidb.storage import Storage
from minidb.types import Boolean
from minidb.types import Date
from minidb.types import Integer
from minidb.types import Numeric
from minidb.types import Real
from minidb.types import Text
from minidb.types import Timestamp
from minidb.uow import Record
from minidb.uow import TransactionError
from minidb.uow import UnitOfWork

__all__ = [
    "Avg",
    "Boolean",
    "Change",
    "Check",
    "CheckError",
    "Column",
    "ConflictError",
    "Connection",
    "ConstraintError",
    "Count",
    "Database",
    "DatabaseError",
    "Date",
    "DomainError",
    "Expr",
    "FairRWLock",
    "ForeignKey",
    "ForeignKeyError",
    "Format",
    "Integer",
    "JsonFormat",
    "Max",
    "Min",
    "NotNullError",
    "Numeric",
    "Query",
    "Real",
    "Record",
    "SQLError",
    "SchemaError",
    "Storage",
    "Sum",
    "TableSchema",
    "Text",
    "Timestamp",
    "TransactionError",
    "UniqueError",
    "UnitOfWork",
    "col",
    "connect",
    "lit",
    "normalizers",
]
```

## `src/minidb/errors.py`

Exceptions. Developed in [Chapter 2](02-tables-and-crud.md).

```python
"""Define the exceptions that minidb raises on purpose."""


class DatabaseError(Exception):
    """Signal any error that minidb raises deliberately.

    Catching it catches everything the database rejected, but none of the
    application's own bugs.
    """


class SchemaError(DatabaseError):
    """Signal that a table or column doesn't exist, or a definition is invalid."""


class ConstraintError(DatabaseError):
    """Signal that data was rejected because it breaks a rule of the schema."""


class DomainError(ConstraintError):
    """Signal that a value doesn't belong to its column's type (domain)."""


class NotNullError(ConstraintError):
    """Signal that a NOT NULL column received NULL."""


class CheckError(ConstraintError):
    """Signal that a CHECK constraint evaluated to false."""


class UniqueError(ConstraintError):
    """Signal that a PRIMARY KEY or UNIQUE constraint would be violated."""


class ForeignKeyError(ConstraintError):
    """Signal a reference to a missing row, or a delete that would orphan rows."""


class ConflictError(DatabaseError):
    """Signal that a concurrent transaction changed something this one read; retry it."""
```

## `src/minidb/values.py`

Value types and typing helpers. Developed in [Chapter 3](03-types-and-normalization.md).

```python
"""Name the types of the values that tables hold."""

import datetime as dt
from decimal import Decimal
from typing import Protocol
from typing import Self
from typing import cast

type Value = bool | int | float | str | Decimal | dt.date | dt.datetime
type Row = dict[str, Value | None]


class Ordered(Protocol):
    """Describe values that can be ordered among themselves."""

    def __lt__(self, other: Self, /) -> bool: ...
    def __le__(self, other: Self, /) -> bool: ...
    def __gt__(self, other: Self, /) -> bool: ...
    def __ge__(self, other: Self, /) -> bool: ...


class Arithmetic(Protocol):
    """Describe values that support the four arithmetic operators among themselves."""

    def __add__(self, other: Self, /) -> Self: ...
    def __sub__(self, other: Self, /) -> Self: ...
    def __mul__(self, other: Self, /) -> Self: ...
    def __truediv__(self, other: Self, /) -> Self: ...


def ordered(value: Value | None) -> Ordered:
    """Return ``value``, typed as orderable.

    Values from one column share a Python type, so they can be compared;
    the type checker can't know that, and this function says so.

    :param value: a value from a column (or a constant of the column's type).
    :return: the same object.
    """
    return cast("Ordered", value)


def arithmetic(value: Value) -> Arithmetic:
    """Return ``value``, typed as supporting arithmetic; see :func:`ordered`.

    :param value: a numeric value.
    :return: the same object.
    """
    return cast("Arithmetic", value)


type Primitive = bool | int | float | str | list[Primitive] | dict[str, Primitive] | None
```

## `src/minidb/types.py`

Column types. Developed in [Chapter 3](03-types-and-normalization.md).

```python
"""Define column types: how each one normalizes and validates its values."""

import datetime as dt
import math
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN
from decimal import Decimal
from decimal import InvalidOperation
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import override

from minidb.errors import DomainError
from minidb.values import Value

if TYPE_CHECKING:
    from minidb.values import Primitive

_INT_RE = re.compile(r"[+-]?\d+")
_TRUE = frozenset({"true", "t", "yes", "y", "on", "1"})
_FALSE = frozenset({"false", "f", "no", "n", "off", "0"})


class Type[T: Value]:
    """Describe a column type: how to normalize its values, and which are valid.

    :meth:`normalize` turns an acceptable input into the one canonical value
    that is stored; :meth:`validate` checks that a value already is canonical
    and inside the type's domain. NULL (``None``) passes through both
    untouched: whether a column may hold NULL is a constraint, not a type.

    Subclasses set :attr:`exact_types`, override :meth:`coerce`, and extend
    :meth:`validate` with rules such as ranges and lengths.
    """

    exact_types: ClassVar[tuple[type, ...]] = ()

    def normalize(self, value: object) -> T | None:
        """Convert ``value`` to this type's canonical form.

        :param value: any input; ``None`` is returned unchanged.
        :return: the canonical value, or ``None``.
        :raises DomainError: if ``value`` can't be converted.
        """
        return None if value is None else self.coerce(value)

    def coerce(self, value: object) -> T:
        """Convert a non-NULL ``value``; subclasses override this.

        :param value: the input, never ``None``.
        :return: the canonical value.
        :raises DomainError: always, in the base class.
        """
        raise self.error(value)

    def validate(self, value: object) -> None:
        """Check that ``value`` is canonical and inside the domain.

        The check is on the *exact* Python type: ``bool`` is a subclass of
        ``int``, but ``True`` is not a valid integer.

        :param value: the value to check; ``None`` always passes.
        :raises DomainError: if the value is not valid.
        """
        if value is not None and type(value) not in self.exact_types:
            raise self.error(value)

    def error(self, value: object, reason: str = "") -> DomainError:
        """Build the error that rejects ``value``.

        :param value: the rejected value.
        :param reason: why it was rejected; empty by default.
        :return: an exception for the caller to raise.
        """
        return DomainError(f"{value!r} is not a valid {self!r}" + (f": {reason}" if reason else ""))

    def to_primitive(self, value: Value | None) -> Primitive:
        """Convert a canonical value into something any :class:`Format` can store.

        :param value: a value of this type, or ``None``.
        :return: the value itself, in the base class.
        """
        return value if not isinstance(value, Decimal | dt.date) else str(value)

    def from_primitive(self, value: Primitive) -> T | None:
        """Convert a stored primitive back into a canonical value, and validate it.

        :param value: what :meth:`to_primitive` produced.
        :return: the canonical value, or ``None``.
        :raises DomainError: if the stored value is not valid for this type.
        """
        result = self.normalize(value)
        self.validate(result)
        return result


def _integral(value: object) -> int | None:
    """Return ``value`` as an int if it is a whole float or Decimal, or a numeric string."""
    match value:
        case float() if value.is_integer():
            return int(value)
        case Decimal() if value.is_finite() and value == value.to_integral_value():
            return int(value)
        case str() if _INT_RE.fullmatch(value.strip()):
            return int(value.strip())
        case _:
            return None


@dataclass(frozen=True)
class Integer(Type[int]):
    """Hold whole numbers, optionally between ``min`` and ``max``.

    >>> Integer(min=0).normalize(" 42 ")
    42

    :param min: the smallest valid value; ``None`` (the default) for no limit.
    :param max: the largest valid value; ``None`` (the default) for no limit.
    """

    min: int | None = None
    max: int | None = None
    exact_types: ClassVar[tuple[type, ...]] = (int,)

    @override
    def coerce(self, value: object) -> int:
        if isinstance(value, bool):
            raise self.error(value, "booleans are not integers")
        if isinstance(value, int):
            return value
        number = _integral(value)
        if number is None:
            raise self.error(value)
        return number

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, int):
            if self.min is not None and value < self.min:
                raise self.error(value, f"below minimum {self.min}")
            if self.max is not None and value > self.max:
                raise self.error(value, f"above maximum {self.max}")


@dataclass(frozen=True)
class Real(Type[float]):
    """Hold finite floating-point numbers; NaN and infinities are rejected.

    >>> Real().normalize("2.5")
    2.5
    """

    exact_types: ClassVar[tuple[type, ...]] = (float,)

    @override
    def coerce(self, value: object) -> float:
        if isinstance(value, bool):
            raise self.error(value, "booleans are not numbers")
        if isinstance(value, int | float | Decimal):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                raise self.error(value) from None
        raise self.error(value)

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, float) and not math.isfinite(value):
            raise self.error(value, "NaN and infinities are not allowed")


@dataclass(frozen=True)
class Text(Type[str]):
    """Hold strings, optionally no longer than ``max_length`` characters.

    >>> Text().normalize(42)
    Traceback (most recent call last):
      ...
    minidb.errors.DomainError: 42 is not a valid Text(max_length=None): no implicit conversion to text

    :param max_length: the longest valid string; ``None`` (the default) for no limit.
    """

    max_length: int | None = None
    exact_types: ClassVar[tuple[type, ...]] = (str,)

    @override
    def coerce(self, value: object) -> str:
        if not isinstance(value, str):
            raise self.error(value, "no implicit conversion to text")
        return value

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, str) and self.max_length is not None and len(value) > self.max_length:
            raise self.error(value, f"longer than {self.max_length} characters")


@dataclass(frozen=True)
class Boolean(Type[bool]):
    """Hold ``True`` or ``False``, accepting 0/1 and words such as "yes" and "off".

    >>> Boolean().normalize("Yes"), Boolean().normalize(0)
    (True, False)
    """

    exact_types: ClassVar[tuple[type, ...]] = (bool,)

    @override
    def coerce(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value in (0, 1):
            return value == 1
        word = value.strip().lower() if isinstance(value, str) else None
        if word in _TRUE or word in _FALSE:
            return word in _TRUE
        raise self.error(value)


def _to_decimal(value: object) -> Decimal | None:
    """Return ``value`` as a Decimal, or ``None`` if it isn't a number."""
    if isinstance(value, float):
        return Decimal(repr(value))  # 0.1 -> Decimal('0.1'), not its binary value
    if isinstance(value, int | Decimal) and not isinstance(value, bool):
        return Decimal(value)
    if isinstance(value, str):
        try:
            return Decimal(value.strip())
        except InvalidOperation:
            return None
    return None


@dataclass(frozen=True)
class Numeric(Type[Decimal]):
    """Hold exact decimals with ``precision`` digits, ``scale`` of them after the point.

    Values are rounded to ``scale`` places with banker's rounding.

    >>> Numeric(6, 2).normalize(0.1)
    Decimal('0.10')

    :param precision: the total number of digits; 18 by default.
    :param scale: the digits after the decimal point; 2 by default.
    :raises ValueError: unless ``0 <= scale <= precision``.
    """

    precision: int = 18
    scale: int = 2
    exact_types: ClassVar[tuple[type, ...]] = (Decimal,)

    def __post_init__(self) -> None:
        if not 0 <= self.scale <= self.precision:
            raise ValueError("need 0 <= scale <= precision")

    @override
    def coerce(self, value: object) -> Decimal:
        number = _to_decimal(value)
        if number is None:
            raise self.error(value)
        if not number.is_finite():
            raise self.error(value, "NaN and infinities are not allowed")
        return number.quantize(Decimal(1).scaleb(-self.scale), ROUND_HALF_EVEN)

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if not isinstance(value, Decimal):
            return
        if value.as_tuple().exponent != -self.scale:
            raise self.error(value, f"expected exactly {self.scale} decimal places")
        if max(value.adjusted() + 1, 0) > self.precision - self.scale:
            raise self.error(value, f"too many digits for NUMERIC({self.precision}, {self.scale})")


@dataclass(frozen=True)
class Date(Type[dt.date]):
    """Hold calendar dates, accepting ISO strings such as ``"2026-11-18"``.

    >>> Date().normalize("2026-11-18")
    datetime.date(2026, 11, 18)
    """

    exact_types: ClassVar[tuple[type, ...]] = (dt.date,)

    @override
    def coerce(self, value: object) -> dt.date:
        if isinstance(value, dt.datetime):
            raise self.error(value, "use .date() to drop the time explicitly")
        if isinstance(value, dt.date):
            return value
        if isinstance(value, str):
            try:
                return dt.date.fromisoformat(value.strip())
            except ValueError:
                raise self.error(value) from None
        raise self.error(value)


@dataclass(frozen=True)
class Timestamp(Type[dt.datetime]):
    """Hold points in time: all timezone-aware (stored in UTC), or all naive.

    Python refuses to compare aware and naive datetimes, so a column must
    pick one kind.

    >>> Timestamp().normalize("2026-11-18T10:00:00+01:00")
    datetime.datetime(2026, 11, 18, 9, 0, tzinfo=datetime.timezone.utc)

    :param with_timezone: whether values must be aware; ``True`` by default.
    """

    with_timezone: bool = True
    exact_types: ClassVar[tuple[type, ...]] = (dt.datetime,)

    @override
    def coerce(self, value: object) -> dt.datetime:
        stamp = self._parse(value)
        aware = stamp.utcoffset() is not None
        if self.with_timezone and not aware:
            raise self.error(value, "a timezone is required")
        if not self.with_timezone and aware:
            raise self.error(value, "timezone not allowed")
        return stamp.astimezone(dt.UTC) if aware else stamp

    def _parse(self, value: object) -> dt.datetime:
        if isinstance(value, dt.datetime):
            return value
        if isinstance(value, str):
            try:
                return dt.datetime.fromisoformat(value.strip())
            except ValueError:
                raise self.error(value) from None
        raise self.error(value)

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, dt.datetime) and self.with_timezone and value.utcoffset() != dt.timedelta(0):
            raise self.error(value, "must be stored in UTC")

    @override
    def to_primitive(self, value: Value | None) -> Primitive:
        return value.isoformat() if isinstance(value, dt.datetime) else None
```

## `src/minidb/normalizers.py`

Value normalizers. Developed in [Chapter 3](03-types-and-normalization.md).

```python
"""Provide small value normalizers for ``Column(normalizers=...)``.

Every normalizer must be idempotent, ``f(f(x)) == f(x)``: rows are
re-normalized whenever they are updated, so a normalizer that isn't would
change data nobody touched. Normalizers leave non-text values alone, so any
of them can be put on any column.
"""

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from minidb.values import Value


def strip(value: Value) -> Value:
    """Remove leading and trailing whitespace from text.

    >>> strip("  Ada ")
    'Ada'

    :param value: the value to normalize.
    :return: the stripped text, or ``value`` unchanged if it isn't text.
    """
    return value.strip() if isinstance(value, str) else value


def lower(value: Value) -> Value:
    """Lower-case text.

    >>> lower("Ada@Example.ORG")
    'ada@example.org'

    :param value: the value to normalize.
    :return: the lower-cased text, or ``value`` unchanged if it isn't text.
    """
    return value.lower() if isinstance(value, str) else value


def upper(value: Value) -> Value:
    """Upper-case text.

    :param value: the value to normalize.
    :return: the upper-cased text, or ``value`` unchanged if it isn't text.
    """
    return value.upper() if isinstance(value, str) else value


def collapse_spaces(value: Value) -> Value:
    """Trim text and replace each run of whitespace with a single space.

    >>> collapse_spaces("  Ada   Lovelace ")
    'Ada Lovelace'

    :param value: the value to normalize.
    :return: the collapsed text, or ``value`` unchanged if it isn't text.
    """
    return " ".join(value.split()) if isinstance(value, str) else value


def nfc(value: Value) -> Value:
    """Convert text to Unicode normalization form NFC.

    Visually identical strings can be different sequences of code points;
    NFC picks one canonical sequence for each.

    >>> nfc("café") == "café"
    True

    :param value: the value to normalize.
    :return: the NFC form of the text, or ``value`` unchanged if it isn't text.
    """
    return unicodedata.normalize("NFC", value) if isinstance(value, str) else value
```

## `src/minidb/schema.py`

Columns, checks, keys, foreign keys. Developed in [Chapter 4](04-constraints.md).

```python
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


def as_key(columns: str | Iterable[str]) -> tuple[str, ...]:
    """Turn one column name or several into a tuple of names.

    >>> as_key("id"), as_key(["a", "b"])
    (('id',), ('a', 'b'))

    :param columns: a column name, or an iterable of them.
    :return: the names as a tuple.
    """
    return (columns,) if isinstance(columns, str) else tuple(columns)


type RowCheck = Callable[[Mapping[str, Value | None]], object]


type OnDelete = Literal["restrict", "cascade", "set null"]
ON_DELETE_ACTIONS: tuple[OnDelete, ...] = ("restrict", "cascade", "set null")


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

    def child_key(self, parent_row: Mapping[str, Value | None]) -> dict[str, Value | None]:
        """Return ``{column: value}`` that the children of ``parent_row`` have.

        :param parent_row: a row of the parent table.
        :return: the key to look up in the child table.
        """
        return {c: parent_row[r] for c, r in zip(self.columns, self.ref_columns, strict=True)}
```

## `src/minidb/index.py`

Index protocols, hash and sorted indexes. Developed in [Chapter 5](05-keys-and-indexes.md).

```python
"""Define indexes: secondary structures that map column values to rowids."""

import bisect
import itertools
import math
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Protocol
from typing import runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping

    from minidb.values import Value

type Key = tuple[Value | None, ...]


class Index(Protocol):
    """Describe what every kind of index offers.

    An index maps the *key* of a row, the tuple of its values in the
    indexed columns, to the set of rowids having that key. Rows whose key
    contains NULL are not indexed, because NULL never equals anything.
    """

    kind: ClassVar[str]
    name: str
    columns: tuple[str, ...]
    unique: bool

    def key_of(self, row: Mapping[str, Value | None]) -> Key | None:
        """Return the row's key, or ``None`` if any of its values is NULL."""
        ...

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``."""
        ...

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``."""
        ...

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``, as a new set."""
        ...

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        ...


class KeyedIndex:
    """Provide the attributes and the :meth:`key_of` that all indexes share.

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    """

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool = False) -> None:
        self.name = name
        self.columns = tuple(columns)
        self.unique = unique

    def key_of(self, row: Mapping[str, Value | None]) -> Key | None:
        """Return the row's values in the indexed columns, or ``None`` if one is NULL.

        >>> KeyedIndex("i", ["a", "b"]).key_of({"a": 1, "b": None, "c": 3}) is None
        True

        :param row: a row with (at least) the indexed columns.
        :return: the key tuple, or ``None``.
        """
        key = tuple(row[c] for c in self.columns)
        return None if any(v is None for v in key) else key


class HashIndex(KeyedIndex):
    """Answer equality lookups in O(1) with a dict from key to rowids.

    >>> index = HashIndex("by_city", ["city"])
    >>> index.add(1, {"city": "London"})
    >>> index.add(4, {"city": "London"})
    >>> index.lookup(("London",))
    {1, 4}

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    """

    kind: ClassVar[str] = "hash"

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool = False) -> None:
        super().__init__(name, columns, unique=unique)
        self._entries: dict[Key, set[int]] = {}

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the row's values.
        """
        key = self.key_of(row)
        if key is not None:
            self._entries.setdefault(key, set()).add(rowid)

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``, dropping keys left with no rows.

        :param rowid: the row's rowid.
        :param row: the values the row had when it was added.
        """
        key = self.key_of(row)
        ids = self._entries.get(key) if key is not None else None
        if key is not None and ids is not None:
            ids.discard(rowid)
            if not ids:
                del self._entries[key]  # don't keep empty buckets around

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``.

        :param key: the key to look up.
        :return: a new set, which the caller may modify.
        """
        return set(self._entries.get(tuple(key), ()))

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        return len(self._entries)

    def __repr__(self) -> str:
        u = "unique " if self.unique else ""
        return f"<{u}{self.kind} index {self.name} on {self.columns}>"


@runtime_checkable
class OrderedIndex(Index, Protocol):
    """Describe an index that also answers range queries, in key order."""

    def range(
        self, lo: Key | None, hi: Key | None, *, lo_inclusive: bool = True, hi_inclusive: bool = True
    ) -> list[int]:
        """Return the rowids with ``lo <= key <= hi``, in key order; ``None`` bounds are open."""
        ...


class IndexFactory(Protocol):
    """Describe what makes an index: any index class's constructor fits."""

    def __call__(self, name: str, columns: Iterable[str], *, unique: bool = False) -> Index:
        """Create an empty index."""
        ...


class SortedIndex(KeyedIndex):
    """Keep ``(key, rowid)`` pairs in a sorted list: lookups and ranges by binary search.

    Inserting shifts the list, so it costs O(n); Chapter 15 fixes that.

    >>> index = SortedIndex("by_age", ["age"])
    >>> for rowid, age in [(1, 41), (2, 36), (3, 85)]:
    ...     index.add(rowid, {"age": age})
    >>> index.range((40,), None)
    [1, 3]

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    """

    kind: ClassVar[str] = "sorted"

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool = False) -> None:
        super().__init__(name, columns, unique=unique)
        self._sorted: list[tuple[Key, int]] = []

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the row's values.
        """
        key = self.key_of(row)
        if key is not None:
            bisect.insort(self._sorted, (key, rowid))  # O(n): the list shifts

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the values the row had when it was added.
        """
        key = self.key_of(row)
        if key is None:
            return
        i = bisect.bisect_left(self._sorted, (key, rowid))
        if i < len(self._sorted) and self._sorted[i] == (key, rowid):
            del self._sorted[i]

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``.

        :param key: the key to look up.
        :return: a new set.
        """
        key = tuple(key)
        i = bisect.bisect_left(self._sorted, (key,))  # (key,) sorts before (key, any rowid)
        found: set[int] = set()
        while i < len(self._sorted) and self._sorted[i][0] == key:
            found.add(self._sorted[i][1])
            i += 1
        return found

    def range(
        self, lo: Key | None, hi: Key | None, *, lo_inclusive: bool = True, hi_inclusive: bool = True
    ) -> list[int]:
        """Return the rowids with ``lo <= key <= hi``, in key order.

        :param lo: the lower bound, or ``None`` for none.
        :param hi: the upper bound, or ``None`` for none.
        :param lo_inclusive: whether ``lo`` itself matches; ``True`` by default.
        :param hi_inclusive: whether ``hi`` itself matches; ``True`` by default.
        :return: the matching rowids.
        """
        i = self._start(lo, lo_inclusive=lo_inclusive)
        found: list[int] = []
        while i < len(self._sorted) and not _beyond(self._sorted[i][0], hi, hi_inclusive=hi_inclusive):
            found.append(self._sorted[i][1])
            i += 1
        return found

    def _start(self, lo: Key | None, *, lo_inclusive: bool) -> int:
        if lo is None:
            return 0
        if lo_inclusive:
            return bisect.bisect_left(self._sorted, (lo,))
        return bisect.bisect_right(self._sorted, (lo, math.inf))  # after every (lo, rowid)

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        return sum(1 for _ in itertools.groupby(self._sorted, key=lambda e: e[0]))


def _beyond(key: Key, hi: Key | None, *, hi_inclusive: bool) -> bool:
    """Tell whether ``key`` lies past the upper bound ``hi``."""
    return hi is not None and (key > hi or (key == hi and not hi_inclusive))
```

## `src/minidb/btree.py`

B+ tree and B-tree index. Developed in [Chapter 15](15-b-trees.md).

```python
"""Implement an in-memory B+ tree, and an ordered index built on it.

Internal nodes hold separator keys and children. Leaves hold the keys, each
with its set of values, and a link to the next leaf, so a range scan walks
the leaf level without climbing back up the tree.
"""

import bisect
from typing import TYPE_CHECKING
from typing import ClassVar

from minidb.index import KeyedIndex

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Iterator
    from collections.abc import Mapping

    from minidb.index import Key
    from minidb.values import Ordered
    from minidb.values import Value


class _Leaf[K: Ordered, V]:
    __slots__ = ("keys", "next", "values")

    def __init__(self) -> None:
        self.keys: list[K] = []
        self.values: list[set[V]] = []
        self.next: _Leaf[K, V] | None = None


class _Internal[K: Ordered, V]:
    __slots__ = ("children", "keys")

    def __init__(self, keys: list[K], children: list[_Node[K, V]]) -> None:
        self.keys = keys  # keys[i] is the smallest key under children[i + 1]
        self.children = children  # always len(keys) + 1 of them


type _Node[K: Ordered, V] = _Leaf[K, V] | _Internal[K, V]


class BPlusTree[K: Ordered, V]:
    """Map ordered keys to sets of values, with O(log n) inserts, lookups and range starts.

    ``K`` is the key type, which must be orderable; ``V`` the type of the
    values stored under each key.

    >>> tree = BPlusTree[int, str](order=4)
    >>> for k in [30, 10, 20]:
    ...     tree.insert(k, f"v{k}")
    >>> tree.get(20), [k for k, _ in tree.items(lo=15)]
    ({'v20'}, [20, 30])

    :param order: the maximum number of children per node; 64 by default.
    :raises ValueError: if ``order`` is below 3.
    """

    def __init__(self, order: int = 64) -> None:
        if order < 3:
            raise ValueError("order must be at least 3")
        self.order = order
        self.root: _Node[K, V] = _Leaf[K, V]()
        self._len = 0

    def __len__(self) -> int:
        return self._len

    @property
    def height(self) -> int:
        """Return the number of levels, counting the leaves."""
        node, h = self.root, 1
        while isinstance(node, _Internal):
            node, h = node.children[0], h + 1
        return h

    # -- search ---------------------------------------------------------------------------
    def _descend(self, key: K) -> tuple[_Leaf[K, V], list[_Internal[K, V]]]:
        """Return the leaf where ``key`` belongs, and the internal nodes on the way."""
        node, path = self.root, list[_Internal[K, V]]()
        while isinstance(node, _Internal):
            path.append(node)
            node = node.children[bisect.bisect_right(node.keys, key)]
        return node, path

    def _first_leaf(self) -> _Leaf[K, V]:
        node = self.root
        while isinstance(node, _Internal):
            node = node.children[0]
        return node

    def get(self, key: K) -> set[V]:
        """Return the values stored under ``key``.

        :param key: the key.
        :return: a new set; empty if the key is absent.
        """
        leaf, _ = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            return set(leaf.values[i])
        return set()

    def items(
        self, lo: K | None = None, hi: K | None = None, *, lo_inclusive: bool = True, hi_inclusive: bool = True
    ) -> Iterator[tuple[K, set[V]]]:
        """Yield ``(key, values)`` for the keys between ``lo`` and ``hi``, in order.

        :param lo: the lower bound; ``None`` (the default) for none.
        :param hi: the upper bound; ``None`` (the default) for none.
        :param lo_inclusive: whether ``lo`` itself is included; ``True`` by default.
        :param hi_inclusive: whether ``hi`` itself is included; ``True`` by default.
        :return: an iterator walking the leaves.
        """
        leaf: _Leaf[K, V] | None
        if lo is None:
            leaf, i = self._first_leaf(), 0
        else:
            leaf, _ = self._descend(lo)
            i = (bisect.bisect_left if lo_inclusive else bisect.bisect_right)(leaf.keys, lo)
        while leaf is not None:
            for key, values in zip(leaf.keys[i:], leaf.values[i:], strict=True):
                if hi is not None and (key > hi or (key == hi and not hi_inclusive)):
                    return
                yield key, values
            leaf, i = leaf.next, 0

    # -- insert ---------------------------------------------------------------------------
    def insert(self, key: K, value: V) -> None:
        """Store ``value`` under ``key``, splitting nodes that overflow.

        :param key: the key.
        :param value: the value to add to the key's set.
        """
        leaf, path = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            leaf.values[i].add(value)
            return
        leaf.keys.insert(i, key)
        leaf.values.insert(i, {value})
        self._len += 1
        if len(leaf.keys) >= self.order:
            self._split_leaf(leaf, path)

    def _split_leaf(self, leaf: _Leaf[K, V], path: list[_Internal[K, V]]) -> None:
        mid = len(leaf.keys) // 2
        right = _Leaf[K, V]()
        right.keys, leaf.keys = leaf.keys[mid:], leaf.keys[:mid]
        right.values, leaf.values = leaf.values[mid:], leaf.values[:mid]
        right.next, leaf.next = leaf.next, right
        self._insert_in_parent(leaf, right.keys[0], right, path)

    def _insert_in_parent(
        self, left: _Node[K, V], separator: K, right: _Node[K, V], path: list[_Internal[K, V]]
    ) -> None:
        if not path:  # the root split: the tree grows a level
            self.root = _Internal[K, V]([separator], [left, right])
            return
        parent = path.pop()
        i = next(j for j, child in enumerate(parent.children) if child is left)
        parent.keys.insert(i, separator)
        parent.children.insert(i + 1, right)
        if len(parent.children) > self.order:
            mid = len(parent.keys) // 2
            up = parent.keys[mid]
            sibling = _Internal[K, V](parent.keys[mid + 1 :], parent.children[mid + 1 :])
            parent.keys, parent.children = parent.keys[:mid], parent.children[: mid + 1]
            self._insert_in_parent(parent, up, sibling, path)

    # -- delete ---------------------------------------------------------------------------
    def remove(self, key: K, value: V) -> None:
        """Remove ``value`` from ``key``, dropping the key when its set is empty.

        Nodes are never merged ("lazy deletion"): simple, and fine for
        workloads that insert more than they delete.

        :param key: the key.
        :param value: the value to remove; nothing happens if it is absent.
        """
        leaf, _ = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            leaf.values[i].discard(value)
            if not leaf.values[i]:
                del leaf.keys[i], leaf.values[i]
                self._len -= 1

    # -- for teaching ----------------------------------------------------------------------
    def dump(self) -> str:
        """Draw the tree's keys, one line per level.

        :return: the drawing.
        """
        lines: list[str] = []
        level: list[_Node[K, V]] = [self.root]
        while level:
            lines.append("   ".join("[" + " ".join(map(str, n.keys)) + "]" for n in level))
            level = [c for n in level if isinstance(n, _Internal) for c in n.children]
        return "\n".join(lines)


class BTreeIndex(KeyedIndex):
    """Answer lookups and ranges with a B+ tree: O(log n) for inserts too.

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    :param order: the tree's maximum fan-out; 64 by default.
    """

    kind: ClassVar[str] = "btree"

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool = False, order: int = 64) -> None:
        super().__init__(name, columns, unique=unique)
        self.tree: BPlusTree[Key, int] = BPlusTree(order)

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the row's values.
        """
        key = self.key_of(row)
        if key is not None:
            self.tree.insert(key, rowid)

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the values the row had when it was added.
        """
        key = self.key_of(row)
        if key is not None:
            self.tree.remove(key, rowid)

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``.

        :param key: the key to look up.
        :return: a new set.
        """
        return self.tree.get(tuple(key))

    def range(
        self, lo: Key | None, hi: Key | None, *, lo_inclusive: bool = True, hi_inclusive: bool = True
    ) -> list[int]:
        """Return the rowids with ``lo <= key <= hi``, in key order.

        :param lo: the lower bound, or ``None`` for none.
        :param hi: the upper bound, or ``None`` for none.
        :param lo_inclusive: whether ``lo`` itself matches; ``True`` by default.
        :param hi_inclusive: whether ``hi`` itself matches; ``True`` by default.
        :return: the matching rowids.
        """
        items = self.tree.items(lo, hi, lo_inclusive=lo_inclusive, hi_inclusive=hi_inclusive)
        return [rowid for _, rowids in items for rowid in sorted(rowids)]

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        return len(self.tree)
```

## `src/minidb/table.py`

Table storage. Developed in [Chapter 8](08-unit-of-work-i.md).

```python
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

    def _fill(self, index: Index) -> None:
        """Add every existing row to a new index, refusing duplicates if it is unique."""
        for rowid, row in self.rows.items():
            key = index.key_of(row)
            if index.unique and key is not None and index.lookup(key):
                raise UniqueError(f"{self.name}: cannot create unique index {index.name!r}: duplicate key {key}")
            index.add(rowid, row)

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

    def committed(self) -> Table:
        """Return the table itself: a table is its own committed state.

        :return: ``self``.
        """
        return self

    def index_on(self, columns: Iterable[str]) -> Index | None:
        """Return an index on exactly these columns, in any order, or ``None``.

        :param columns: the columns the index must cover.
        :return: such an index, or ``None``.
        """
        wanted = set(columns)
        return next((i for i in self.indexes.values() if set(i.columns) == wanted), None)

    def unique_keys(self) -> list[tuple[str, ...]]:
        """Return the column tuples of every unique index.

        :return: one tuple of column names per unique index.
        """
        return [i.columns for i in self.indexes.values() if i.unique]

    # -- primitives: no validation ---------------------------------------------------
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

        Planning happens outside the exclusive lock, so the counter has a
        small latch of its own.

        :return: a rowid no row has ever had.
        """
        with self._rowid_latch:
            rowid = self._next_rowid
            self._next_rowid += 1
            return rowid

    # -- reads -------------------------------------------------------------------------
    def row(self, rowid: int) -> Row:
        """Return the stored row itself; callers must never mutate it.

        :param rowid: the row to fetch.
        :return: the stored row.
        :raises KeyError: if there is no such row.
        """
        return self.rows[rowid]

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

    def select(self, where: Where = None) -> list[Row]:
        """Return copies of the rows matching ``where``; see :meth:`match`.

        :param where: which rows to return; ``None`` (the default) for all.
        :return: the matching rows.
        """
        return [dict(self.rows[rid]) for rid in self.match(where)]

    @property
    def next_rowid(self) -> int:
        """Return the rowid the next insert will get."""
        return self._next_rowid

    def reserve_rowid(self, rowid: int) -> None:
        """Make sure the counter never hands out ``rowid``, or anything below it.

        :param rowid: a rowid that is in use.
        """
        with self._rowid_latch:
            self._next_rowid = max(self._next_rowid, rowid + 1)


INDEX_KINDS: dict[str, IndexFactory] = {"hash": HashIndex, "sorted": SortedIndex}


INDEX_KINDS["btree"] = BTreeIndex
```

## `src/minidb/changes.py`

Planning and validating changes. Developed in [Chapter 8](08-unit-of-work-i.md).

```python
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
```

## `src/minidb/operators.py`

Query operators. Developed in [Chapter 7](07-query-primitives.md).

```python
"""Implement query operators in the iterator (Volcano) model.

Every operator is iterable: it yields :class:`Row` objects, which it gets by
iterating over its child operators. A query is a tree of operators, and
iterating over the root makes rows flow up from the leaves.
"""

import itertools
from typing import TYPE_CHECKING
from typing import Literal
from typing import Protocol
from typing import cast
from typing import override

from minidb.values import arithmetic
from minidb.values import ordered

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Mapping

    from minidb.schema import TableSchema
    from minidb.table import Table
    from minidb.values import Ordered
    from minidb.values import Row as StoredRow
    from minidb.values import Value


class Row(dict[str, "Value | None"]):
    """Hold a result row, keyed by qualified names such as ``"u.age"``.

    An unqualified name such as ``"age"`` also works when exactly one
    column has it.

    >>> row = Row({"u.id": 1, "o.id": 10, "o.total": 25})
    >>> row["total"]
    25
    >>> row["id"]
    Traceback (most recent call last):
      ...
    KeyError: "ambiguous column 'id': one of ['o.id', 'u.id']"
    """

    def __missing__(self, key: str) -> Value | None:
        if "." not in key:
            found = [k for k in self if k.rpartition(".")[2] == key]
            if len(found) == 1:
                return self[found[0]]
            if found:
                raise KeyError(f"ambiguous column {key!r}: one of {sorted(found)}")
        raise KeyError(key)


class Source(Protocol):
    """Describe something a :class:`Scan` can read: a table, or a view of one."""

    name: str
    columns: tuple[str, ...]

    def scan(self) -> Iterator[tuple[int, StoredRow]]:
        """Yield every ``(rowid, row)`` pair."""
        ...


type RowPredicate = Callable[[Row], object]
type RowFunction = Callable[[Row], Value | None]
type SortKey = tuple[str | RowFunction, bool]


class Operator:
    """Produce rows when iterated; the base class of every operator.

    Subclasses implement :meth:`__iter__`, :meth:`columns` and :attr:`label`.
    The planner sets :attr:`estimate`, the number of rows it expects.
    """

    children: tuple[Operator, ...] = ()
    estimate: float | None = None

    def __iter__(self) -> Iterator[Row]:
        raise NotImplementedError

    def columns(self) -> list[str]:
        """Return the names of the columns this operator produces.

        :return: the names, by default those of the first child.
        """
        return self.children[0].columns()

    @property
    def label(self) -> str:
        """Return a one-line description, used by :meth:`explain`."""
        return type(self).__name__

    def explain(self, indent: int = 0) -> str:
        """Describe the operator tree rooted here, one operator per line, with estimates.

        :param indent: the nesting depth of this operator; 0 by default.
        :return: the indented description.
        """
        line = "  " * indent + self.label
        if self.estimate is not None:
            line += f"  [~{self.estimate:,.0f} rows]"
        return "\n".join([line] + [child.explain(indent + 1) for child in self.children])


class Scan(Operator):
    """Yield every row of a source, with names qualified by ``alias``.

    :param source: the table (or view) to read.
    :param alias: the qualifier for column names; ``None`` (the default)
        uses the source's name.
    """

    def __init__(self, source: Source, alias: str | None = None) -> None:
        self.source = source
        self.alias = alias or source.name

    @override
    def __iter__(self) -> Iterator[Row]:
        names = [(c, f"{self.alias}.{c}") for c in self.source.columns]
        for _, row in self.source.scan():
            yield Row({q: row[c] for c, q in names})

    @override
    def columns(self) -> list[str]:
        return [f"{self.alias}.{c}" for c in self.source.columns]

    @property
    @override
    def label(self) -> str:
        return f"Scan {self.source.name} AS {self.alias}"


class Filter(Operator):
    """Keep the rows for which ``predicate`` is exactly ``True`` (WHERE semantics).

    :param child: the input.
    :param predicate: a function of the row; ``False`` and ``None``
        (UNKNOWN) both drop the row.
    """

    def __init__(self, child: Operator, predicate: RowPredicate) -> None:
        self.children = (child,)
        self.predicate = predicate

    @override
    def __iter__(self) -> Iterator[Row]:
        return (row for row in self.children[0] if self.predicate(row) is True)

    @property
    @override
    def label(self) -> str:
        return f"Filter {getattr(self.predicate, '__name__', self.predicate)}"


class Project(Operator):
    """Compute output columns, each from a column name or a function of the row.

    :param child: the input.
    :param outputs: ``{output name: source column or function}``.
    """

    def __init__(self, child: Operator, outputs: dict[str, str | RowFunction]) -> None:
        self.children = (child,)
        self.outputs = outputs

    @override
    def __iter__(self) -> Iterator[Row]:
        getters = [(name, _getter(src)) for name, src in self.outputs.items()]
        for row in self.children[0]:
            yield Row({name: get(row) for name, get in getters})

    @override
    def columns(self) -> list[str]:
        return list(self.outputs)

    @property
    @override
    def label(self) -> str:
        return f"Project {', '.join(self.outputs)}"


def _getter(source: str | RowFunction) -> RowFunction:
    """Turn a column name into a function that reads it; leave functions alone."""
    if callable(source):
        return source
    return lambda row: row[source]


class NestedLoopJoin(Operator):
    """Join every pair of rows for which ``on`` is true.

    The right input is read once into a list: an operator may not be safely
    iterable twice, or may be expensive to re-run.

    :param left: the outer input.
    :param right: the inner input.
    :param on: the join condition; ``None`` (the default) joins every pair.
    :param kind: ``"inner"`` (the default), or ``"left"`` to keep unmatched
        left rows, padded with NULLs.
    :raises ValueError: for any other ``kind``.
    """

    def __init__(
        self, left: Operator, right: Operator, on: RowPredicate | None = None, kind: JoinKind = "inner"
    ) -> None:
        if kind not in ("inner", "left"):
            raise ValueError("kind must be 'inner' or 'left'")
        self.children = (left, right)
        self.on, self.kind = on, kind

    @override
    def __iter__(self) -> Iterator[Row]:
        left, right = self.children
        inner = list(right)  # materialize once: blocking
        nulls = dict.fromkeys(right.columns())
        for lrow in left:
            matches = [row for r in inner if self._matches(row := Row(lrow | r))]
            yield from matches
            if not matches and self.kind == "left":
                yield Row(lrow | nulls)

    def _matches(self, row: Row) -> bool:
        return self.on is None or self.on(row) is True

    @override
    def columns(self) -> list[str]:
        return self.children[0].columns() + self.children[1].columns()

    @property
    @override
    def label(self) -> str:
        return f"NestedLoopJoin ({self.kind})"


class Sort(Operator):
    """Order rows by several keys, each ascending or descending; NULLs sort first.

    :param child: the input.
    :param keys: ``(column name or function, descending)`` pairs, most
        significant first.
    """

    def __init__(self, child: Operator, keys: list[SortKey]) -> None:
        self.children = (child,)
        self.keys = keys

    @override
    def __iter__(self) -> Iterator[Row]:
        rows = list(self.children[0])  # blocking
        for key, descending in reversed(self.keys):  # stable sorts, last key first
            get = _getter(key)
            rows.sort(key=lambda r: _nulls_first(get(r)), reverse=descending)
        return iter(rows)

    @property
    @override
    def label(self) -> str:
        return "Sort " + ", ".join(f"{k}{' DESC' if d else ''}" for k, d in self.keys)


def _nulls_first(value: Value | None) -> tuple[bool, Ordered]:
    """Make a sort key under which NULL sorts before every value.

    ``(False, None) < (True, anything)``, so ``None`` is never compared with
    a real value.
    """
    return (value is not None, ordered(value))


class Limit(Operator):
    """Skip ``offset`` rows, then yield at most ``count``.

    :param child: the input.
    :param count: the maximum number of rows; ``None`` for no maximum.
    :param offset: how many rows to skip first; 0 by default.
    """

    def __init__(self, child: Operator, count: int | None, offset: int = 0) -> None:
        self.children = (child,)
        self.count, self.offset = count, offset

    @override
    def __iter__(self) -> Iterator[Row]:
        stop = None if self.count is None else self.offset + self.count
        return itertools.islice(self.children[0], self.offset, stop)

    @property
    @override
    def label(self) -> str:
        return f"Limit {self.count} offset {self.offset}"


class Distinct(Operator):
    """Drop rows equal to an earlier row, keeping the first of each.

    :param child: the input.
    """

    def __init__(self, child: Operator) -> None:
        self.children = (child,)

    @override
    def __iter__(self) -> Iterator[Row]:
        seen: set[tuple[tuple[str, Value | None], ...]] = set()
        for row in self.children[0]:
            key = tuple(row.items())
            if key not in seen:
                seen.add(key)
                yield row


type JoinKind = Literal["inner", "left"]


class Accumulator(Protocol):
    """Fold the values of one group into a single result."""

    def add(self, value: Value) -> None:
        """Fold in one non-NULL value."""
        ...

    def result(self) -> Value | None:
        """Return the aggregate of the values added so far."""
        ...


class AggregateFunction[A: Accumulator]:
    """Name an aggregate over a column, and make one accumulator per group.

    The type parameter is the kind of accumulator the function makes. It
    appears only as a return type, so ``AggregateFunction`` is covariant: a
    ``Count`` is an ``AggregateFunction[Accumulator]``.

    :param column: the column to aggregate; ``None`` (the default) means
        the whole row, as in ``COUNT(*)``.
    """

    def __init__(self, column: str | None = None) -> None:
        self.column = column

    def accumulator(self) -> A:
        """Return a fresh accumulator for one group; subclasses override this.

        :return: the accumulator.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{type(self).__name__.upper()}({self.column or '*'})"


class _CountAcc:
    def __init__(self) -> None:
        self.n = 0

    def add(self, value: Value) -> None:  # noqa: ARG002 - only the number of values matters
        self.n += 1

    def result(self) -> Value | None:
        return self.n


class _SumAcc:
    def __init__(self) -> None:
        self.total: Value | None = None

    def add(self, value: Value) -> None:
        self.total = value if self.total is None else cast("Value", arithmetic(self.total) + arithmetic(value))

    def result(self) -> Value | None:
        return self.total


class _AvgAcc(_SumAcc):
    def __init__(self) -> None:
        super().__init__()
        self.n = 0

    @override
    def add(self, value: Value) -> None:
        super().add(value)
        self.n += 1

    @override
    def result(self) -> Value | None:
        if self.total is None:
            return None
        return cast("Value", arithmetic(self.total) / arithmetic(self.n))


class _ExtremeAcc:
    def __init__(self, *, largest: bool) -> None:
        self.largest = largest
        self.best: Value | None = None

    def add(self, value: Value) -> None:
        if self.best is None or (ordered(value) > ordered(self.best)) == self.largest:
            self.best = value

    def result(self) -> Value | None:
        return self.best


class Count(AggregateFunction[_CountAcc]):
    """Count the non-NULL values of a column, or the rows (``COUNT(*)``)."""

    @override
    def accumulator(self) -> _CountAcc:
        return _CountAcc()


class Sum(AggregateFunction[_SumAcc]):
    """Add up the non-NULL values of a column; the sum of no values is NULL."""

    @override
    def accumulator(self) -> _SumAcc:
        return _SumAcc()


class Avg(AggregateFunction[_AvgAcc]):
    """Average the non-NULL values of a column; the average of none is NULL."""

    @override
    def accumulator(self) -> _AvgAcc:
        return _AvgAcc()


class Min(AggregateFunction[_ExtremeAcc]):
    """Find the smallest non-NULL value of a column."""

    @override
    def accumulator(self) -> _ExtremeAcc:
        return _ExtremeAcc(largest=False)


class Max(AggregateFunction[_ExtremeAcc]):
    """Find the largest non-NULL value of a column."""

    @override
    def accumulator(self) -> _ExtremeAcc:
        return _ExtremeAcc(largest=True)


class Aggregate(Operator):
    """Group rows by ``group_by`` and compute ``aggregates`` for each group.

    This is hash aggregation: one dict entry per group. With no
    ``group_by`` the whole input is one group, so an empty input still
    produces one row.

    :param child: the input.
    :param group_by: the grouping columns.
    :param aggregates: ``{output name: aggregate function}``.
    """

    def __init__(
        self, child: Operator, group_by: list[str], aggregates: dict[str, AggregateFunction[Accumulator]]
    ) -> None:
        self.children = (child,)
        self.group_by, self.aggregates = list(group_by), aggregates

    @override
    def __iter__(self) -> Iterator[Row]:
        groups: dict[tuple[Value | None, ...], list[Accumulator]] = {}
        for row in self.children[0]:  # blocking
            key = tuple(row[c] for c in self.group_by)
            if key not in groups:
                groups[key] = self._fresh()
            self._accumulate(groups[key], row)
        if not groups and not self.group_by:  # aggregate of no rows
            groups[()] = self._fresh()
        for key, accs in groups.items():
            out = Row(zip(self.group_by, key, strict=True))
            out.update((name, acc.result()) for name, acc in zip(self.aggregates, accs, strict=True))
            yield out

    def _fresh(self) -> list[Accumulator]:
        return [f.accumulator() for f in self.aggregates.values()]

    def _accumulate(self, accs: list[Accumulator], row: Row) -> None:
        """Fold one row into a group's accumulators; aggregates skip NULLs."""
        for f, acc in zip(self.aggregates.values(), accs, strict=True):
            value = True if f.column is None else row[f.column]  # COUNT(*) counts rows
            if value is not None:
                acc.add(value)

    @override
    def columns(self) -> list[str]:
        return self.group_by + list(self.aggregates)

    @property
    @override
    def label(self) -> str:
        aggs = ", ".join(f"{n}={f!r}" for n, f in self.aggregates.items())
        return f"Aggregate by {self.group_by or '()'}: {aggs}"


class PlannedSource(Source, Protocol):
    """Describe what the planner needs from a source: rows, indexes, and the committed table."""

    schema: TableSchema

    def row(self, rowid: int) -> StoredRow:
        """Return the stored row itself."""
        ...

    def lookup(self, key: Mapping[str, Value | None]) -> set[int]:
        """Return the rowids whose columns equal ``key``, through an index."""
        ...

    def range(
        self,
        column: str,
        lo: Value | None = None,
        hi: Value | None = None,
        *,
        lo_inclusive: bool = True,
        hi_inclusive: bool = True,
    ) -> list[int]:
        """Return the rowids within the bounds, through an ordered index."""
        ...

    def committed(self) -> Table:
        """Return the committed table, for its statistics and indexes."""
        ...
```

## `src/minidb/expr.py`

Expression trees. Developed in [Chapter 14](14-query-planning.md).

```python
"""Build predicates the planner can look inside: expression trees.

``col("age") > 30`` is not ``True`` or ``False`` but a :class:`Compare`
object. Expressions are callable, so they work anywhere a predicate does,
and they follow SQL's three-valued logic: ``None`` means UNKNOWN.
"""

from typing import TYPE_CHECKING
from typing import Literal
from typing import NoReturn
from typing import Protocol
from typing import cast
from typing import override

from minidb.values import arithmetic
from minidb.values import ordered

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

    from minidb.values import Ordered
    from minidb.values import Value

type CompareOp = Literal["=", "!=", "<", "<=", ">", ">="]
type ArithOp = Literal["+", "-", "*", "/"]

# System R's default selectivities, used when nothing better is known
EQ_SELECTIVITY = 1 / 10
RANGE_SELECTIVITY = 1 / 3
OTHER_SELECTIVITY = 1 / 2


class Statistics(Protocol):
    """Describe what selectivity estimates need to know about columns."""

    def distinct(self, column: str) -> int | None:
        """Return the number of distinct values in ``column``, or ``None`` if unknown."""
        ...


def _eq_selectivity(distinct: int | None) -> float:
    return 1 / distinct if distinct else EQ_SELECTIVITY


class Expr:
    """Represent an expression over a row; the base of every expression node.

    The comparison and arithmetic operators build new expressions instead of
    computing answers, and ``&``, ``|``, ``~`` combine conditions.

    >>> e = (col("age") >= 30) & ~col("city").is_null()
    >>> e
    ((age >= 30) AND NOT city IS NULL)
    >>> e({"age": 41, "city": "Paris"}), e({"age": None, "city": "Paris"})
    (True, None)
    """

    __hash__ = object.__hash__  # we override ==, but keep identity hashing

    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        """Evaluate the expression against ``row``; subclasses override this.

        :param row: the row, by column name.
        :return: the value, ``None`` meaning NULL or UNKNOWN.
        """
        raise NotImplementedError

    def __call__(self, row: Mapping[str, Value | None]) -> Value | None:  # noqa: D102 - a dunder
        return self.eval(row)

    def columns(self) -> set[str]:
        """Return the names of the columns the expression reads.

        :return: the column names, as written.
        """
        return set()

    def selectivity(self, stats: Statistics) -> float:
        """Estimate the fraction of rows for which this condition is true.

        :param stats: what is known about the columns.
        :return: a number between 0 and 1; 1/2 unless a subclass knows better.
        """
        del stats
        return OTHER_SELECTIVITY

    # -- building expressions with operators -----------------------------------------
    # Returning an expression from == and != is the point of this class, so
    # the incompatibility with object.__eq__ is deliberate.
    @override
    def __eq__(self, other: object) -> Compare:  # pyrefly: ignore[bad-override]
        return Compare("=", self, _wrap(other))

    @override
    def __ne__(self, other: object) -> Compare:  # pyrefly: ignore[bad-override]
        return Compare("!=", self, _wrap(other))

    def __lt__(self, other: object) -> Compare:
        return Compare("<", self, _wrap(other))

    def __le__(self, other: object) -> Compare:
        return Compare("<=", self, _wrap(other))

    def __gt__(self, other: object) -> Compare:
        return Compare(">", self, _wrap(other))

    def __ge__(self, other: object) -> Compare:
        return Compare(">=", self, _wrap(other))

    def __and__(self, other: object) -> And:
        return And(self, _wrap(other))

    def __or__(self, other: object) -> Or:
        return Or(self, _wrap(other))

    def __invert__(self) -> Not:
        return Not(self)

    def __add__(self, other: object) -> Arith:
        return Arith("+", self, _wrap(other))

    def __sub__(self, other: object) -> Arith:
        return Arith("-", self, _wrap(other))

    def __mul__(self, other: object) -> Arith:
        return Arith("*", self, _wrap(other))

    def __truediv__(self, other: object) -> Arith:
        return Arith("/", self, _wrap(other))

    def is_null(self) -> IsNull:
        """Return the condition ``self IS NULL``, which is never UNKNOWN.

        :return: the condition.
        """
        return IsNull(self)

    def is_not_null(self) -> Not:
        """Return the condition ``self IS NOT NULL``.

        :return: the condition.
        """
        return Not(IsNull(self))

    def isin(self, *values: Value | None) -> In:
        """Return the condition ``self IN (values)``.

        :param values: the values to look for.
        :return: the condition.
        """
        return In(self, values)

    def __bool__(self) -> NoReturn:
        raise TypeError("use & | ~ to combine expressions, not and/or/not")


def _wrap(value: object) -> Expr:
    """Turn a Python value into a constant; leave expressions alone."""
    return value if isinstance(value, Expr) else Const(cast("Value | None", value))


class Col(Expr):
    """Read a column: ``Col("age")``, or ``Col("u.age")`` qualified by an alias.

    :param name: the column's name, qualified or not.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        return row[self.name]

    @override
    def columns(self) -> set[str]:
        return {self.name}

    def __repr__(self) -> str:
        return self.name


class Const(Expr):
    """Hold a constant value.

    :param value: the value; ``None`` is NULL.
    """

    def __init__(self, value: Value | None) -> None:
        self.value = value

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        return self.value

    def __repr__(self) -> str:
        return "NULL" if self.value is None else repr(self.value)


_COMPARE: dict[CompareOp, Callable[[Ordered, Ordered], bool]] = {
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}
_FLIPPED: dict[CompareOp, CompareOp] = {"=": "=", "!=": "!=", "<": ">", "<=": ">=", ">": "<", ">=": "<="}


class Compare(Expr):
    """Compare two expressions; UNKNOWN if either side is NULL.

    >>> Compare("<", Col("a"), Const(3))({"a": 1}), (col("a") < 3)({"a": None})
    (True, None)

    :param op: one of ``= != < <= > >=``.
    :param left: the left operand.
    :param right: the right operand.
    """

    def __init__(self, op: CompareOp, left: Expr, right: Expr) -> None:
        self.op, self.left, self.right = op, left, right

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        a, b = self.left.eval(row), self.right.eval(row)
        if a is None or b is None:
            return None  # UNKNOWN
        return _COMPARE[self.op](ordered(a), ordered(b))

    @override
    def columns(self) -> set[str]:
        return self.left.columns() | self.right.columns()

    def flipped(self) -> Compare:
        """Return the same condition with the operands swapped: ``3 < a`` becomes ``a > 3``.

        :return: the flipped comparison.
        """
        return Compare(_FLIPPED[self.op], self.right, self.left)

    def column_first(self) -> Compare:
        """Return this comparison with a column on the left, if either side is one.

        :return: ``self`` or :meth:`flipped`.
        """
        return self.flipped() if isinstance(self.right, Col) and not isinstance(self.left, Col) else self

    @override
    def selectivity(self, stats: Statistics) -> float:
        c = self.column_first()
        if isinstance(c.left, Col) and isinstance(c.right, Col):
            if c.op != "=":
                return RANGE_SELECTIVITY
            known = [n for n in (stats.distinct(c.left.name), stats.distinct(c.right.name)) if n]
            return 1 / max(known) if known else EQ_SELECTIVITY
        if not isinstance(c.left, Col):
            return OTHER_SELECTIVITY
        eq = _eq_selectivity(stats.distinct(c.left.name))
        if c.op in ("=", "!="):
            return eq if c.op == "=" else 1 - eq
        return RANGE_SELECTIVITY

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"


class And(Expr):
    """Combine conditions with AND: false if any is false, else UNKNOWN if any is.

    :param items: the conditions.
    """

    def __init__(self, *items: Expr) -> None:
        self.items = items

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        results = [item.eval(row) for item in self.items]
        if any(r is False for r in results):
            return False
        return None if any(r is None for r in results) else True

    @override
    def columns(self) -> set[str]:
        return set[str]().union(*(i.columns() for i in self.items))

    @override
    def selectivity(self, stats: Statistics) -> float:
        result = 1.0
        for item in self.items:
            result *= item.selectivity(stats)  # the independence assumption
        return result

    def __repr__(self) -> str:
        return "(" + " AND ".join(map(repr, self.items)) + ")"


class Or(Expr):
    """Combine conditions with OR: true if any is true, else UNKNOWN if any is.

    :param items: the conditions.
    """

    def __init__(self, *items: Expr) -> None:
        self.items = items

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        results = [item.eval(row) for item in self.items]
        if any(r is True for r in results):
            return True
        return None if any(r is None for r in results) else False

    @override
    def columns(self) -> set[str]:
        return set[str]().union(*(i.columns() for i in self.items))

    @override
    def selectivity(self, stats: Statistics) -> float:
        result = 0.0
        for item in self.items:
            s = item.selectivity(stats)
            result = result + s - result * s
        return result

    def __repr__(self) -> str:
        return "(" + " OR ".join(map(repr, self.items)) + ")"


class Not(Expr):
    """Negate a condition; NOT UNKNOWN is UNKNOWN.

    :param item: the condition.
    """

    def __init__(self, item: Expr) -> None:
        self.item = item

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        v = self.item.eval(row)
        return None if v is None else not v

    @override
    def columns(self) -> set[str]:
        return self.item.columns()

    @override
    def selectivity(self, stats: Statistics) -> float:
        return 1 - self.item.selectivity(stats)

    def __repr__(self) -> str:
        return f"NOT {self.item!r}"


class IsNull(Expr):
    """Test for NULL; the result is never UNKNOWN.

    :param item: the expression to test.
    """

    def __init__(self, item: Expr) -> None:
        self.item = item

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool:
        return self.item.eval(row) is None

    @override
    def columns(self) -> set[str]:
        return self.item.columns()

    @override
    def selectivity(self, stats: Statistics) -> float:
        return EQ_SELECTIVITY

    def __repr__(self) -> str:
        return f"{self.item!r} IS NULL"


class In(Expr):
    """Test membership in a list of constants, SQL-style.

    ``x IN (1, NULL)`` is UNKNOWN, not false, when ``x`` is 2.

    :param item: the expression to test.
    :param values: the constants.
    """

    def __init__(self, item: Expr, values: tuple[Value | None, ...]) -> None:
        self.item, self.values = item, values

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        v = self.item.eval(row)
        if v is None:
            return None
        if v in self.values:
            return True
        return None if None in self.values else False

    @override
    def columns(self) -> set[str]:
        return self.item.columns()

    @override
    def selectivity(self, stats: Statistics) -> float:
        if not isinstance(self.item, Col):
            return OTHER_SELECTIVITY
        return min(1.0, len(self.values) * _eq_selectivity(stats.distinct(self.item.name)))

    def __repr__(self) -> str:
        return f"{self.item!r} IN {self.values!r}"


_ARITH: dict[ArithOp, Callable[[Value, Value], Value]] = {
    "+": lambda a, b: cast("Value", arithmetic(a) + arithmetic(b)),
    "-": lambda a, b: cast("Value", arithmetic(a) - arithmetic(b)),
    "*": lambda a, b: cast("Value", arithmetic(a) * arithmetic(b)),
    "/": lambda a, b: cast("Value", arithmetic(a) / arithmetic(b)),
}


class Arith(Expr):
    """Apply ``+ - * /`` to two expressions; NULL if either is NULL.

    :param op: the operator.
    :param left: the left operand.
    :param right: the right operand.
    """

    def __init__(self, op: ArithOp, left: Expr, right: Expr) -> None:
        self.op, self.left, self.right = op, left, right

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        a, b = self.left.eval(row), self.right.eval(row)
        return None if a is None or b is None else _ARITH[self.op](a, b)

    @override
    def columns(self) -> set[str]:
        return self.left.columns() | self.right.columns()

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"


def col(name: str) -> Col:
    """Return an expression that reads column ``name``.

    :param name: the column, qualified (``"u.age"``) or not (``"age"``).
    :return: the column expression.
    """
    return Col(name)


def lit(value: Value | None) -> Const:
    """Return a constant expression.

    :param value: the constant; ``None`` is NULL.
    :return: the constant expression.
    """
    return Const(value)


def conjuncts(predicate: Expr) -> list[Expr]:
    """Split a condition on its top-level ANDs.

    >>> conjuncts((col("a") == 1) & (col("b") == 2) & (col("c") == 3))
    [(a = 1), (b = 2), (c = 3)]

    :param predicate: the condition.
    :return: the parts which must all be true.
    """
    if isinstance(predicate, And):
        return [c for item in predicate.items for c in conjuncts(item)]
    return [predicate]
```

## `src/minidb/query.py`

The query builder. Developed in [Chapter 7](07-query-primitives.md).

```python
"""Provide a fluent, immutable query builder on top of the operators."""

from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from typing import TYPE_CHECKING
from typing import Protocol

from minidb.operators import Aggregate
from minidb.operators import Distinct
from minidb.operators import Filter
from minidb.operators import Limit
from minidb.operators import NestedLoopJoin
from minidb.operators import Project
from minidb.operators import Scan
from minidb.operators import Sort
from minidb.planner import Planner

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import AbstractContextManager

    from minidb.operators import Accumulator
    from minidb.operators import AggregateFunction
    from minidb.operators import JoinKind
    from minidb.operators import Operator
    from minidb.operators import PlannedSource
    from minidb.operators import Row
    from minidb.operators import RowFunction
    from minidb.operators import RowPredicate
    from minidb.operators import SortKey
    from minidb.values import Value


class QueryState(Protocol):
    """Describe where a query finds its tables, and how it protects its reads."""

    def table(self, name: str) -> PlannedSource:
        """Return the table (or view) called ``name``."""
        ...

    def reading(self) -> AbstractContextManager[object]:
        """Return a context manager to hold while the query reads."""
        ...


@dataclass(frozen=True)
class Query:
    """Build a query step by step; each method returns a new, extended query.

    Nothing runs until the query is iterated, or :meth:`all`, :meth:`first`
    or :meth:`explain` is called. The parts are assembled in the order SQL
    evaluates them: FROM and JOIN, WHERE, GROUP BY, HAVING, ORDER BY,
    SELECT, DISTINCT, LIMIT.

    :param state: where the tables come from.
    :param table: the first table, as in ``FROM table``.
    :param alias: its alias; ``None`` (the default) uses the table's name.
    """

    state: QueryState
    table: str
    alias: str | None = None
    joins: tuple[tuple[str, str | None, RowPredicate, JoinKind], ...] = ()
    filters: tuple[RowPredicate, ...] = ()
    grouping: tuple[str, ...] | None = None
    aggregates: dict[str, AggregateFunction[Accumulator]] = field(default_factory=dict)
    having_filters: tuple[RowPredicate, ...] = ()
    ordering: tuple[SortKey, ...] = ()
    outputs: dict[str, str | RowFunction] | None = None
    is_distinct: bool = False
    bounds: tuple[int | None, int] | None = None

    # -- building ---------------------------------------------------------------
    def join(self, table: str, on: RowPredicate, alias: str | None = None, kind: JoinKind = "inner") -> Query:
        """Join another table.

        :param table: the table to join.
        :param on: the join condition.
        :param alias: its alias; ``None`` (the default) uses its name.
        :param kind: ``"inner"`` (the default) or ``"left"``.
        :return: the extended query.
        """
        return replace(self, joins=(*self.joins, (table, alias, on, kind)))

    def where(self, predicate: RowPredicate) -> Query:
        """Keep only rows for which ``predicate`` is true; calls combine with AND.

        :param predicate: a function of the row.
        :return: the extended query.
        """
        return replace(self, filters=(*self.filters, predicate))

    def group_by(self, *columns: str, **aggregates: AggregateFunction[Accumulator]) -> Query:
        """Group rows by ``columns`` and compute ``aggregates`` for each group.

        :param columns: the grouping columns; none for a single group.
        :param aggregates: ``name=function`` for each output aggregate.
        :return: the extended query.
        """
        return replace(self, grouping=columns, aggregates=aggregates)

    def having(self, predicate: RowPredicate) -> Query:
        """Keep only groups for which ``predicate`` is true.

        :param predicate: a function of the aggregated row.
        :return: the extended query.
        """
        return replace(self, having_filters=(*self.having_filters, predicate))

    def order_by(self, *keys: str | RowFunction) -> Query:
        """Sort the result; ``"name"`` ascends, ``"-name"`` descends.

        :param keys: column names, optionally prefixed with ``-``, or
            functions of the row, most significant first.
        :return: the extended query.
        """
        parsed = tuple((k[1:], True) if isinstance(k, str) and k.startswith("-") else (k, False) for k in keys)
        return replace(self, ordering=(*self.ordering, *parsed))

    def select(self, *columns: str, **computed: str | RowFunction) -> Query:
        """Choose the output columns.

        ``select("u.name", total="o.total", double=lambda r: 2 * r["x"])``

        :param columns: columns to output, under their unqualified names.
        :param computed: ``name=column`` or ``name=function`` pairs.
        :return: the extended query.
        :raises ValueError: if two outputs would have the same name.
        """
        outputs: dict[str, str | RowFunction] = {c.rpartition(".")[2]: c for c in columns}
        if len(outputs) != len(columns):
            raise ValueError("duplicate output names; use keyword aliases")
        return replace(self, outputs=outputs | computed)

    def distinct(self) -> Query:
        """Drop duplicate result rows.

        :return: the extended query.
        """
        return replace(self, is_distinct=True)

    def limit(self, count: int | None, offset: int = 0) -> Query:
        """Return at most ``count`` rows, after skipping ``offset``.

        :param count: the maximum number of rows, or ``None`` for no limit.
        :param offset: the rows to skip first; 0 by default.
        :return: the extended query.
        """
        return replace(self, bounds=(count, offset))

    # -- planning ---------------------------------------------------------------
    def plan(self) -> Operator:
        """Return the physical plan chosen by the cost-based planner.

        :return: the root operator.
        """
        return Planner(self).plan()

    def plan_naive(self) -> Operator:
        """Return Chapter 7's plan: joins in the written order, every filter on top.

        :return: the root operator.
        """
        op: Operator = Scan(self.state.table(self.table), self.alias)
        for jtable, jalias, on, kind in self.joins:
            op = NestedLoopJoin(op, Scan(self.state.table(jtable), jalias), on, kind)
        for predicate in self.filters:
            op = Filter(op, predicate)
        return self.finish_plan(op)

    def finish_plan(self, op: Operator) -> Operator:
        """Add GROUP BY, HAVING, ORDER BY, SELECT, DISTINCT and LIMIT on top of ``op``.

        :param op: the plan for FROM, JOIN and WHERE.
        :return: the complete plan.
        """
        return self._shape(self._group(op))

    def _group(self, op: Operator) -> Operator:
        if self.grouping is not None:
            op = Aggregate(op, list(self.grouping), self.aggregates)
        for predicate in self.having_filters:
            op = Filter(op, predicate)
        return op

    def _shape(self, op: Operator) -> Operator:
        if self.ordering:
            op = Sort(op, list(self.ordering))
        if self.outputs is not None:
            op = Project(op, self.outputs)
        if self.is_distinct:
            op = Distinct(op)
        if self.bounds is not None:
            op = Limit(op, *self.bounds)
        return op

    # -- running ----------------------------------------------------------------
    def __iter__(self) -> Iterator[Row]:
        with self.state.reading():
            rows = list(self.plan())  # materialize while protected
        return iter(rows)

    def all(self) -> list[dict[str, Value | None]]:
        """Run the query and return every row, as a plain dict.

        :return: the result rows.
        """
        with self.state.reading():
            return [dict(row) for row in self.plan()]

    def first(self) -> dict[str, Value | None] | None:
        """Run the query and return its first row.

        :return: the first row, or ``None`` if there are no rows.
        """
        rows = self.limit(1).all()
        return rows[0] if rows else None

    def explain(self) -> str:
        """Describe the plan, one operator per line.

        :return: the description.
        """
        return self.plan().explain()
```

## `src/minidb/planner.py`

The cost-based planner. Developed in [Chapter 14](14-query-planning.md).

```python
"""Plan queries: choose access paths, push filters down, and order joins by cost.

The planner turns a :class:`~minidb.query.Query` into a tree of physical
operators. Conditions written as :class:`~minidb.expr.Expr` objects can be
analysed; plain Python callables are opaque, and are applied last, exactly
where the query put them.
"""

import math
from typing import TYPE_CHECKING
from typing import Literal
from typing import override

from minidb.errors import DatabaseError
from minidb.expr import And
from minidb.expr import Col
from minidb.expr import Compare
from minidb.expr import Const
from minidb.expr import Expr
from minidb.expr import conjuncts
from minidb.operators import Filter
from minidb.operators import NestedLoopJoin
from minidb.operators import Operator
from minidb.operators import Row
from minidb.operators import Scan
from minidb.values import ordered

if TYPE_CHECKING:
    from collections.abc import Iterator

    from minidb.expr import CompareOp
    from minidb.index import Index
    from minidb.operators import PlannedSource
    from minidb.operators import RowPredicate
    from minidb.query import Query
    from minidb.values import Value

type Candidate = tuple[float, Operator, list[Expr]]  # (cost, access path, conditions it consumes)
type RangeCondition = tuple[CompareOp, Value, Expr]
type Bounds = tuple[Value | None, Value | None, bool, bool]  # lo, hi, lo_inclusive, hi_inclusive


# -- physical operators that need indexes or hashing ----------------------------------------
class IndexLookup(Operator):
    """Yield the rows whose indexed columns equal ``key``, without a scan.

    :param source: the table or view.
    :param alias: the qualifier for column names.
    :param index_name: the index used, for :meth:`explain`.
    :param key: ``{column: value}`` to look up.
    """

    def __init__(self, source: PlannedSource, alias: str, index_name: str, key: dict[str, Value | None]) -> None:
        self.source, self.alias, self.index_name, self.key = source, alias, index_name, key

    @override
    def __iter__(self) -> Iterator[Row]:
        for rid in self.source.lookup(self.key):
            row = self.source.row(rid)
            yield Row({f"{self.alias}.{c}": row[c] for c in self.source.columns})

    @override
    def columns(self) -> list[str]:
        return [f"{self.alias}.{c}" for c in self.source.columns]

    @property
    @override
    def label(self) -> str:
        return f"IndexLookup {self.source.name} AS {self.alias} using {self.index_name} {self.key}"


class IndexRange(Operator):
    """Yield the rows whose ``column`` lies between ``lo`` and ``hi``, through an ordered index.

    :param source: the table or view.
    :param alias: the qualifier for column names.
    :param index_name: the index used, for :meth:`explain`.
    :param column: the indexed column.
    :param bounds: ``(lo, hi, lo_inclusive, hi_inclusive)``; a ``None``
        bound is open.
    """

    def __init__(self, source: PlannedSource, alias: str, index_name: str, column: str, bounds: Bounds) -> None:
        self.source, self.alias, self.index_name, self.column = source, alias, index_name, column
        self.bounds = bounds

    @override
    def __iter__(self) -> Iterator[Row]:
        lo, hi, lo_inclusive, hi_inclusive = self.bounds
        for rid in self.source.range(self.column, lo, hi, lo_inclusive=lo_inclusive, hi_inclusive=hi_inclusive):
            row = self.source.row(rid)
            yield Row({f"{self.alias}.{c}": row[c] for c in self.source.columns})

    @override
    def columns(self) -> list[str]:
        return [f"{self.alias}.{c}" for c in self.source.columns]

    @property
    @override
    def label(self) -> str:
        lo, hi, lo_inclusive, hi_inclusive = self.bounds
        left = "" if lo is None else f"{lo!r} {'<=' if lo_inclusive else '<'} "
        right = "" if hi is None else f" {'<=' if hi_inclusive else '<'} {hi!r}"
        return f"IndexRange {self.source.name} AS {self.alias} using {self.index_name}: {left}{self.column}{right}"


class HashJoin(Operator):
    """Join on equalities in O(|left| + |right|): hash one side, probe with the other.

    :param left: the left input.
    :param right: the right input.
    :param left_keys: the join columns of the left input.
    :param right_keys: the matching columns of the right input.
    :param build: which side to hash, ideally the smaller; ``"right"`` by default.
    """

    def __init__(
        self,
        left: Operator,
        right: Operator,
        left_keys: list[Expr],
        right_keys: list[Expr],
        build: Literal["left", "right"] = "right",
    ) -> None:
        self.children = (left, right)
        self.left_keys, self.right_keys, self.build = left_keys, right_keys, build

    @override
    def __iter__(self) -> Iterator[Row]:
        left, right = self.children
        if self.build == "right":
            build, build_keys, probe, probe_keys = right, self.right_keys, left, self.left_keys
        else:
            build, build_keys, probe, probe_keys = left, self.left_keys, right, self.right_keys
        buckets = _buckets(build, build_keys)  # blocking on the build side
        for row in probe:
            key = tuple(k.eval(row) for k in probe_keys)
            for match in buckets.get(key, ()):
                yield Row(row | match)

    @override
    def columns(self) -> list[str]:
        return self.children[0].columns() + self.children[1].columns()

    @property
    @override
    def label(self) -> str:
        on = " AND ".join(f"{lk!r} = {rk!r}" for lk, rk in zip(self.left_keys, self.right_keys, strict=True))
        return f"HashJoin (build {self.build}) on {on}"


def _buckets(rows: Operator, keys: list[Expr]) -> dict[tuple[Value | None, ...], list[Row]]:
    """Group ``rows`` by their join key, leaving out keys with NULL: NULL never joins."""
    buckets: dict[tuple[Value | None, ...], list[Row]] = {}
    for row in rows:
        key = tuple(k.eval(row) for k in keys)
        if not any(v is None for v in key):
            buckets.setdefault(key, []).append(row)
    return buckets


def _conjunction(exprs: list[Expr]) -> Expr:
    return exprs[0] if len(exprs) == 1 else And(*exprs)


# -- the planner -------------------------------------------------------------------------
class Relation:
    """Describe one FROM or JOIN item: a source, its alias, and its committed table.

    :param source: the table, or a transaction's view of it.
    :param alias: the name the query uses for it.
    """

    def __init__(self, source: PlannedSource, alias: str) -> None:
        self.source, self.alias = source, alias
        self.table = source.committed()  # for statistics and indexes
        self.columns = set(source.columns)


class Planner:
    """Turn one query into a physical plan; also the query's :class:`~minidb.expr.Statistics`.

    :param query: the query to plan.
    """

    def __init__(self, query: Query) -> None:
        self.q = query
        rels = [Relation(query.state.table(query.table), query.alias or query.table)]
        rels += [Relation(query.state.table(t), a or t) for t, a, _, _ in query.joins]
        self.rels = {r.alias: r for r in rels}

    # -- column resolution and statistics ----------------------------------------------------
    def resolve(self, name: str) -> tuple[str, str] | None:
        """Find which relation a column belongs to.

        :param name: ``"u.age"`` or ``"age"``.
        :return: ``(alias, column)``, or ``None`` if the name is unknown or
            ambiguous.
        """
        if "." in name:
            alias, _, column = name.partition(".")
            rel = self.rels.get(alias)
            return (alias, column) if rel and column in rel.columns else None
        found = [(a, name) for a, r in self.rels.items() if name in r.columns]
        return found[0] if len(found) == 1 else None

    def aliases(self, expr: Expr) -> set[str] | None:
        """Return the relations an expression reads from.

        :param expr: the expression.
        :return: their aliases, or ``None`` if a column can't be resolved.
        """
        out: set[str] = set()
        for name in expr.columns():
            hit = self.resolve(name)
            if hit is None:
                return None
            out.add(hit[0])
        return out

    def distinct(self, column: str) -> int | None:
        """Return the number of distinct values of a column, from statistics or an index.

        :param column: the column, qualified or not.
        :return: the count, or ``None`` if unknown.
        """
        hit = self.resolve(column)
        if hit is None:
            return None
        table = self.rels[hit[0]].table
        if hit[1] in table.stats:
            return table.stats[hit[1]]
        index = table.index_on([hit[1]])
        return max(index.distinct_keys(), 1) if index is not None else None

    # -- access paths: how to read one table ---------------------------------------------------
    def access_path(self, rel: Relation, preds: list[Expr]) -> tuple[Operator, float]:
        """Choose the cheapest way to read ``rel`` given its own conditions.

        :param rel: the relation.
        :param preds: the conditions that mention only ``rel``.
        :return: the access path, with remaining conditions on top, and the
            estimated number of rows it produces.
        """
        preds, eq, ranges = self._canonical(rel, preds)
        n = len(rel.table)
        scan = Scan(rel.source, rel.alias)
        scan.estimate = n
        candidates: list[Candidate] = [(float(n), scan, [])]
        for index in rel.table.indexes.values():
            found = (self._lookup_path(rel, index, eq, n), self._range_path(rel, index, ranges, n))
            candidates.extend(c for c in found if c is not None)
        _, op, consumed = min(candidates, key=lambda c: c[0])
        estimate = n * math.prod(p.selectivity(self) for p in preds)
        residual = [p for p in preds if not any(p is c for c in consumed)]
        if residual:
            op = Filter(op, _conjunction(residual))
            op.estimate = estimate
        return op, estimate

    def _canonical(
        self, rel: Relation, preds: list[Expr]
    ) -> tuple[list[Expr], dict[str, tuple[Value, Expr]], dict[str, list[RangeCondition]]]:
        """Normalize the constants in ``column op constant`` conditions, and sort them by use.

        :return: the rewritten conditions; the equalities by column; and the
            range conditions by column.
        """
        canonical: list[Expr] = []
        eq: dict[str, tuple[Value, Expr]] = {}
        ranges: dict[str, list[RangeCondition]] = {}
        for p in preds:
            found = self._column_constant(rel, p)
            canonical.append(found[0] if found else p)
            if found is None:
                continue
            q, column, value = found
            if q.op == "=":
                eq[column] = (value, q)
            elif q.op in ("<", "<=", ">", ">="):
                ranges.setdefault(column, []).append((q.op, value, q))
        return canonical, eq, ranges

    def _column_constant(self, rel: Relation, p: Expr) -> tuple[Compare, str, Value] | None:
        """Return ``p`` as ``column op constant``, the constant prepared like a stored value."""
        if not isinstance(p, Compare):
            return None
        c = p.column_first()
        if not isinstance(c.left, Col) or not isinstance(c.right, Const) or c.right.value is None:
            return None
        hit = self.resolve(c.left.name)
        value = self._prepared(rel, hit[1], c.right.value) if hit else None
        if hit is None or value is None:
            return None
        return Compare(c.op, c.left, Const(value)), hit[1], value

    @staticmethod
    def _prepared(rel: Relation, column: str, value: Value) -> Value | None:
        """Normalize ``value`` for ``column``, or return ``None`` if it isn't valid there."""
        try:
            return rel.source.schema.column(column).prepare(value)
        except DatabaseError:
            return None  # not a valid value: compare it as written

    @staticmethod
    def _lookup_path(rel: Relation, index: Index, eq: dict[str, tuple[Value, Expr]], n: int) -> Candidate | None:
        if not set(index.columns) <= eq.keys():
            return None
        matches = n / max(index.distinct_keys(), 1)
        op = IndexLookup(rel.source, rel.alias, index.name, {c: eq[c][0] for c in index.columns})
        op.estimate = matches
        return (1 + matches, op, [eq[c][1] for c in index.columns])

    @staticmethod
    def _range_path(rel: Relation, index: Index, ranges: dict[str, list[RangeCondition]], n: int) -> Candidate | None:
        if index.kind == "hash" or len(index.columns) != 1 or index.columns[0] not in ranges:
            return None
        column = index.columns[0]
        bounds = _bounds(ranges[column])
        matches = n * (1 / 3) ** ((bounds[0] is not None) + (bounds[1] is not None))
        op = IndexRange(rel.source, rel.alias, index.name, column, bounds)
        op.estimate = matches
        return (1 + matches, op, [p for _, _, p in ranges[column]])

    # -- join ordering: greedy, smallest intermediate result first ------------------------------
    def join(self, paths: dict[str, tuple[Operator, float]], multi: list[tuple[Expr, set[str]]]) -> Operator:
        """Join the access paths, always adding the relation that gives the smallest result.

        :param paths: the access path and estimate of each relation.
        :param multi: conditions that mention several relations, with their aliases.
        :return: the joined plan.
        """
        remaining = dict(paths)
        start = min(remaining, key=lambda a: remaining[a][1])
        op, est = remaining.pop(start)
        joined, pending = {start}, list(multi)
        while remaining:
            scores = {a: self._score(a, joined, est, remaining[a][1], pending) for a in remaining}
            alias = min(scores, key=scores.__getitem__)
            right, right_est = remaining.pop(alias)
            usable = [e for e, al in pending if alias in al and al <= joined | {alias}]
            pending = [(e, al) for e, al in pending if not any(e is u for u in usable)]
            op = self._join_op(
                op, left_est=est, right=right, right_est=right_est, alias=alias, joined=joined, usable=usable
            )
            est = scores[alias][1]
            op.estimate = est
            joined.add(alias)
        for e, _ in pending:
            op = Filter(op, e)
        return op

    def _score(
        self, alias: str, joined: set[str], est: float, right_est: float, pending: list[tuple[Expr, set[str]]]
    ) -> tuple[bool, float]:
        """Rate joining ``alias`` next: connected joins first, then the smallest estimate."""
        usable = [e for e, al in pending if alias in al and al <= joined | {alias}]
        size = est * right_est * math.prod(e.selectivity(self) for e in usable)
        return (not usable, size)

    def _join_op(
        self,
        left: Operator,
        *,
        left_est: float,
        right: Operator,
        right_est: float,
        alias: str,
        joined: set[str],
        usable: list[Expr],
    ) -> Operator:
        """Join with a hash join when there are equalities between the sides, else nested loops."""
        left_keys: list[Expr] = []
        right_keys: list[Expr] = []
        others: list[Expr] = []
        for e in usable:
            sides = self._equi_sides(e, alias, joined)
            if sides is None:
                others.append(e)
            else:
                left_keys.append(sides[0])
                right_keys.append(sides[1])
        if not left_keys:
            return NestedLoopJoin(left, right, _conjunction(others) if others else None)
        op: Operator = HashJoin(left, right, left_keys, right_keys, "right" if right_est <= left_est else "left")
        return Filter(op, _conjunction(others)) if others else op

    def _equi_sides(self, e: Expr, alias: str, joined: set[str]) -> tuple[Col, Col] | None:
        """Return ``(joined side, new side)`` if ``e`` equates a column of each."""
        if not (isinstance(e, Compare) and e.op == "=" and isinstance(e.left, Col) and isinstance(e.right, Col)):
            return None
        lhs, rhs = self.resolve(e.left.name), self.resolve(e.right.name)
        if lhs is None or rhs is None:
            return None
        if rhs[0] == alias and lhs[0] in joined:
            return e.left, e.right
        return (e.right, e.left) if lhs[0] == alias and rhs[0] in joined else None

    # -- putting it together -----------------------------------------------------------------
    def plan(self) -> Operator:
        """Build the physical plan for the query.

        :return: the root operator.
        """
        if any(kind != "inner" for _, _, _, kind in self.q.joins):
            return self.q.plan_naive()  # outer joins: keep the written order
        local, multi, opaque = self._classify()
        paths = {a: self.access_path(self.rels[a], local[a]) for a in self.rels}
        op = self.join(paths, multi)
        for predicate in opaque:
            op = Filter(op, predicate)
        return self.q.finish_plan(op)

    def _classify(self) -> tuple[dict[str, list[Expr]], list[tuple[Expr, set[str]]], list[RowPredicate]]:
        """Split every condition into conjuncts, and sort them by the relations they mention."""
        local: dict[str, list[Expr]] = {a: [] for a in self.rels}
        multi: list[tuple[Expr, set[str]]] = []
        opaque: list[RowPredicate] = []
        for predicate in [*self.q.filters, *(on for _, _, on, _ in self.q.joins)]:
            parts = conjuncts(predicate) if isinstance(predicate, Expr) else [predicate]
            for part in parts:
                self._place(part, local, multi, opaque)
        return local, multi, opaque

    def _place(
        self,
        part: RowPredicate,
        local: dict[str, list[Expr]],
        multi: list[tuple[Expr, set[str]]],
        opaque: list[RowPredicate],
    ) -> None:
        aliases = self.aliases(part) if isinstance(part, Expr) else None
        if not aliases or not isinstance(part, Expr):
            opaque.append(part)  # callables, unresolvable or constant
        elif len(aliases) == 1:
            local[next(iter(aliases))].append(part)
        else:
            multi.append((part, aliases))


def _bounds(conditions: list[RangeCondition]) -> Bounds:
    """Combine range conditions on one column into the tightest lower and upper bounds."""
    lo: Value | None = None
    hi: Value | None = None
    lo_inclusive = hi_inclusive = True
    for op, value, _ in conditions:
        if op in (">", ">=") and (lo is None or ordered(value) > ordered(lo) or (value == lo and op == ">")):
            lo, lo_inclusive = value, op == ">="
        elif op in ("<", "<=") and (hi is None or ordered(value) < ordered(hi) or (value == hi and op == "<")):
            hi, hi_inclusive = value, op == "<="
    return lo, hi, lo_inclusive, hi_inclusive
```

## `src/minidb/locks.py`

Readers–writer locks. Developed in [Chapter 11](11-readers-writer-locks.md).

```python
"""Implement readers-writer locks: any number of readers, or exactly one writer."""

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING
from typing import Protocol
from typing import override

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import AbstractContextManager


class RWLock(Protocol):
    """Describe a readers-writer lock: shared mode for readers, exclusive for a writer."""

    def acquire_read(self) -> None:
        """Wait until the lock can be held in shared mode, and take it."""
        ...

    def release_read(self) -> None:
        """Release a shared hold."""
        ...

    def acquire_write(self) -> None:
        """Wait until the lock can be held exclusively, and take it."""
        ...

    def release_write(self) -> None:
        """Release the exclusive hold."""
        ...

    def read(self) -> AbstractContextManager[None]:
        """Return a context manager that holds the lock in shared mode."""
        ...

    def write(self) -> AbstractContextManager[None]:
        """Return a context manager that holds the lock exclusively."""
        ...


class RWLockBase:
    """Provide :meth:`read` and :meth:`write` on top of the four acquire/release methods.

    Subclasses implement the four methods; the context managers make sure
    every acquire is matched by a release, even when an exception escapes.
    """

    def acquire_read(self) -> None:
        """Wait until the lock can be held in shared mode, and take it."""
        raise NotImplementedError

    def release_read(self) -> None:
        """Release a shared hold."""
        raise NotImplementedError

    def acquire_write(self) -> None:
        """Wait until the lock can be held exclusively, and take it."""
        raise NotImplementedError

    def release_write(self) -> None:
        """Release the exclusive hold."""
        raise NotImplementedError

    @contextmanager
    def read(self) -> Iterator[None]:
        """Hold the lock in shared mode for the duration of a ``with`` block.

        :return: a context manager.
        """
        self.acquire_read()
        try:
            yield
        finally:
            self.release_read()

    @contextmanager
    def write(self) -> Iterator[None]:
        """Hold the lock exclusively for the duration of a ``with`` block.

        :return: a context manager.
        """
        self.acquire_write()
        try:
            yield
        finally:
            self.release_write()


class ReaderPreferringLock(RWLockBase):
    """Never make readers wait for waiting writers: Courtois et al.'s first problem.

    A steady stream of readers starves writers forever.
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._readers = 0
        self._writer = False

    @override
    def acquire_read(self) -> None:
        with self._cond:
            self._cond.wait_for(lambda: not self._writer)
            self._readers += 1

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    @override
    def acquire_write(self) -> None:
        with self._cond:
            self._cond.wait_for(lambda: not self._writer and self._readers == 0)
            self._writer = True

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._cond.notify_all()


class WriterPreferringLock(RWLockBase):
    """Make new readers wait while a writer waits: Courtois et al.'s second problem.

    A steady stream of writers starves readers forever.
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._readers = 0
        self._writer = False
        self._writers_waiting = 0

    @override
    def acquire_read(self) -> None:
        with self._cond:
            self._cond.wait_for(lambda: not self._writer and self._writers_waiting == 0)
            self._readers += 1

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    @override
    def acquire_write(self) -> None:
        with self._cond:
            self._writers_waiting += 1
            self._cond.wait_for(lambda: not self._writer and self._readers == 0)
            self._writers_waiting -= 1
            self._writer = True

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._cond.notify_all()


class FairRWLock(RWLockBase):
    """Admit requests strictly in arrival (ticket) order, so nobody starves.

    Consecutive readers are admitted together; a writer waits for the
    readers ahead of it to leave, and nobody behind it can overtake it.

    >>> lock = FairRWLock()
    >>> with lock.read(), lock.read():  # readers share
    ...     pass
    >>> with lock.write():
    ...     pass
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._next_ticket = 0  # handed to the next arrival
        self._serving = 0  # ticket at the head of the queue
        self._readers = 0  # readers inside
        self._writer = False  # writer inside?

    def _take_ticket(self) -> int:
        ticket = self._next_ticket
        self._next_ticket += 1
        return ticket

    @override
    def acquire_read(self) -> None:
        with self._cond:
            ticket = self._take_ticket()
            self._cond.wait_for(lambda: self._serving == ticket and not self._writer)
            self._readers += 1
            self._serving += 1
            self._cond.notify_all()  # the next ticket may be a reader too

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()  # a writer may be waiting at the head

    @override
    def acquire_write(self) -> None:
        with self._cond:
            ticket = self._take_ticket()
            self._cond.wait_for(lambda: self._serving == ticket and not self._writer and self._readers == 0)
            self._writer = True
            self._serving += 1

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._cond.notify_all()
```

## `src/minidb/uow.py`

The Unit of Work. Developed in [Chapter 12](12-isolation.md).

```python
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
```

## `src/minidb/storage.py`

Formats, snapshot and write-ahead log. Developed in [Chapter 13](13-persistence.md).

```python
"""Make data durable: pluggable formats, an atomic snapshot and a write-ahead log."""

import hashlib
import json
import os
import struct
import threading
import zlib
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Protocol
from typing import TypedDict
from typing import cast

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from io import BufferedRandom
    from io import BufferedWriter

    from minidb.schema import ForeignKey
    from minidb.schema import TableSchema
    from minidb.table import Table
    from minidb.values import Primitive
    from minidb.values import Row


class Format(Protocol):
    """Describe a file format: how to turn primitives into bytes, and back."""

    name: str
    suffix: str

    def dumps(self, obj: object) -> bytes:
        """Encode a structure of primitives (dicts, lists, strings, numbers, None)."""
        ...

    def loads(self, data: bytes) -> object:
        """Decode what :meth:`dumps` produced."""
        ...


class JsonFormat:
    """Store primitives as compact UTF-8 JSON.

    >>> JsonFormat().loads(JsonFormat().dumps({"a": [1, None, "x"]}))
    {'a': [1, None, 'x']}
    """

    name = "json"
    suffix = ".json"

    def dumps(self, obj: object) -> bytes:
        """Encode ``obj`` as JSON; NaN and infinities are refused.

        :param obj: a structure of primitives.
        :return: the encoded bytes.
        :raises ValueError: if ``obj`` contains NaN or an infinity.
        """
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()

    def loads(self, data: bytes) -> object:
        """Decode JSON bytes.

        :param data: what :meth:`dumps` produced.
        :return: the decoded structure.
        :raises ValueError: if ``data`` is not valid JSON.
        """
        result: object = json.loads(data.decode())
        return result


def encode_row(schema: TableSchema, row: Row) -> list[Primitive]:
    """Encode a row as a list of primitives, in column order.

    :param schema: the row's table.
    :param row: the row.
    :return: one primitive per column.
    """
    return [c.type.to_primitive(row[c.name]) for c in schema.columns]


def decode_row(schema: TableSchema, values: Sequence[Primitive]) -> Row:
    """Decode what :func:`encode_row` produced, validating every value.

    :param schema: the row's table.
    :param values: one primitive per column.
    :return: the row.
    :raises ValueError: if the number of values is wrong.
    :raises DomainError: if a value is not valid for its column.
    """
    if len(values) != len(schema.columns):
        raise ValueError(f"{schema.name}: stored row has {len(values)} values")
    return {c.name: c.type.from_primitive(v) for c, v in zip(schema.columns, values, strict=True)}


def schema_fingerprint(tables: Mapping[str, Table], foreign_keys: Sequence[ForeignKey]) -> str:
    """Hash everything declarative about a schema; checks and defaults are code, and left out.

    :param tables: the tables, by name.
    :param foreign_keys: the foreign keys between them.
    :return: a short hexadecimal digest.
    """
    parts: list[object] = []
    for name in sorted(tables):
        s = tables[name].schema
        parts.append((name, [(c.name, repr(c.type), c.nullable) for c in s.columns], s.primary_key, sorted(s.unique)))
    parts.append(sorted((fk.table, fk.columns, fk.ref_table, fk.ref_columns, fk.on_delete) for fk in foreign_keys))
    return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]


class TableData(TypedDict):
    """Describe one table in a snapshot."""

    next_rowid: int
    rows: list[tuple[int, list[Primitive]]]


class Snapshot(TypedDict):
    """Describe a snapshot: the whole database at one commit."""

    format: int
    fingerprint: str
    commit_seq: int
    tables: dict[str, TableData]


class LogRecord(TypedDict):
    """Describe one commit in the write-ahead log."""

    seq: int
    changes: list[tuple[str, int, list[Primitive] | None]]  # (table, rowid, values or None)


_FRAME = struct.Struct(">II")  # payload length, crc32


class Storage:
    """Keep a database in a directory: ``snapshot<suffix>`` plus ``wal.log``.

    :param directory: where the files live; created if missing.
    :param fmt: the format of the snapshot and log payloads;
        ``None`` (the default) means :class:`JsonFormat`.
    :param sync: whether to ``fsync`` before reporting a write as done;
        ``True`` by default. ``False`` is faster but not crash-safe.
    """

    def __init__(self, directory: str | os.PathLike[str], fmt: Format | None = None, *, sync: bool = True) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.format: Format = fmt if fmt is not None else JsonFormat()
        self.sync = sync
        self.snapshot_path = self.dir / f"snapshot{self.format.suffix}"
        self.log_path = self.dir / "wal.log"
        self._latch = threading.Lock()  # serializes file operations
        self._log: BufferedWriter | None = None

    # -- snapshot ----------------------------------------------------------------------
    def write_snapshot(self, state: Snapshot) -> None:
        """Replace the snapshot atomically: write a temporary file, then rename it.

        :param state: the whole database.
        """
        tmp = self.snapshot_path.with_name(self.snapshot_path.name + ".tmp")
        with self._latch:
            with tmp.open("wb") as f:
                f.write(self.format.dumps(state))
                self._fsync(f)
            tmp.replace(self.snapshot_path)  # atomic switch
            self._fsync_dir()

    def read_snapshot(self) -> Snapshot | None:
        """Return the last snapshot, or ``None`` if there is none yet.

        :return: the snapshot, or ``None``.
        """
        if not self.snapshot_path.exists():
            return None
        return cast("Snapshot", self.format.loads(self.snapshot_path.read_bytes()))

    # -- log ------------------------------------------------------------------------------
    def append(self, record: LogRecord) -> None:
        """Append one framed record to the log, and make it durable.

        :param record: the commit to log.
        """
        payload = self.format.dumps(record)
        frame = _FRAME.pack(len(payload), zlib.crc32(payload)) + payload
        with self._latch:
            if self._log is None:
                self._log = self.log_path.open("ab")
            self._log.write(frame)
            self._fsync(self._log)

    def read_log(self) -> Iterator[LogRecord]:
        """Yield the intact records, then cut off any torn or corrupt tail.

        :return: an iterator over the logged commits, oldest first.
        """
        if not self.log_path.exists():
            return
        data = self.log_path.read_bytes()
        pos = 0
        while (payload := _frame_at(data, pos)) is not None:
            yield cast("LogRecord", self.format.loads(payload))
            pos += _FRAME.size + len(payload)
        if pos < len(data):
            with self._latch, self.log_path.open("r+b") as f:
                f.truncate(pos)
                self._fsync(f)

    def truncate_log(self) -> None:
        """Empty the log, after a snapshot has made its records redundant."""
        with self._latch:
            if self._log is not None:
                self._log.close()
                self._log = None
            with self.log_path.open("wb") as f:
                self._fsync(f)

    def close(self) -> None:
        """Close the log file, if it is open."""
        with self._latch:
            if self._log is not None:
                self._log.close()
                self._log = None

    # -- fsync helpers --------------------------------------------------------------------
    def _fsync(self, f: BufferedWriter | BufferedRandom) -> None:
        f.flush()
        if self.sync:
            os.fsync(f.fileno())

    def _fsync_dir(self) -> None:
        if not self.sync or os.name != "posix":
            return  # Windows can't open directories
        fd = os.open(self.dir, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _frame_at(data: bytes, pos: int) -> bytes | None:
    """Return the payload of the intact frame at ``pos``, or ``None`` if there isn't one."""
    if pos + _FRAME.size > len(data):
        return None
    length, crc = _FRAME.unpack_from(data, pos)
    payload = data[pos + _FRAME.size : pos + _FRAME.size + length]
    if len(payload) < length or zlib.crc32(payload) != crc:
        return None  # torn write
    return payload
```

## `src/minidb/database.py`

The Database façade. Developed in [Chapter 13](13-persistence.md).

```python
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
```

## `src/minidb/sql.py`

The SQL front end. Developed in [Appendix A](appendix-a-sql-parser.md).

```python
"""Run a useful subset of SQL, compiled onto minidb's own API.

The module has four parts: a tokenizer, syntax-tree dataclasses, a parser
(recursive descent, with precedence climbing for expressions), and a
:class:`Connection` that compiles each statement and runs it.
"""

import re
from dataclasses import dataclass
from dataclasses import field
from decimal import Decimal
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Literal
from typing import override

from minidb.errors import DatabaseError
from minidb.expr import And
from minidb.expr import Arith
from minidb.expr import Col
from minidb.expr import Compare
from minidb.expr import Const
from minidb.expr import Expr
from minidb.expr import In
from minidb.expr import IsNull
from minidb.expr import Not
from minidb.expr import Or
from minidb.operators import Avg
from minidb.operators import Count
from minidb.operators import Max
from minidb.operators import Min
from minidb.operators import Sum
from minidb.schema import Check
from minidb.schema import Column
from minidb.schema import ForeignKey
from minidb.types import Boolean
from minidb.types import Date
from minidb.types import Integer
from minidb.types import Numeric
from minidb.types import Real
from minidb.types import Text
from minidb.types import Timestamp

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence

    from minidb.database import Database
    from minidb.expr import ArithOp
    from minidb.expr import CompareOp
    from minidb.operators import Accumulator
    from minidb.operators import AggregateFunction
    from minidb.operators import JoinKind
    from minidb.operators import RowFunction
    from minidb.query import Query
    from minidb.schema import OnDelete
    from minidb.types import Type
    from minidb.uow import UnitOfWork
    from minidb.values import Value

type Result = list[dict[str, Value | None]] | int | None


class SQLError(DatabaseError):
    """Signal SQL text that can't be parsed or compiled."""


# -- 1. tokens ------------------------------------------------------------------------------
KEYWORDS = frozenset(
    {
        "SELECT",
        "DISTINCT",
        "FROM",
        "AS",
        "JOIN",
        "INNER",
        "LEFT",
        "OUTER",
        "ON",
        "WHERE",
        "GROUP",
        "BY",
        "HAVING",
        "ORDER",
        "ASC",
        "DESC",
        "LIMIT",
        "OFFSET",
        "AND",
        "OR",
        "NOT",
        "IS",
        "NULL",
        "IN",
        "TRUE",
        "FALSE",
        "INSERT",
        "INTO",
        "VALUES",
        "UPDATE",
        "SET",
        "DELETE",
        "CREATE",
        "TABLE",
        "INDEX",
        "UNIQUE",
        "PRIMARY",
        "KEY",
        "DEFAULT",
        "REFERENCES",
        "CHECK",
        "CASCADE",
        "RESTRICT",
        "USING",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
    }
)

_TOKEN = re.compile(
    r"""
      (?P<space>\s+|--[^\n]*)
    | (?P<number>\d+\.\d*|\.\d+|\d+)
    | (?P<string>'(?:[^']|'')*')
    | (?P<name>[A-Za-z_][A-Za-z_0-9]*)
    | (?P<quoted>"(?:[^"]|"")+")
    | (?P<op><=|>=|<>|!=|[=<>(),.*+\-/;?])
    """,
    re.VERBOSE,
)

type TokenKind = Literal["number", "string", "name", "keyword", "op", "end"]
type TokenValue = int | Decimal | str | None


@dataclass(frozen=True)
class Token:
    """Hold one token: its kind, its value and where it starts in the text.

    :param kind: one of ``number string name keyword op end``.
    :param value: the number, the unquoted string or name, the upper-cased
        keyword, or the operator; ``None`` for the end.
    :param pos: the offset of its first character.
    """

    kind: TokenKind
    value: TokenValue
    pos: int


def _name_token(text: str, pos: int) -> Token:
    upper = text.upper()
    return Token("keyword", upper, pos) if upper in KEYWORDS else Token("name", text, pos)


_MAKERS: dict[str, Callable[[str, int], Token | None]] = {
    "space": lambda _text, _pos: None,
    "number": lambda text, pos: Token("number", Decimal(text) if "." in text else int(text), pos),
    "string": lambda text, pos: Token("string", text[1:-1].replace("''", "'"), pos),
    "name": _name_token,
    "quoted": lambda text, pos: Token("name", text[1:-1].replace('""', '"'), pos),
    "op": lambda text, pos: Token("op", "!=" if text == "<>" else text, pos),
}


def tokenize(sql: str) -> list[Token]:
    """Split SQL text into tokens, ending with an ``end`` token.

    >>> [t.value for t in tokenize("SELECT name FROM users WHERE age >= 3.5")]
    ['SELECT', 'name', 'FROM', 'users', 'WHERE', 'age', '>=', Decimal('3.5'), None]

    :param sql: the text.
    :return: the tokens.
    :raises SQLError: on a character that starts no token.
    """
    tokens: list[Token] = []
    pos = 0
    while pos < len(sql):
        m = _TOKEN.match(sql, pos)
        if m is None or m.lastgroup is None:
            raise SQLError(f"unexpected character {sql[pos]!r} at position {pos}")
        token = _MAKERS[m.lastgroup](m.group(), pos)
        if token is not None:
            tokens.append(token)
        pos = m.end()
    tokens.append(Token("end", None, pos))
    return tokens


# -- 2. syntax tree -----------------------------------------------------------------------------
@dataclass(eq=False, repr=False)  # keep Expr's == (it builds a Compare) and its repr
class AggCall(Expr):
    """Stand for ``COUNT(*)``, ``SUM(x)`` and so on inside an expression.

    Grouping computes each aggregate under its :attr:`key`, so evaluating the
    call afterwards just reads that column.

    :param func: the aggregate's name, upper-cased.
    :param column: its column, or ``None`` for ``*``.
    """

    func: str
    column: str | None

    @property
    def key(self) -> str:
        """Return the output column the aggregate is computed into, e.g. ``"SUM(o.total)"``."""
        return f"{self.func}({self.column or '*'})"

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        return row[self.key]

    def __repr__(self) -> str:
        return self.key


@dataclass
class Select:
    """Hold a parsed ``SELECT``; ``items`` is ``None`` for ``SELECT *``."""

    items: list[tuple[Expr, str | None]] | None
    distinct: bool
    table: tuple[str, str | None]
    joins: list[tuple[str, str | None, Expr, JoinKind]]
    where: Expr | None
    group_by: list[str]
    having: Expr | None
    order_by: list[tuple[Expr, bool]]
    limit: int | None
    offset: int


@dataclass
class Insert:
    """Hold a parsed ``INSERT``; ``columns`` is ``None`` for all, in order."""

    table: str
    columns: list[str] | None
    rows: list[list[Value | None]]


@dataclass
class Update:
    """Hold a parsed ``UPDATE``."""

    table: str
    assignments: dict[str, Expr]
    where: Expr | None


@dataclass
class Delete:
    """Hold a parsed ``DELETE``."""

    table: str
    where: Expr | None


@dataclass
class CreateTable:
    """Hold a parsed ``CREATE TABLE``."""

    name: str
    columns: list[Column] = field(default_factory=list[Column])
    primary_key: tuple[str, ...] = ()
    unique: list[tuple[str, ...]] = field(default_factory=list[tuple[str, ...]])
    checks: list[Expr] = field(default_factory=list[Expr])
    foreign_keys: list[ForeignKey] = field(default_factory=list[ForeignKey])


@dataclass
class CreateIndex:
    """Hold a parsed ``CREATE INDEX``."""

    name: str
    table: str
    columns: list[str]
    unique: bool
    kind: str


@dataclass
class TransactionControl:
    """Hold ``BEGIN``, ``COMMIT`` or ``ROLLBACK``."""

    action: str


type Statement = Select | Insert | Update | Delete | CreateTable | CreateIndex | TransactionControl


@dataclass
class _ColumnOptions:
    nullable: bool = True
    default: Value | None = None


AGGREGATES: dict[str, Callable[[str | None], AggregateFunction[Accumulator]]] = {
    "COUNT": Count,
    "SUM": Sum,
    "AVG": Avg,
    "MIN": Min,
    "MAX": Max,
}

_TYPES: dict[str, Callable[[list[int]], Type[Value]]] = {
    "INT": lambda _: Integer(),
    "INTEGER": lambda _: Integer(),
    "BIGINT": lambda _: Integer(),
    "REAL": lambda _: Real(),
    "FLOAT": lambda _: Real(),
    "DOUBLE": lambda _: Real(),
    "TEXT": lambda args: Text(*args[:1]),
    "VARCHAR": lambda args: Text(*args[:1]),
    "CHAR": lambda args: Text(*args[:1]),
    "BOOL": lambda _: Boolean(),
    "BOOLEAN": lambda _: Boolean(),
    "NUMERIC": lambda args: Numeric(*args[:2]),
    "DECIMAL": lambda args: Numeric(*args[:2]),
    "DATE": lambda _: Date(),
    "TIMESTAMP": lambda _: Timestamp(),
}

_ON_DELETE: dict[str, OnDelete] = {"CASCADE": "cascade", "SET": "set null", "RESTRICT": "restrict"}


# -- 3. the parser ----------------------------------------------------------------------------
class Parser:
    """Parse one SQL statement: recursive descent, with precedence climbing for expressions.

    >>> Parser("SELECT name FROM users WHERE age > ?", [40]).statement().where
    (age > 40)

    :param sql: the statement's text.
    :param params: the values for the ``?`` placeholders, in order; none by default.
    """

    # binding power of each infix operator: higher binds tighter
    INFIX: ClassVar[dict[str, int]] = {
        "OR": 10,
        "AND": 20,
        "=": 40,
        "!=": 40,
        "<": 40,
        "<=": 40,
        ">": 40,
        ">=": 40,
        "IS": 40,
        "IN": 40,
        "NOT": 40,
        "+": 50,
        "-": 50,
        "*": 60,
        "/": 60,
    }

    def __init__(self, sql: str, params: Sequence[Value | None] = ()) -> None:
        self.tokens = tokenize(sql)
        self.i = 0
        self.params = list(params)
        self.used_params = 0

    # -- token helpers ------------------------------------------------------------------
    def peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[min(self.i, len(self.tokens) - 1)]

    def next(self) -> Token:
        """Consume and return the current token."""
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, *values: str) -> Token | None:
        """Consume the current token if it is one of these keywords or operators.

        :param values: the acceptable keywords and operators.
        :return: the token, or ``None`` if it didn't match (and wasn't consumed).
        """
        tok = self.peek()
        if tok.kind in ("keyword", "op") and tok.value in values:
            self.i += 1
            return tok
        return None

    def expect(self, *values: str) -> Token:
        """Consume the current token, which must be one of these keywords or operators.

        :param values: the acceptable keywords and operators.
        :return: the token.
        :raises SQLError: if it is something else.
        """
        tok = self.accept(*values)
        if tok is None:
            got = self.peek()
            raise SQLError(f"expected {' or '.join(values)} at position {got.pos}, got {got.value!r}")
        return tok

    def name(self) -> str:
        """Consume a name.

        :return: the name.
        :raises SQLError: if the current token is not a name.
        """
        tok = self.next()
        if tok.kind != "name" or not isinstance(tok.value, str):
            raise SQLError(f"expected a name at position {tok.pos}, got {tok.value!r}")
        return tok.value

    def name_list(self) -> list[str]:
        """Consume ``(name, name, ...)``.

        :return: the names.
        """
        self.expect("(")
        names = [self.name()]
        while self.accept(","):
            names.append(self.name())
        self.expect(")")
        return names

    # -- statements -----------------------------------------------------------------------
    def statement(self) -> Statement:
        """Parse the whole text as one statement, optionally ending with ``;``.

        :return: the statement's syntax tree.
        :raises SQLError: if the text isn't one valid statement, or the
            number of parameters doesn't match the placeholders.
        """
        tok = self.peek()
        handlers: dict[TokenValue, Callable[[], Statement]] = {
            "SELECT": self.select,
            "INSERT": self.insert,
            "UPDATE": self.update,
            "DELETE": self.delete,
            "CREATE": self.create,
            "BEGIN": self.transaction,
            "COMMIT": self.transaction,
            "ROLLBACK": self.transaction,
        }
        handler = handlers.get(tok.value) if tok.kind == "keyword" else None
        if handler is None:
            raise SQLError(f"expected a statement at position {tok.pos}")
        stmt = handler()
        self.accept(";")
        if self.peek().kind != "end":
            raise SQLError(f"unexpected {self.peek().value!r} at position {self.peek().pos}")
        if self.used_params != len(self.params):
            raise SQLError(f"{len(self.params)} parameters given, {self.used_params} used")
        return stmt

    def transaction(self) -> TransactionControl:
        """Parse ``BEGIN``, ``COMMIT`` or ``ROLLBACK``."""
        return TransactionControl(str(self.next().value))

    def select(self) -> Select:
        """Parse a ``SELECT`` statement, clause by clause."""
        self.expect("SELECT")
        distinct = self.accept("DISTINCT") is not None
        items = None if self.accept("*") else self._items()
        self.expect("FROM")
        table = self.table_ref()
        joins = self._joins()
        where = self.expr() if self.accept("WHERE") else None
        group_by = self._group_by()
        having = self.expr() if self.accept("HAVING") else None
        order_by = self._order_by()
        limit, offset = self._limit()
        return Select(items, distinct, table, joins, where, group_by, having, order_by, limit, offset)

    def _items(self) -> list[tuple[Expr, str | None]]:
        items = [self._item()]
        while self.accept(","):
            items.append(self._item())
        return items

    def _item(self) -> tuple[Expr, str | None]:
        e = self.expr()
        if self.accept("AS") or self.peek().kind == "name":
            return e, self.name()
        return e, None

    def _joins(self) -> list[tuple[str, str | None, Expr, JoinKind]]:
        joins: list[tuple[str, str | None, Expr, JoinKind]] = []
        while (kind := self._join_kind()) is not None:
            name, alias = self.table_ref()
            self.expect("ON")
            joins.append((name, alias, self.expr(), kind))
        return joins

    def _join_kind(self) -> JoinKind | None:
        if self.accept("JOIN") or (self.accept("INNER") and self.expect("JOIN")):
            return "inner"
        if self.accept("LEFT"):
            self.accept("OUTER")
            self.expect("JOIN")
            return "left"
        return None

    def _group_by(self) -> list[str]:
        if not self.accept("GROUP"):
            return []
        self.expect("BY")
        columns = [self.column_name()]
        while self.accept(","):
            columns.append(self.column_name())
        return columns

    def _order_by(self) -> list[tuple[Expr, bool]]:
        if not self.accept("ORDER"):
            return []
        self.expect("BY")
        keys = [self._order_key()]
        while self.accept(","):
            keys.append(self._order_key())
        return keys

    def _order_key(self) -> tuple[Expr, bool]:
        e = self.expr()
        descending = self.accept("DESC") is not None
        if not descending:
            self.accept("ASC")
        return e, descending

    def _limit(self) -> tuple[int | None, int]:
        if not self.accept("LIMIT"):
            return None, 0
        limit = self.integer()
        return limit, self.integer() if self.accept("OFFSET") else 0

    def table_ref(self) -> tuple[str, str | None]:
        """Parse ``name [AS] [alias]``."""
        name = self.name()
        if self.accept("AS") or self.peek().kind == "name":
            return name, self.name()
        return name, None

    def column_name(self) -> str:
        """Parse ``name`` or ``alias.name``."""
        name = self.name()
        return f"{name}.{self.name()}" if self.accept(".") else name

    def integer(self) -> int:
        """Parse an integer literal (or a parameter holding one).

        :raises SQLError: if it is something else.
        """
        e = self.primary()
        if not isinstance(e, Const) or not isinstance(e.value, int):
            raise SQLError("expected an integer")
        return e.value

    def insert(self) -> Insert:
        """Parse ``INSERT INTO t [(columns)] VALUES (...), (...)``."""
        self.expect("INSERT")
        self.expect("INTO")
        table = self.name()
        columns = self.name_list() if self.peek().value == "(" else None
        self.expect("VALUES")
        rows = [self._value_row()]
        while self.accept(","):
            rows.append(self._value_row())
        return Insert(table, columns, rows)

    def _value_row(self) -> list[Value | None]:
        self.expect("(")
        row = [self.constant()]
        while self.accept(","):
            row.append(self.constant())
        self.expect(")")
        return row

    def constant(self) -> Value | None:
        """Parse an expression that must be a constant.

        :raises SQLError: if it isn't.
        """
        e = self.expr()
        if not isinstance(e, Const):
            raise SQLError("VALUES must contain constants")
        return e.value

    def update(self) -> Update:
        """Parse ``UPDATE t SET column = expr, ... [WHERE expr]``."""
        self.expect("UPDATE")
        table = self.name()
        self.expect("SET")
        assignments: dict[str, Expr] = {}
        while True:
            column = self.name()
            self.expect("=")
            assignments[column] = self.expr()
            if not self.accept(","):
                break
        where = self.expr() if self.accept("WHERE") else None
        return Update(table, assignments, where)

    def delete(self) -> Delete:
        """Parse ``DELETE FROM t [WHERE expr]``."""
        self.expect("DELETE")
        self.expect("FROM")
        table = self.name()
        return Delete(table, self.expr() if self.accept("WHERE") else None)

    def create(self) -> CreateTable | CreateIndex:
        """Parse ``CREATE TABLE`` or ``CREATE [UNIQUE] INDEX``."""
        self.expect("CREATE")
        unique = self.accept("UNIQUE") is not None
        if self.accept("INDEX"):
            return self._create_index(unique=unique)
        if unique:
            raise SQLError("expected INDEX after CREATE UNIQUE")
        self.expect("TABLE")
        stmt = CreateTable(self.name())
        self.expect("(")
        self._table_element(stmt)
        while self.accept(","):
            self._table_element(stmt)
        self.expect(")")
        return stmt

    def _create_index(self, *, unique: bool) -> CreateIndex:
        name = self.name()
        self.expect("ON")
        table = self.name()
        columns = self.name_list()
        kind = self.name().lower() if self.accept("USING") else "hash"
        return CreateIndex(name, table, columns, unique, kind)

    def _table_element(self, stmt: CreateTable) -> None:
        if self.accept("PRIMARY"):
            self.expect("KEY")
            stmt.primary_key = tuple(self.name_list())
        elif self.accept("UNIQUE"):
            stmt.unique.append(tuple(self.name_list()))
        elif self.accept("CHECK"):
            stmt.checks.append(self._parenthesized())
        else:
            self._column_def(stmt)

    def _parenthesized(self) -> Expr:
        self.expect("(")
        e = self.expr()
        self.expect(")")
        return e

    def _column_def(self, stmt: CreateTable) -> None:
        name = self.name()
        type_ = self.type_name()
        options = _ColumnOptions()
        while self._column_option(name, stmt, options):
            pass
        stmt.columns.append(Column(name, type_, nullable=options.nullable, default=options.default))

    def _column_option(self, name: str, stmt: CreateTable, options: _ColumnOptions) -> bool:
        """Parse one column option, if there is one; return whether there was."""
        actions: dict[str, Callable[[], None]] = {
            "NOT": lambda: self._not_null(options),
            "NULL": lambda: self._nullable(options),
            "PRIMARY": lambda: self._key_option(name, stmt, primary=True),
            "UNIQUE": lambda: self._key_option(name, stmt, primary=False),
            "DEFAULT": lambda: self._default(options),
            "CHECK": lambda: stmt.checks.append(self._parenthesized()),
            "REFERENCES": lambda: stmt.foreign_keys.append(self._references(name)),
        }
        tok = self.accept(*actions)
        if tok is None:
            return False
        actions[str(tok.value)]()
        return True

    def _not_null(self, options: _ColumnOptions) -> None:
        self.expect("NULL")
        options.nullable = False

    @staticmethod
    def _nullable(options: _ColumnOptions) -> None:
        options.nullable = True

    def _default(self, options: _ColumnOptions) -> None:
        options.default = self.constant()

    def _key_option(self, name: str, stmt: CreateTable, *, primary: bool) -> None:
        if primary:
            self.expect("KEY")
            stmt.primary_key = (name,)
        else:
            stmt.unique.append((name,))

    def _references(self, column: str) -> ForeignKey:
        ref_table = self.name()
        ref_columns = tuple(self.name_list()) if self.peek().value == "(" else ()
        on_delete: OnDelete = "restrict"
        if self.accept("ON"):
            self.expect("DELETE")
            action = self.expect("CASCADE", "SET", "RESTRICT").value
            if action == "SET":
                self.expect("NULL")
            on_delete = _ON_DELETE[str(action)]
        return ForeignKey((column,), ref_table, ref_columns, on_delete)

    def type_name(self) -> Type[Value]:
        """Parse a type such as ``INTEGER``, ``VARCHAR(80)`` or ``NUMERIC(8, 2)``.

        :raises SQLError: if the type is unknown.
        """
        name = self.name().upper()
        args: list[int] = []
        if self.accept("("):
            args.append(self.integer())
            while self.accept(","):
                args.append(self.integer())
            self.expect(")")
        if name not in _TYPES:
            raise SQLError(f"unknown type {name}")
        return _TYPES[name](args)

    # -- expressions: precedence climbing ------------------------------------------------
    def expr(self, min_bp: int = 0) -> Expr:
        """Parse an expression whose operators all bind tighter than ``min_bp``.

        :param min_bp: the binding power of the operator to our left; 0 by default.
        :return: the expression.
        """
        left = self.prefix()
        while True:
            tok = self.peek()
            op = tok.value if tok.kind in ("op", "keyword") and isinstance(tok.value, str) else ""
            bp = self.INFIX.get(op)
            if bp is None or bp <= min_bp:
                return left
            self.next()
            left = self._infix(op, left, bp)

    def _infix(self, op: str, left: Expr, bp: int) -> Expr:
        """Build the expression for ``left op ...``, parsing the right-hand side."""
        if op in ("OR", "AND"):
            right = self.expr(bp)
            return Or(left, right) if op == "OR" else And(left, right)
        if op == "IS":
            negate = self.accept("NOT") is not None
            self.expect("NULL")
            return Not(IsNull(left)) if negate else IsNull(left)
        if op in ("IN", "NOT"):
            return self._in(left, negate=op == "NOT")
        if op in ("+", "-", "*", "/"):
            return Arith(_arith_op(op), left, self.expr(bp))
        return Compare(_compare_op(op), left, self.expr(bp))

    def _in(self, left: Expr, *, negate: bool) -> Expr:
        if negate:
            self.expect("IN")
        self.expect("(")
        values = [self.constant()]
        while self.accept(","):
            values.append(self.constant())
        self.expect(")")
        membership = In(left, tuple(values))
        return Not(membership) if negate else membership

    def prefix(self) -> Expr:
        """Parse ``NOT x``, ``-x`` or a primary expression."""
        if self.accept("NOT"):
            return Not(self.expr(30))
        if self.accept("-"):
            operand = self.expr(70)
            if isinstance(operand, Const) and isinstance(operand.value, int | Decimal):
                return Const(-operand.value)
            return Arith("-", Const(0), operand)
        return self.primary()

    def primary(self) -> Expr:
        """Parse a literal, a parameter, a column, an aggregate or ``(expr)``.

        :raises SQLError: if none of those starts here.
        """
        tok = self.next()
        if tok.kind in ("number", "string"):
            return Const(tok.value)
        if tok.kind == "keyword" and tok.value in ("TRUE", "FALSE", "NULL"):
            return Const({"TRUE": True, "FALSE": False, "NULL": None}[str(tok.value)])
        if tok.value in ("?", "("):
            return self._parameter() if tok.value == "?" else self._group()
        if tok.kind == "name" and isinstance(tok.value, str):
            return self._name_expr(tok.value)
        raise SQLError(f"unexpected {tok.value!r} at position {tok.pos}")

    def _parameter(self) -> Const:
        if self.used_params >= len(self.params):
            raise SQLError("not enough parameters")
        self.used_params += 1
        return Const(self.params[self.used_params - 1])

    def _group(self) -> Expr:
        e = self.expr()
        self.expect(")")
        return e

    def _name_expr(self, name: str) -> Expr:
        if self.peek().value == "(" and name.upper() in AGGREGATES:
            self.next()
            column = None if self.accept("*") else self.column_name()
            self.expect(")")
            return AggCall(name.upper(), column)
        if self.accept("."):
            return Col(f"{name}.{self.name()}")
        return Col(name)


_COMPARE_OPS: dict[str, CompareOp] = {"=": "=", "!=": "!=", "<": "<", "<=": "<=", ">": ">", ">=": ">="}
_ARITH_OPS: dict[str, ArithOp] = {"+": "+", "-": "-", "*": "*", "/": "/"}


def _compare_op(op: str) -> CompareOp:
    return _COMPARE_OPS[op]


def _arith_op(op: str) -> ArithOp:
    return _ARITH_OPS[op]


# -- 4. execution ------------------------------------------------------------------------------
class Connection:
    """Run SQL statements against a database.

    Statements outside ``BEGIN ... COMMIT`` run in transactions of their
    own: ``SELECT`` in a read-only one, everything else through
    :meth:`Database.transaction`, with retries.

    :param db: the database.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.uow: UnitOfWork | None = None

    def execute(self, sql: str, params: Sequence[Value | None] = ()) -> Result:
        """Parse and run one statement.

        :param sql: the statement.
        :param params: the values for its ``?`` placeholders; none by default.
        :return: the rows for a ``SELECT``, the number of rows affected for
            ``INSERT``, ``UPDATE`` and ``DELETE``, ``None`` otherwise.
        :raises SQLError: if the statement is invalid.
        :raises DatabaseError: whatever the database refuses.
        """
        stmt = Parser(sql, params).statement()
        if isinstance(stmt, TransactionControl):
            return self._transaction_control(stmt.action)
        if isinstance(stmt, CreateTable | CreateIndex):
            return self._ddl(stmt)
        if self.uow is not None:
            return self._run(stmt, self.uow)
        if isinstance(stmt, Select):
            with self.db.unit_of_work(readonly=True) as uow:
                return self._select(stmt, uow)
        return self.db.transaction(lambda uow: self._run(stmt, uow))

    def _transaction_control(self, action: str) -> None:
        if action == "BEGIN":
            if self.uow is not None:
                raise SQLError("already in a transaction")
            self.uow = self.db.unit_of_work()
            return
        if self.uow is None:
            raise SQLError(f"{action} without BEGIN")
        uow, self.uow = self.uow, None
        if action == "ROLLBACK":
            uow.rollback()
            return
        with uow:  # commits, or rolls back if the commit fails
            pass

    def _ddl(self, stmt: CreateTable | CreateIndex) -> None:
        if self.uow is not None:
            raise SQLError("DDL is not allowed inside a transaction")
        if isinstance(stmt, CreateIndex):
            self.db.create_index(stmt.table, stmt.name, stmt.columns, unique=stmt.unique, kind=stmt.kind)
            return
        checks = [Check(f"check_{i + 1}", e) for i, e in enumerate(stmt.checks)]
        self.db.create_table(
            stmt.name,
            stmt.columns,
            primary_key=stmt.primary_key,
            unique=stmt.unique,
            checks=checks,
            foreign_keys=stmt.foreign_keys,
        )

    def _run(self, stmt: Select | Insert | Update | Delete, uow: UnitOfWork) -> Result:
        if isinstance(stmt, Insert):
            return self._insert(stmt, uow)
        if isinstance(stmt, Update):
            return self._update(stmt, uow)
        if isinstance(stmt, Delete):
            return uow.delete(stmt.table, stmt.where)
        return self._select(stmt, uow)

    @staticmethod
    def _insert(stmt: Insert, uow: UnitOfWork) -> int:
        names = stmt.columns or list(uow.table(stmt.table).columns)
        for values in stmt.rows:
            if len(values) != len(names):
                raise SQLError(f"{len(names)} columns but {len(values)} values")
            uow.insert(stmt.table, dict(zip(names, values, strict=True)))
        return len(stmt.rows)

    @staticmethod
    def _update(stmt: Update, uow: UnitOfWork) -> int:
        """Compute each row's new values from its old ones, and let dirty checking save them."""
        records = uow.find(stmt.table, stmt.where)
        for record in records:
            record.update({c: e.eval(record) for c, e in stmt.assignments.items()})
        uow.flush()
        return len(records)

    def _select(self, s: Select, uow: UnitOfWork) -> list[dict[str, Value | None]]:
        q = uow.query(*s.table)
        for name, alias, on, kind in s.joins:
            q = q.join(name, on, alias, kind)
        if s.where is not None:
            q = q.where(s.where)
        q = _with_ordering(_with_grouping(q, s), s)
        if s.items is not None:
            q = q.select(**_outputs(s.items))
        q = q.distinct() if s.distinct else q
        return (q.limit(s.limit, s.offset) if s.limit is not None or s.offset else q).all()


def _with_grouping(q: Query, s: Select) -> Query:
    """Add GROUP BY and HAVING, computing every aggregate the statement mentions."""
    aggregates = {call.key: AGGREGATES[call.func](call.column) for e in _all_exprs(s) for call in _agg_calls(e)}
    if s.group_by or aggregates:
        q = q.group_by(*s.group_by, **aggregates)
    return q.having(s.having) if s.having is not None else q


def _with_ordering(q: Query, s: Select) -> Query:
    """Add ORDER BY; a name that is a SELECT alias sorts by what the alias stands for."""
    if not s.order_by:
        return q
    aliases = {a: e for e, a in s.items or () if a}
    keys = [_sort_key(aliases.get(e.name, e) if isinstance(e, Col) else e, d) for e, d in s.order_by]
    return q.order_by(*keys)


def _outputs(items: list[tuple[Expr, str | None]]) -> dict[str, str | RowFunction]:
    """Name each output: its alias, else its column's name, else its text."""
    return {alias or (e.name.rpartition(".")[2] if isinstance(e, Col) else repr(e)): e for e, alias in items}


def _sort_key(e: Expr, descending: bool) -> str | RowFunction:  # noqa: FBT001 - a pair with e, from the parser
    """Turn an ORDER BY item into a key for :meth:`Query.order_by`."""
    if isinstance(e, Col | AggCall):  # by name: works in either direction
        return ("-" if descending else "") + (e.name if isinstance(e, Col) else e.key)
    if descending:
        raise SQLError("ORDER BY <expression> DESC is not supported; use an alias")
    return e


def _all_exprs(s: Select) -> Iterator[Expr]:
    yield from (e for e, _ in s.items or ())
    if s.having is not None:
        yield s.having
    yield from (e for e, _ in s.order_by)


def _agg_calls(e: Expr) -> Iterator[AggCall]:
    """Yield every aggregate call inside ``e``."""
    if isinstance(e, AggCall):
        yield e
    for child in _children(e):
        yield from _agg_calls(child)


def _children(e: Expr) -> tuple[Expr, ...]:
    if isinstance(e, Compare | Arith):
        return (e.left, e.right)
    if isinstance(e, Not | IsNull | In):
        return (e.item,)
    if isinstance(e, And | Or):
        return e.items
    return ()


def connect(db: Database) -> Connection:
    """Open a SQL connection to ``db``.

    >>> from minidb.database import Database
    >>> conn = connect(Database())
    >>> conn.execute("CREATE TABLE t (n INTEGER PRIMARY KEY)")
    >>> conn.execute("INSERT INTO t VALUES (1), (2)")
    2
    >>> conn.execute("SELECT COUNT(*) AS n FROM t")
    [{'n': 2}]

    :param db: the database.
    :return: a new connection.
    """
    return Connection(db)
```

## `examples/toy.py`

A toy relational algebra. Developed in [Chapter 1](01-relational-model.md).

```python
"""Implement relational algebra over lists of dicts: a toy to learn from.

The toy is not part of minidb. It exists to show, in a few lines, both the
idea of relational operators and everything a real database must add.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

type Row = dict[str, object]
type Relation = list[Row]


def select(relation: Relation, predicate: Callable[[Row], bool]) -> Relation:
    """Keep the rows of ``relation`` for which ``predicate`` is true (*selection*).

    >>> select([{"a": 1}, {"a": 2}], lambda row: row["a"] == 2)
    [{'a': 2}]

    :param relation: the input relation.
    :param predicate: decides whether a row is kept.
    :return: the kept rows, in input order.
    """
    return [row for row in relation if predicate(row)]


def project(relation: Relation, *attributes: str) -> Relation:
    """Keep only ``attributes`` of each row, dropping duplicate results (*projection*).

    Relations are sets, so two rows that become equal after projection are
    kept only once.

    >>> project([{"a": 1, "b": 1}, {"a": 1, "b": 2}], "a")
    [{'a': 1}]

    :param relation: the input relation.
    :param attributes: the names of the attributes to keep.
    :return: the projected rows, without duplicates.
    :raises KeyError: if a row lacks one of ``attributes``.
    """
    seen: set[tuple[tuple[str, object], ...]] = set()
    out: Relation = []
    for row in relation:
        projected = {a: row[a] for a in attributes}
        key = tuple(projected.items())
        if key not in seen:
            seen.add(key)
            out.append(projected)
    return out


def join(left: Relation, right: Relation, on: Callable[[Row, Row], bool]) -> Relation:
    """Combine every pair of rows from ``left`` and ``right`` that matches (*join*).

    >>> join([{"a": 1}], [{"b": 1}, {"b": 2}], lambda x, y: x["a"] == y["b"])
    [{'a': 1, 'b': 1}]

    :param left: the outer relation.
    :param right: the inner relation.
    :param on: decides whether a pair of rows matches.
    :return: the merged pairs, ordered by ``left`` and then by ``right``.
    """
    return [lrow | rrow for lrow in left for rrow in right if on(lrow, rrow)]


USERS: Relation = [
    {"id": 1, "name": "Ada", "age": 36},
    {"id": 2, "name": "Alan", "age": 41},
    {"id": 3, "name": "Grace", "age": None},
]
ORDERS: Relation = [
    {"order_id": 10, "user_id": 1, "total": 25},
    {"order_id": 11, "user_id": 2, "total": 40},
    {"order_id": 12, "user_id": 1, "total": 15},
]
```

## `examples/index_speed.py`

Scan vs index lookup. Developed in [Chapter 5](05-keys-and-indexes.md).

```python
"""Compare a lookup by scan with a lookup through the primary-key index."""

import timeit

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Text


def main() -> None:
    """Fill a table with 100,000 rows and time both kinds of lookup."""
    db = Database()
    db.create_table("t", [Column("id", Integer()), Column("name", Text())], primary_key="id")
    for i in range(100_000):
        db.insert("t", {"id": i, "name": f"n{i}"})
    scan = timeit.timeit(lambda: db.select("t", lambda r: r["id"] == 77_777), number=20) / 20
    index = timeit.timeit(lambda: db.select("t", {"id": 77_777}), number=20) / 20
    print(f"scan:  {scan * 1e3:8.3f} ms")
    print(f"index: {index * 1e3:8.3f} ms   ({scan / index:,.0f}x faster)")


if __name__ == "__main__":
    main()
```

## `examples/transfers.py`

Concurrent transfers. Developed in [Chapter 10](10-concurrency-i.md).

```python
"""Move money between accounts from many threads, and check none is lost.

An auditor thread keeps summing all balances while the transfers run; it
must always see the same total.
"""

import random
import sys
import threading

from minidb import Column
from minidb import Database
from minidb import DomainError
from minidb import Integer
from minidb import Sum

ACCOUNTS, START = 10, 1000


def gil_enabled() -> bool:
    """Return whether this interpreter runs with the GIL."""
    check = getattr(sys, "_is_gil_enabled", None)
    return bool(check()) if callable(check) else True


def transfer(db: Database, seed: int) -> None:
    """Make 500 random transfers, skipping those that would overdraw.

    :param db: the database.
    :param seed: the seed for this thread's random choices.
    """
    rnd = random.Random(seed)  # noqa: S311 - test data, not cryptography
    for _ in range(500):
        a, b = rnd.sample(range(ACCOUNTS), 2)
        amount = rnd.randint(1, 100)
        try:
            with db.unit_of_work() as uow:
                src, dst = uow.find("accounts", {"id": a})[0], uow.find("accounts", {"id": b})[0]
                src["balance"] = int(src["balance"] or 0) - amount  # DomainError below zero
                dst["balance"] = int(dst["balance"] or 0) + amount
        except DomainError:
            pass


def audit(db: Database, stop: threading.Event, problems: list[object]) -> None:
    """Sum the balances until ``stop`` is set, recording any wrong total.

    :param db: the database.
    :param stop: set when the transfers have finished.
    :param problems: where to record wrong totals.
    """
    while not stop.is_set():
        result = db.query("accounts").group_by(total=Sum("balance")).first()
        if result is None or result["total"] != ACCOUNTS * START:
            problems.append(result)


def main() -> None:
    """Run eight transfer threads and one auditor, then check the final total."""
    db = Database()
    db.create_table("accounts", [Column("id", Integer()), Column("balance", Integer(min=0))], primary_key="id")
    for i in range(ACCOUNTS):
        db.insert("accounts", {"id": i, "balance": START})
    stop, problems = threading.Event(), list[object]()
    workers = [threading.Thread(target=transfer, args=(db, s)) for s in range(8)]
    auditor = threading.Thread(target=audit, args=(db, stop, problems))
    auditor.start()
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    stop.set()
    auditor.join()
    final = sum(int(r["balance"] or 0) for r in db.select("accounts"))
    print(f"GIL={gil_enabled()} final total={final} audit problems={len(problems)}")
    assert final == ACCOUNTS * START
    assert not problems


if __name__ == "__main__":
    main()
```

## `examples/starvation.py`

Starvation under three locks. Developed in [Chapter 11](11-readers-writer-locks.md).

```python
"""Measure how long a late reader and a late writer wait under each lock.

A stream of overlapping readers and two looping writers keep each lock busy
for one second; a quarter of the way in, one more reader and one more
writer arrive and time how long they wait.
"""

import threading
import time

from minidb.locks import FairRWLock
from minidb.locks import ReaderPreferringLock
from minidb.locks import RWLockBase
from minidb.locks import WriterPreferringLock

DURATION, HOLD = 1.0, 0.01


def reader_stream(lock: RWLockBase, stop: threading.Event, offset: float) -> None:
    """Hold the lock for reading, again and again, until ``stop`` is set.

    :param lock: the lock under test.
    :param stop: set when the experiment is over.
    :param offset: how long to wait before starting, to stagger readers.
    """
    time.sleep(offset)
    while not stop.is_set():
        with lock.read():
            time.sleep(HOLD)


def writer_stream(lock: RWLockBase, stop: threading.Event) -> None:
    """Hold the lock for writing, briefly, again and again, until ``stop`` is set.

    :param lock: the lock under test.
    :param stop: set when the experiment is over.
    """
    while not stop.is_set():
        with lock.write():
            time.sleep(HOLD / 10)


def probe(lock: RWLockBase, kind: str, waited: dict[str, float]) -> None:
    """Arrive late, and record how long it takes to get the lock.

    :param lock: the lock under test.
    :param kind: ``"reader"`` or ``"writer"``.
    :param waited: where to record the wait, in seconds.
    """
    time.sleep(DURATION / 4)
    t0 = time.perf_counter()
    with lock.read() if kind == "reader" else lock.write():
        waited[kind] = time.perf_counter() - t0


def starvation_test(lock: RWLockBase) -> dict[str, float]:
    """Run the experiment on one lock.

    :param lock: the lock under test.
    :return: the late reader's and late writer's waits, in seconds.
    """
    stop, waited = threading.Event(), dict[str, float]()
    threads = [threading.Thread(target=reader_stream, args=(lock, stop, i * HOLD / 4)) for i in range(4)]
    threads += [threading.Thread(target=writer_stream, args=(lock, stop)) for _ in range(2)]
    threads += [threading.Thread(target=probe, args=(lock, k, waited)) for k in ("reader", "writer")]
    for t in threads:
        t.start()
    time.sleep(DURATION)
    stop.set()
    for t in threads:
        t.join()
    return waited


def main() -> None:
    """Print a table of waits for the three locks."""
    print(f"{'lock':<24}{'reader waited':>15}{'writer waited':>15}")
    for cls in (ReaderPreferringLock, WriterPreferringLock, FairRWLock):
        w = starvation_test(cls())
        print(f"{cls.__name__:<24}{w['reader'] * 1000:>12.1f} ms{w['writer'] * 1000:>12.1f} ms")


if __name__ == "__main__":
    main()
```

## `examples/shared_reads.py`

Shared vs exclusive reads. Developed in [Chapter 11](11-readers-writer-locks.md).

```python
"""Compare shared reads under the fair lock with reads that exclude each other.

``MutexAsRWLock`` satisfies the :class:`~minidb.locks.RWLock` protocol, but
makes every acquisition exclusive, as the single lock of Chapter 10 did.
"""

import sys
import threading
import time

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Sum
from minidb.locks import RWLockBase


class MutexAsRWLock(RWLockBase):
    """Behave like Chapter 10's lock: every acquisition is exclusive."""

    def __init__(self) -> None:
        self._mutex = threading.Lock()

    def acquire_read(self) -> None:
        """Take the mutex."""
        self._mutex.acquire()

    def release_read(self) -> None:
        """Release the mutex."""
        self._mutex.release()

    def acquire_write(self) -> None:
        """Take the mutex."""
        self._mutex.acquire()

    def release_write(self) -> None:
        """Release the mutex."""
        self._mutex.release()


def filled(db: Database) -> Database:
    """Create and fill the test table in ``db``.

    :param db: an empty database.
    :return: the same database.
    """
    db.create_table("t", [Column("id", Integer()), Column("v", Integer())], primary_key="id")
    with db.unit_of_work() as uow:
        for i in range(20_000):
            uow.insert("t", {"id": i, "v": i % 7})
    return db


def run(db: Database, threads: int = 4, queries: int = 20) -> float:
    """Run ``queries`` aggregate queries in each of ``threads`` threads.

    :param db: the database to query.
    :param threads: the number of threads; 4 by default.
    :param queries: the queries per thread; 20 by default.
    :return: the elapsed wall-clock time, in seconds.
    """

    def work() -> None:
        for _ in range(queries):
            db.query("t").group_by(total=Sum("v")).all()

    ts = [threading.Thread(target=work) for _ in range(threads)]
    t0 = time.perf_counter()
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return time.perf_counter() - t0


def main() -> None:
    """Time both locks and print the speed-up."""
    shared = run(filled(Database()))
    exclusive = run(filled(Database(lock=MutexAsRWLock())))
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"GIL={gil}  exclusive: {exclusive:.2f}s   shared: {shared:.2f}s   speed-up: {exclusive / shared:.1f}x")


if __name__ == "__main__":
    main()
```

## `examples/counter.py`

A contended counter. Developed in [Chapter 12](12-isolation.md).

```python
"""Increment one shared counter from eight threads, through ``Database.transaction``.

Every increment conflicts with every concurrent one, so this is the worst
case for optimistic concurrency; the test is that no increment is lost.
"""

import sys
import threading

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import UnitOfWork

THREADS, INCREMENTS = 8, 200


def increment(uow: UnitOfWork, attempts: list[int]) -> None:
    """Add one to the counter, recording the attempt.

    :param uow: the transaction to work in.
    :param attempts: one entry is appended per attempt, retries included.
    """
    attempts.append(1)
    record = uow.find("counter", {"id": 1})[0]
    record["n"] = int(record["n"] or 0) + 1


def worker(db: Database, attempts: list[int]) -> None:
    """Increment the counter ``INCREMENTS`` times, retrying on conflicts.

    :param db: the database.
    :param attempts: where :func:`increment` records its attempts.
    """
    for _ in range(INCREMENTS):
        db.transaction(lambda uow: increment(uow, attempts))


def main() -> None:
    """Run the threads, then print the counter and the number of retries."""
    db = Database()
    db.create_table("counter", [Column("id", Integer()), Column("n", Integer())], primary_key="id")
    db.insert("counter", {"id": 1, "n": 0})
    attempts: list[int] = []
    threads = [threading.Thread(target=worker, args=(db, attempts)) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    n = int(db.select("counter")[0]["n"] or 0)
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"GIL={gil} n={n} attempts={len(attempts)} conflicts={len(attempts) - n}")
    assert n == THREADS * INCREMENTS


if __name__ == "__main__":
    main()
```

## `examples/crash_child.py`

Transfers until killed. Developed in [Chapter 13](13-persistence.md).

```python
"""Make money transfers against a database on disk as fast as possible, forever.

``examples.crash_test`` starts this program and kills it at a random moment.
"""

import random
import sys

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Storage
from minidb import UnitOfWork

ACCOUNTS, START = 10, 1000


def open_db(folder: str) -> Database:
    """Declare the schema and attach the storage in ``folder``.

    :param folder: the database directory.
    :return: the database, with its saved data loaded.
    """
    db = Database()
    db.create_table("acct", [Column("id", Integer()), Column("bal", Integer(min=0))], primary_key="id")
    db.attach(Storage(folder))
    return db


def move(uow: UnitOfWork, a: int, b: int, amount: int) -> None:
    """Move ``amount`` from account ``a`` to account ``b``, if ``a`` has enough.

    :param uow: the transaction.
    :param a: the paying account.
    :param b: the receiving account.
    :param amount: the sum to move.
    """
    src, dst = uow.find("acct", {"id": a})[0], uow.find("acct", {"id": b})[0]
    if int(src["bal"] or 0) >= amount:
        src["bal"] = int(src["bal"] or 0) - amount
        dst["bal"] = int(dst["bal"] or 0) + amount


def main() -> None:
    """Fill the accounts if needed, say "ready", then transfer until killed."""
    if len(sys.argv) != 2:
        print("usage: python -m examples.crash_child FOLDER")
        return
    db = open_db(sys.argv[1])
    if not db.select("acct"):
        with db.unit_of_work() as uow:
            for i in range(ACCOUNTS):
                uow.insert("acct", {"id": i, "bal": START})
    print("ready", flush=True)
    rnd = random.Random()  # noqa: S311 - test data, not cryptography
    while True:
        a, b = rnd.sample(range(ACCOUNTS), 2)
        n = rnd.randint(1, 50)
        db.transaction(lambda uow, a=a, b=b, n=n: move(uow, a, b, n))


if __name__ == "__main__":
    main()
```

## `examples/crash_test.py`

Kill, recover, check. Developed in [Chapter 13](13-persistence.md).

```python
"""Kill a process that is committing transfers, recover its database, and check the total.

Every transfer is either entirely present or entirely absent, so the total
must always be what it was at the start.
"""

import subprocess
import sys
import tempfile
import time

from examples.crash_child import ACCOUNTS
from examples.crash_child import START
from examples.crash_child import open_db


def main() -> None:
    """Kill and recover the child five times, checkpointing once in between."""
    folder = tempfile.mkdtemp()
    for round_ in range(5):
        child = subprocess.Popen(  # noqa: S603 - runs this interpreter on our own module
            [sys.executable, "-m", "examples.crash_child", folder], stdout=subprocess.PIPE, text=True
        )
        assert child.stdout is not None
        child.stdout.readline()  # wait for "ready"
        time.sleep(0.2 + round_ * 0.1)
        child.kill()  # SIGKILL: no cleanup at all
        child.wait()
        child.stdout.close()
        db = open_db(folder)
        total = sum(int(r["bal"] or 0) for r in db.select("acct"))
        print(f"round {round_}: recovered commit {db.commit_seq:>5}, total = {total}")
        assert total == ACCOUNTS * START
        if round_ == 2:
            db.checkpoint()  # also survive a kill after a checkpoint
        db.close()


if __name__ == "__main__":
    main()
```

## `examples/planner_speed.py`

Naive vs planned join. Developed in [Chapter 14](14-query-planning.md).

```python
"""Time the same join with Chapter 7's naive plan and with the planner's plan."""

import time

from minidb import Column
from minidb import Database
from minidb import ForeignKey
from minidb import Integer
from minidb import Text
from minidb import col

CITIES = ["Paris", "London", "Rome", "Oslo", "Lima", "Pune", "Kyiv", "Cairo", "Quito", "Perth"]


def build() -> Database:
    """Create 1,000 users and 10,000 orders, with an age index and statistics.

    :return: the filled database.
    """
    db = Database()
    db.create_table(
        "users", [Column("id", Integer()), Column("city", Text()), Column("age", Integer())], primary_key="id"
    )
    db.create_table(
        "orders",
        [Column("id", Integer()), Column("user_id", Integer())],
        primary_key="id",
        foreign_keys=[ForeignKey(("user_id",), "users")],
    )
    with db.unit_of_work() as uow:
        for i in range(1000):
            uow.insert("users", {"id": i, "city": CITIES[i % 10], "age": 18 + (i * 7) % 60})
        for i in range(10_000):
            uow.insert("orders", {"id": i, "user_id": (i * 13) % 1000})
    db.create_index("users", "by_age", ["age"], kind="sorted")
    db.analyze()
    return db


def main() -> None:
    """Run both plans, check they agree, and print the times."""
    db = build()
    q = (
        db.query("users", "u")
        .join("orders", on=col("u.id") == col("o.user_id"), alias="o")
        .where((col("u.city") == "Paris") & (col("u.age") >= 30))
    )
    with db.reading():
        t0 = time.perf_counter()
        naive = list(q.plan_naive())
        t1 = time.perf_counter()
        planned = list(q.plan())
        t2 = time.perf_counter()
    assert len(naive) == len(planned)
    print(
        f"{len(planned)} rows | naive: {t1 - t0:.2f} s | planned: {(t2 - t1) * 1000:.1f} ms | {(t1 - t0) / (t2 - t1):,.0f}x faster"
    )


if __name__ == "__main__":
    main()
```

## `examples/index_benchmark.py`

Index kinds compared. Developed in [Chapter 15](15-b-trees.md).

```python
"""Insert 200,000 random keys into each kind of index, then run 1,000 range scans."""

import random
import time

from minidb.btree import BTreeIndex
from minidb.index import HashIndex
from minidb.index import KeyedIndex
from minidb.index import SortedIndex


def fill(index: KeyedIndex, rows: list[dict[str, int]]) -> float:
    """Add every row to ``index``.

    :param index: an empty index on column ``k``.
    :param rows: the rows to add.
    :return: the time taken, in seconds.
    """
    t0 = time.perf_counter()
    for rowid, row in enumerate(rows):
        index.add(rowid, dict(row))
    return time.perf_counter() - t0


def scan(index: SortedIndex | BTreeIndex, rnd: random.Random) -> float:
    """Run 1,000 range queries, each over one thousandth of the key space.

    :param index: a filled ordered index.
    :param rnd: the source of random bounds.
    :return: the time taken, in seconds.
    """
    t0 = time.perf_counter()
    for _ in range(1000):
        lo = rnd.randrange(10**9)
        index.range((lo,), (lo + 10**6,))
    return time.perf_counter() - t0


def main() -> None:
    """Print insert and range times for the three kinds of index."""
    rnd = random.Random(1)  # noqa: S311 - test data, not cryptography
    rows = [{"k": rnd.randrange(10**9)} for _ in range(200_000)]
    print(f"{'index':<12}{'200k inserts':>14}{'1k range scans':>16}")
    print(f"{'HashIndex':<12}{fill(HashIndex('i', ['k']), rows):>12.2f} s{'(no ranges)':>16}")
    for index in (SortedIndex("i", ["k"]), BTreeIndex("i", ["k"])):
        inserts = fill(index, rows)
        print(f"{type(index).__name__:<12}{inserts:>12.2f} s{scan(index, rnd):>14.2f} s")


if __name__ == "__main__":
    main()
```

## `examples/run_tests.py`

Run the test suite. Developed in [Appendix B](appendix-b-testing.md).

```python
"""Run the test suite, and fail if any test fails."""

import unittest


def main() -> None:
    """Load ``tests.test_minidb`` and run it."""
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_minidb")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful()


if __name__ == "__main__":
    main()
```

## `tests/test_minidb.py`

The test suite. Developed in [Appendix B](appendix-b-testing.md).

```python
"""Test minidb: unit, property-based, model-based, concurrency and crash tests."""

import random
import shutil
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from minidb import CheckError
from minidb import Column
from minidb import Database
from minidb import Date
from minidb import DomainError
from minidb import Integer
from minidb import Numeric
from minidb import Real
from minidb import Storage
from minidb import Text
from minidb import Timestamp
from minidb import UniqueError
from minidb import UnitOfWork
from minidb.btree import BPlusTree
from minidb.locks import FairRWLock

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator

    from minidb.index import Index
    from minidb.schema import ForeignKey
    from minidb.table import Table
    from minidb.values import Row


@contextmanager
def expect(error: type[BaseException], context: str = "") -> Iterator[None]:
    """Fail unless the block raises ``error``."""
    try:
        yield
    except error:
        return
    raise AssertionError(f"{error.__name__} not raised {context}")


# -- an integrity checker: the invariants every test can assert ------------------------------
def check_integrity(db: Database) -> None:
    """Raise AssertionError if any index, key or reference is inconsistent."""
    for t in db.tables.values():
        for index in t.indexes.values():
            _check_index(t, index)
        for row in t.rows.values():
            t.schema.prepare_row({}, base=row)  # re-runs NOT NULL and CHECKs
    for fk in db.foreign_keys:
        _check_references(db, fk)


def _check_index(t: Table, index: Index) -> None:
    """Rebuild the index's expected contents from the rows, and compare."""
    expected: dict[tuple[object, ...], set[int]] = {}
    for rowid, row in t.rows.items():
        key = index.key_of(row)
        if key is not None:
            expected.setdefault(key, set()).add(rowid)
    assert index.distinct_keys() == len(expected), f"{t.name}.{index.name}: stale keys"
    for key, rowids in expected.items():
        assert index.lookup(key) == rowids, f"{t.name}.{index.name}: wrong rows for {key}"
        assert not index.unique or len(rowids) == 1, f"{index.name}: duplicate {key}"


def _check_references(db: Database, fk: ForeignKey) -> None:
    parent = db.tables[fk.ref_table]
    for row in db.tables[fk.table].rows.values():
        key = fk.parent_key(row)
        assert key is None or parent.lookup(key), f"{fk.name}: orphan {row}"


# -- unit tests -----------------------------------------------------------------------------
class TypeTests(unittest.TestCase):
    def test_integer_rejects_bool(self) -> None:
        with expect(DomainError):
            Integer().normalize(True)  # noqa: FBT003 - the point of the test

    def test_numeric_rounds_half_even(self) -> None:
        assert str(Numeric(6, 2).normalize("2.665")) == "2.66"

    def test_round_trip_through_primitives(self) -> None:
        for t, raw in [
            (Numeric(8, 2), "12.30"),
            (Date(), "2026-11-18"),
            (Timestamp(), "2026-11-18T10:00:00+00:00"),
            (Real(), 0.1),
        ]:
            value = t.normalize(raw)
            assert t.from_primitive(t.to_primitive(value)) == value


# -- property-based: compare a data structure with a trivially correct model -----------------
def _btree_step(rnd: random.Random, tree: BPlusTree[int, int], model: dict[int, set[int]]) -> None:
    k, v = rnd.randrange(500), rnd.randrange(4)
    if rnd.random() < 0.6:
        tree.insert(k, v)
        model.setdefault(k, set()).add(v)
        return
    tree.remove(k, v)
    if v in model.get(k, set()):
        model[k].discard(v)
        if not model[k]:
            del model[k]


class BTreeProperties(unittest.TestCase):
    def test_matches_a_dict(self) -> None:
        for order in (3, 4, 7, 32):
            rnd = random.Random(order)  # noqa: S311 - test data
            tree, model = BPlusTree[int, int](order), dict[int, set[int]]()
            for _ in range(5000):
                _btree_step(rnd, tree, model)
            assert list(tree.items()) == sorted(model.items())
            assert [k for k, _ in tree.items(100, 300, lo_inclusive=False)] == [
                k for k in sorted(model) if 100 < k <= 300
            ]


# -- model-based: random operations on minidb and on a dict, compared after each step ----------
class UsersModel:
    """Predict, with a plain dict, what minidb should do with a ``users`` table."""

    def __init__(self) -> None:
        self.rows: dict[int, Row] = {}

    def insert(self, row: Row) -> type[Exception] | None:
        if int(row["age"] or 0) < 0:
            return CheckError
        if row["id"] in self.rows or any(r["email"] == row["email"] for r in self.rows.values()):
            return UniqueError
        self.rows[int(row["id"] or 0)] = row
        return None

    def update(self, row: Row) -> type[Exception] | None:
        uid = int(row["id"] or 0)
        if uid not in self.rows:
            return None
        if int(row["age"] or 0) < 0:
            return CheckError
        if any(r["email"] == row["email"] and i != uid for i, r in self.rows.items()):
            return UniqueError
        self.rows[uid] = self.rows[uid] | row
        return None

    def delete(self, row: Row) -> type[Exception] | None:
        self.rows.pop(int(row["id"] or 0), None)
        return None


def _users_db() -> Database:
    db = Database()
    db.create_table(
        "users",
        [Column("id", Integer()), Column("email", Text()), Column("age", Integer(), check=lambda a: int(a) >= 0)],
        primary_key="id",
        unique=["email"],
    )
    db.create_index("users", "by_age", ["age"], kind="btree")
    return db


def _actions(db: Database, row: Row) -> dict[str, Callable[[], object]]:
    changes = {"email": row["email"], "age": row["age"]}
    return {
        "insert": lambda: db.insert("users", row),
        "update": lambda: db.update("users", changes, {"id": row["id"]}),
        "delete": lambda: db.delete("users", {"id": row["id"]}),
    }


class ModelBasedTest(unittest.TestCase):
    def test_random_operations(self) -> None:
        rnd = random.Random(42)  # noqa: S311 - test data
        db, model = _users_db(), UsersModel()
        predict = {"insert": model.insert, "update": model.update, "delete": model.delete}
        for step in range(1500):
            row: Row = {"id": rnd.randrange(60), "email": f"u{rnd.randrange(60)}@x", "age": rnd.randrange(-3, 90)}
            op = rnd.choice(list(predict))
            expected = predict[op](row)
            if expected is None:
                _actions(db, row)[op]()
            else:
                with expect(expected, f"at step {step}: {op} {row}"):
                    _actions(db, row)[op]()
            if step % 50 == 0:
                check_integrity(db)
        assert sorted(db.select("users"), key=lambda r: int(r["id"] or 0)) == [
            model.rows[k] for k in sorted(model.rows)
        ]
        check_integrity(db)


# -- concurrency: invariants, fairness ----------------------------------------------------------
def _move(uow: UnitOfWork, a: int, b: int) -> None:
    src, dst = uow.find("acct", {"id": a})[0], uow.find("acct", {"id": b})[0]
    if int(src["bal"] or 0) >= 10:
        src["bal"] = int(src["bal"] or 0) - 10
        dst["bal"] = int(dst["bal"] or 0) + 10


def _transfers(db: Database, seed: int) -> None:
    rnd = random.Random(seed)  # noqa: S311 - test data
    for _ in range(100):
        a, b = rnd.sample(range(5), 2)
        db.transaction(lambda uow, a=a, b=b: _move(uow, a, b))


def _reader(lock: FairRWLock, stop: threading.Event, offset: float) -> None:
    time.sleep(offset)
    while not stop.is_set():
        with lock.read():
            time.sleep(0.005)


class ConcurrencyTests(unittest.TestCase):
    def test_transfers_preserve_total(self) -> None:
        db = Database()
        db.create_table("acct", [Column("id", Integer()), Column("bal", Integer(min=0))], primary_key="id")
        for i in range(5):
            db.insert("acct", {"id": i, "bal": 100})
        threads = [threading.Thread(target=_transfers, args=(db, s)) for s in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert sum(int(r["bal"] or 0) for r in db.select("acct")) == 500
        check_integrity(db)

    def test_fair_lock_bounds_writer_wait(self) -> None:
        lock, stop = FairRWLock(), threading.Event()
        readers = [threading.Thread(target=_reader, args=(lock, stop, i * 0.002)) for i in range(4)]
        for r in readers:
            r.start()
        time.sleep(0.05)
        t0 = time.perf_counter()
        with lock.write():
            waited = time.perf_counter() - t0
        stop.set()
        for r in readers:
            r.join()
        assert waited < 0.1  # a reader-preferring lock would wait until stop


# -- crash recovery: every possible torn write recovers to a prefix of the commits --------------
def _open(path: str) -> Database:
    db = Database()
    db.create_table("t", [Column("id", Integer()), Column("v", Text())], primary_key="id")
    db.attach(Storage(path, sync=False))
    return db


def _ids(db: Database) -> list[int]:
    return sorted(int(r["id"] or 0) for r in db.select("t"))


def _write_history(folder: str) -> list[list[int]]:
    """Make twelve commits, and return the table's ids after each one."""
    db = _open(folder)
    states = [_ids(db)]
    for i in range(12):
        if i % 4 == 3:
            db.delete("t", {"id": i - 2})
        else:
            db.insert("t", {"id": i, "v": "x" * i})
        states.append(_ids(db))
    db.close()
    return states


class CrashTests(unittest.TestCase):
    def test_every_truncation_recovers_a_prefix(self) -> None:
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        states = _write_history(folder)
        log = (Path(folder) / "wal.log").read_bytes()
        for cut in range(0, len(log) + 1, 3):
            copy = tempfile.mkdtemp()
            try:
                (Path(copy) / "wal.log").write_bytes(log[:cut])
                recovered = _open(copy)
                assert _ids(recovered) == states[recovered.commit_seq], f"cut at byte {cut}"
                recovered.close()
            finally:
                shutil.rmtree(copy)


if __name__ == "__main__":
    unittest.main()
```

---

[🏠 Contents](index.md) · [Next: Appendix D — Answers to the Exercises →](appendix-d-answers.md)
