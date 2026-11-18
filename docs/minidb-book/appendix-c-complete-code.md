[🏠 Contents](index.md) · [← Previous: Appendix B — Testing a Database](appendix-b-testing.md)

# Appendix C — The Complete Code

This is minidb as it stands at the end of the book: 17 modules and the test suite, 3,731 lines in total. It's the exact code that the book's examples were run against, assembled chapter by chapter from the listings. It needs Python 3.14 (3.13 also works) and nothing outside the standard library.

To use it, recreate the files under a project directory:

```text
minidb-project/
├── minidb/
│   ├── __init__.py
│   ├── errors.py
│   ├── types.py
│   ├── normalizers.py
│   ├── schema.py
│   ├── index.py
│   ├── btree.py
│   ├── table.py
│   ├── changes.py
│   ├── query.py
│   ├── expr.py
│   ├── planner.py
│   ├── locks.py
│   ├── uow.py
│   ├── storage.py
│   ├── database.py
│   ├── sql.py
└── tests/
    ├── __init__.py   (empty)
    └── test_minidb.py
```

| File | Contents | Main chapter | Lines |
|---|---|---|---|
| [`minidb/__init__.py`](#minidb__init__py) | Package exports | – | 31 |
| [`minidb/errors.py`](#minidberrorspy) | Exceptions | [Ch. 2](02-tables-and-crud.md) | 37 |
| [`minidb/types.py`](#minidbtypespy) | Column types | [Ch. 3](03-types-and-normalization.md) | 234 |
| [`minidb/normalizers.py`](#minidbnormalizerspy) | Value normalizers | [Ch. 3](03-types-and-normalization.md) | 29 |
| [`minidb/schema.py`](#minidbschemapy) | Columns, checks, keys, foreign keys | [Ch. 4](04-constraints.md) | 166 |
| [`minidb/index.py`](#minidbindexpy) | Hash and sorted indexes | [Ch. 5](05-keys-and-indexes.md) | 99 |
| [`minidb/btree.py`](#minidbbtreepy) | B+ tree and B-tree index | [Ch. 15](15-b-trees.md) | 176 |
| [`minidb/table.py`](#minidbtablepy) | Table storage | [Ch. 8](08-unit-of-work-i.md) | 138 |
| [`minidb/changes.py`](#minidbchangespy) | Planning and validating changes | [Ch. 8](08-unit-of-work-i.md) | 179 |
| [`minidb/query.py`](#minidbquerypy) | Query operators and builder | [Ch. 7](07-query-primitives.md) | 376 |
| [`minidb/expr.py`](#minidbexprpy) | Expression trees | [Ch. 14](14-query-planning.md) | 226 |
| [`minidb/planner.py`](#minidbplannerpy) | Cost-based planner | [Ch. 14](14-query-planning.md) | 305 |
| [`minidb/locks.py`](#minidblockspy) | Readers–writer locks | [Ch. 11](11-readers-writer-locks.md) | 138 |
| [`minidb/uow.py`](#minidbuowpy) | Unit of Work | [Ch. 12](12-isolation.md) | 355 |
| [`minidb/storage.py`](#minidbstoragepy) | Formats, snapshot and write-ahead log | [Ch. 13](13-persistence.md) | 145 |
| [`minidb/database.py`](#minidbdatabasepy) | The Database façade | [Ch. 13](13-persistence.md) | 245 |
| [`minidb/sql.py`](#minidbsqlpy) | SQL front end | [App. A](appendix-a-sql-parser.md) | 635 |
| [`tests/test_minidb.py`](#teststest_minidbpy) | Test suite | [App. B](appendix-b-testing.md) | 217 |

## `minidb/__init__.py`

Package exports. Through the book this file grew by a few appended lines per chapter. Here the same imports are consolidated in one place.

```python
"""minidb: a small relational database, built in the book."""
from minidb import normalizers
from minidb.changes import Change
from minidb.database import Database
from minidb.errors import (CheckViolation, ConflictError, ConstraintError, DatabaseError,
                           DomainError, ForeignKeyViolation, NotNullViolation, SchemaError,
                           UniqueViolation)
from minidb.expr import Expr, col, lit
from minidb.locks import FairRWLock
from minidb.query import Avg, Count, Max, Min, Query, Sum
from minidb.schema import Check, Column, ForeignKey, TableSchema
from minidb.sql import Connection, SQLError, connect
from minidb.storage import Format, JsonFormat, Storage
from minidb.types import Boolean, Date, Integer, Numeric, Real, Text, Timestamp
from minidb.uow import Record, TransactionError, UnitOfWork

__all__ = [
    # the database and its transactions
    "Database", "UnitOfWork", "Record", "Change", "FairRWLock",
    # schema
    "Column", "Check", "ForeignKey", "TableSchema", "normalizers",
    "Integer", "Real", "Text", "Boolean", "Numeric", "Date", "Timestamp",
    # queries
    "Query", "Expr", "col", "lit", "Count", "Sum", "Avg", "Min", "Max",
    # persistence and SQL
    "Storage", "Format", "JsonFormat", "connect", "Connection",
    # errors
    "DatabaseError", "SchemaError", "ConstraintError", "DomainError", "NotNullViolation",
    "CheckViolation", "UniqueViolation", "ForeignKeyViolation", "ConflictError",
    "TransactionError", "SQLError",
]
```

## `minidb/errors.py`

Exceptions. Developed in [Chapter 2](02-tables-and-crud.md).

```python
"""Exceptions raised by minidb."""


class DatabaseError(Exception):
    """Base class for every error minidb raises on purpose."""


class SchemaError(DatabaseError):
    """A table or column does not exist, or a definition is invalid."""


class ConstraintError(DatabaseError):
    """Data was rejected because it violates a rule of the schema."""


class DomainError(ConstraintError):
    """A value does not belong to its column's type (domain)."""


class NotNullViolation(ConstraintError):
    """A NOT NULL column received NULL."""


class CheckViolation(ConstraintError):
    """A CHECK constraint evaluated to false."""


class UniqueViolation(ConstraintError):
    """A PRIMARY KEY or UNIQUE constraint would be violated."""


class ForeignKeyViolation(ConstraintError):
    """A reference points at a missing row, or a delete would orphan rows."""


class ConflictError(DatabaseError):
    """A concurrent transaction changed something this one read. Retry it."""
```

## `minidb/types.py`

Column types. Developed in [Chapter 3](03-types-and-normalization.md).

```python
"""Column types. Each type knows how to normalize and validate its values."""
import datetime as dt
import math
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

from minidb.errors import DomainError

_INT_RE = re.compile(r"[+-]?\d+")


class Type:
    """Base class for column types.

    normalize(): turn an acceptable input into the canonical stored form.
    validate():  check that a value already is in canonical form.
    NULL (None) passes through both untouched; NOT NULL is a constraint,
    not a type (see Chapter 4).
    """
    exact_types: tuple[type, ...] = (object,)

    def normalize(self, value):
        if value is None:
            return None
        return self.coerce(value)

    def coerce(self, value):
        """Override: convert `value` or call self.reject(value)."""
        return value

    def validate(self, value) -> None:
        if value is None:
            return
        if object not in self.exact_types and type(value) not in self.exact_types:
            self.reject(value)
        self.check(value)

    def check(self, value) -> None:
        """Override: extra domain rules such as ranges and lengths."""

    def reject(self, value, reason: str = ""):
        raise DomainError(f"{value!r} is not a valid {self!r}"
                          + (f": {reason}" if reason else ""))

    def to_primitive(self, value):
        """A canonical value as something any Format can store."""
        return value

    def from_primitive(self, value):
        value = self.normalize(value)
        self.validate(value)
        return value


@dataclass(frozen=True)
class Integer(Type):
    min: int | None = None
    max: int | None = None
    exact_types = (int,)

    def coerce(self, value):
        match value:
            case bool():
                self.reject(value, "booleans are not integers")
            case int():
                return value
            case float() if value.is_integer():
                return int(value)
            case Decimal() if value.is_finite() and value == value.to_integral_value():
                return int(value)
            case str() if _INT_RE.fullmatch(value.strip()):
                return int(value.strip())
        self.reject(value)

    def check(self, value):
        if self.min is not None and value < self.min:
            self.reject(value, f"below minimum {self.min}")
        if self.max is not None and value > self.max:
            self.reject(value, f"above maximum {self.max}")


@dataclass(frozen=True)
class Real(Type):
    exact_types = (float,)

    def coerce(self, value):
        match value:
            case bool():
                self.reject(value, "booleans are not numbers")
            case int() | float() | Decimal():
                result = float(value)
            case str():
                try:
                    result = float(value.strip())
                except ValueError:
                    self.reject(value)
            case _:
                self.reject(value)
        return result

    def check(self, value):
        if not math.isfinite(value):
            self.reject(value, "NaN and infinities are not allowed")


@dataclass(frozen=True)
class Text(Type):
    max_length: int | None = None
    exact_types = (str,)

    def coerce(self, value):
        if not isinstance(value, str):
            self.reject(value, "no implicit conversion to text")
        return value

    def check(self, value):
        if self.max_length is not None and len(value) > self.max_length:
            self.reject(value, f"longer than {self.max_length} characters")


_TRUE = {"true", "t", "yes", "y", "on", "1"}
_FALSE = {"false", "f", "no", "n", "off", "0"}


@dataclass(frozen=True)
class Boolean(Type):
    exact_types = (bool,)

    def coerce(self, value):
        match value:
            case bool():
                return value
            case 0 | 1:
                return bool(value)
            case str() if value.strip().lower() in _TRUE:
                return True
            case str() if value.strip().lower() in _FALSE:
                return False
        self.reject(value)


@dataclass(frozen=True)
class Numeric(Type):
    """Exact decimal with `precision` total digits, `scale` after the point."""
    precision: int = 18
    scale: int = 2
    exact_types = (Decimal,)

    def __post_init__(self):
        if not 0 <= self.scale <= self.precision:
            raise ValueError("need 0 <= scale <= precision")

    def coerce(self, value):
        match value:
            case bool():
                self.reject(value)
            case float():
                value = Decimal(repr(value))     # 0.1 -> Decimal('0.1')
            case int() | Decimal():
                value = Decimal(value)
            case str():
                try:
                    value = Decimal(value.strip())
                except InvalidOperation:
                    self.reject(value)
            case _:
                self.reject(value)
        if not value.is_finite():
            self.reject(value, "NaN and infinities are not allowed")
        return value.quantize(Decimal(1).scaleb(-self.scale), ROUND_HALF_EVEN)

    def check(self, value):
        if value.as_tuple().exponent != -self.scale:
            self.reject(value, f"expected exactly {self.scale} decimal places")
        digits_before_point = max(value.adjusted() + 1, 0)
        if digits_before_point > self.precision - self.scale:
            self.reject(value, f"too many digits for NUMERIC({self.precision}, {self.scale})")

    def to_primitive(self, value):
        return None if value is None else str(value)       # exact, unlike float


@dataclass(frozen=True)
class Date(Type):
    exact_types = (dt.date,)

    def coerce(self, value):
        match value:
            case dt.datetime():
                self.reject(value, "use .date() to drop the time explicitly")
            case dt.date():
                return value
            case str():
                try:
                    return dt.date.fromisoformat(value.strip())
                except ValueError:
                    self.reject(value)
        self.reject(value)

    def to_primitive(self, value):
        return None if value is None else value.isoformat()


@dataclass(frozen=True)
class Timestamp(Type):
    """A datetime. With with_timezone=True, values must be aware and are
    stored in UTC; otherwise they must be naive."""
    with_timezone: bool = True
    exact_types = (dt.datetime,)

    def coerce(self, value):
        if isinstance(value, str):
            try:
                value = dt.datetime.fromisoformat(value.strip())
            except ValueError:
                self.reject(value)
        if not isinstance(value, dt.datetime):
            self.reject(value)
        aware = value.tzinfo is not None and value.utcoffset() is not None
        if self.with_timezone:
            if not aware:
                self.reject(value, "a timezone is required")
            return value.astimezone(dt.UTC)
        if aware:
            self.reject(value, "timezone not allowed")
        return value

    def check(self, value):
        if self.with_timezone and value.utcoffset() != dt.timedelta(0):
            self.reject(value, "must be stored in UTC")

    def to_primitive(self, value):
        return None if value is None else value.isoformat()
```

## `minidb/normalizers.py`

Value normalizers. Developed in [Chapter 3](03-types-and-normalization.md).

```python
"""Small value normalizers for Column(normalizers=...).

Every normalizer must be idempotent: f(f(x)) == f(x). Rows are re-normalized
whenever they are updated, so a non-idempotent normalizer would change data
that nobody touched.
"""
import unicodedata


def strip(s: str) -> str:
    return s.strip()


def lower(s: str) -> str:
    return s.lower()


def upper(s: str) -> str:
    return s.upper()


def collapse_spaces(s: str) -> str:
    """'  Ada   Lovelace ' -> 'Ada Lovelace'"""
    return " ".join(s.split())


def nfc(s: str) -> str:
    """Unicode NFC: one canonical byte sequence for visually equal text."""
    return unicodedata.normalize("NFC", s)
```

## `minidb/schema.py`

Columns, checks, keys, foreign keys. Developed in [Chapter 4](04-constraints.md).

```python
"""Declarative table definitions."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from minidb.errors import DomainError, SchemaError
from minidb.types import Type
from types import MappingProxyType
from minidb.errors import CheckViolation, NotNullViolation
from collections.abc import Iterable
from dataclasses import replace

type Row = dict[str, object]


_NO_DEFAULT = object()


@dataclass(frozen=True)
class Column:
    name: str
    type: Type
    normalizers: tuple[Callable[[object], object], ...] = ()
    nullable: bool = True
    default: object = None          # a value, or a zero-argument callable
    check: Callable[[object], bool | None] | None = None

    def make_default(self):
        return self.default() if callable(self.default) else self.default

    def prepare(self, value):
        """Normalize, then validate one value. Raises DomainError."""
        value = self.type.normalize(value)
        if value is not None:
            for fn in self.normalizers:
                value = fn(value)
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
    primary_key: tuple[str, ...] = ()                       # new
    unique: tuple[tuple[str, ...], ...] = ()                # new
    by_name: Mapping[str, Column] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        pk = _as_key(self.primary_key)
        unique = tuple(_as_key(u) for u in self.unique)
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise SchemaError(f"duplicate column names in {self.name!r}")
        for key in (pk, *unique):
            missing = set(key) - set(names)
            if missing:
                raise SchemaError(f"{self.name}: key uses unknown column(s) {sorted(missing)}")
        # entity integrity: primary-key columns are implicitly NOT NULL
        columns = tuple(replace(c, nullable=False) if c.name in pk else c
                        for c in self.columns)
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "checks", tuple(self.checks))
        object.__setattr__(self, "primary_key", pk)
        object.__setattr__(self, "unique", unique)
        object.__setattr__(self, "by_name", {c.name: c for c in columns})

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns)

    def column(self, name: str) -> Column:
        try:
            return self.by_name[name]
        except KeyError:
            raise SchemaError(f"{self.name}: no such column {name!r}") from None

    def prepare_row(self, values: Mapping[str, object],
                    base: Row | None = None) -> Row:
        """Run the constraint pipeline; return a complete, valid row.

        `values` are the user's input; `base` is the existing row for an
        update (None for an insert). Neither argument is modified.
        """
        for name in values:
            self.column(name)                                # unknown column?
        if base is None:                                     # insert
            row = {c.name: values[c.name] if c.name in values else c.make_default()
                   for c in self.columns}
            touched = self.column_names
        else:                                                # update
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


def _as_key(columns: str | Iterable[str]) -> tuple[str, ...]:
    """'id' -> ('id',);  ['a', 'b'] -> ('a', 'b')"""
    return (columns,) if isinstance(columns, str) else tuple(columns)


ON_DELETE_ACTIONS = ("restrict", "cascade", "set null")


@dataclass(frozen=True)
class ForeignKey:
    """`table.columns` must match `ref_table.ref_columns` (a key) or be NULL."""
    columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...] = ()     # empty: the referenced primary key
    on_delete: str = "restrict"
    table: str = ""                       # the child table; set by create_table

    def __post_init__(self):
        object.__setattr__(self, "columns", _as_key(self.columns))
        object.__setattr__(self, "ref_columns", _as_key(self.ref_columns))
        if self.on_delete not in ON_DELETE_ACTIONS:
            raise SchemaError(f"on_delete must be one of {ON_DELETE_ACTIONS}")

    @property
    def name(self) -> str:
        return f"fk_{self.table}_{'_'.join(self.columns)}"

    def parent_key(self, child_row) -> dict[str, object] | None:
        """{ref_column: value} for the parent this child points at, or None."""
        values = [child_row[c] for c in self.columns]
        if any(v is None for v in values):
            return None                   # NULL references nothing (MATCH SIMPLE)
        return dict(zip(self.ref_columns, values))

    def child_key(self, parent_row) -> dict[str, object]:
        """{column: value} that children of `parent_row` have."""
        return {c: parent_row[r] for c, r in zip(self.columns, self.ref_columns)}
```

## `minidb/index.py`

Hash and sorted indexes. Developed in [Chapter 5](05-keys-and-indexes.md).

```python
"""Secondary structures mapping column values to rowids."""
from collections.abc import Iterable, Mapping
import bisect
import itertools
import math

type Key = tuple


class HashIndex:
    """Equality index: key tuple -> set of rowids. NULL keys are not indexed."""
    kind = "hash"

    def __init__(self, name: str, columns: Iterable[str], unique: bool = False):
        self.name = name
        self.columns = tuple(columns)
        self.unique = unique
        self._entries: dict[Key, set[int]] = {}

    def key_of(self, row: Mapping[str, object]) -> Key | None:
        key = tuple(row[c] for c in self.columns)
        return None if any(v is None for v in key) else key

    def add(self, rowid: int, row: Mapping[str, object]) -> None:
        key = self.key_of(row)
        if key is not None:
            self._entries.setdefault(key, set()).add(rowid)

    def remove(self, rowid: int, row: Mapping[str, object]) -> None:
        key = self.key_of(row)
        if key is None:
            return
        ids = self._entries.get(key)
        if ids is not None:
            ids.discard(rowid)
            if not ids:
                del self._entries[key]       # don't keep empty buckets around

    def lookup(self, key: Key) -> set[int]:
        return set(self._entries.get(tuple(key), ()))

    def distinct_keys(self) -> int:
        return len(self._entries)

    def __repr__(self):
        u = "unique " if self.unique else ""
        return f"<{u}{self.kind} index {self.name} on {self.columns}>"


class SortedIndex(HashIndex):
    """Ordered index: a sorted list of (key, rowid). Supports ranges."""
    kind = "sorted"

    def __init__(self, name: str, columns: Iterable[str], unique: bool = False):
        super().__init__(name, columns, unique)
        self._sorted: list[tuple[Key, int]] = []

    def add(self, rowid: int, row: Mapping[str, object]) -> None:
        key = self.key_of(row)
        if key is not None:
            bisect.insort(self._sorted, (key, rowid))      # O(n): the list shifts

    def remove(self, rowid: int, row: Mapping[str, object]) -> None:
        key = self.key_of(row)
        if key is None:
            return
        i = bisect.bisect_left(self._sorted, (key, rowid))
        if i < len(self._sorted) and self._sorted[i] == (key, rowid):
            del self._sorted[i]

    def lookup(self, key: Key) -> set[int]:
        key = tuple(key)
        i = bisect.bisect_left(self._sorted, (key,))       # (key,) sorts before (key, any)
        found = set()
        while i < len(self._sorted) and self._sorted[i][0] == key:
            found.add(self._sorted[i][1])
            i += 1
        return found

    def range(self, lo: Key | None, hi: Key | None,
              lo_inclusive: bool = True, hi_inclusive: bool = True) -> list[int]:
        """Rowids with lo <= key <= hi (bounds optional), in key order."""
        if lo is None:
            i = 0
        elif lo_inclusive:
            i = bisect.bisect_left(self._sorted, (lo,))
        else:
            i = bisect.bisect_right(self._sorted, (lo, math.inf))
        found = []
        while i < len(self._sorted):
            key, rowid = self._sorted[i]
            if hi is not None and (key > hi or (key == hi and not hi_inclusive)):
                break
            found.append(rowid)
            i += 1
        return found

    def distinct_keys(self) -> int:
        return sum(1 for _ in itertools.groupby(self._sorted, key=lambda e: e[0]))
```

## `minidb/btree.py`

B+ tree and B-tree index. Developed in [Chapter 15](15-b-trees.md).

```python
"""An in-memory B+ tree, and an index built on it.

Internal nodes hold separator keys and children; leaves hold keys, their
values (sets of rowids) and a link to the next leaf, so range scans walk
the leaf level without going back up the tree.
"""
import bisect
from collections.abc import Iterable, Iterator, Mapping

from minidb.index import HashIndex, Key


class _Leaf:
    __slots__ = ("keys", "values", "next")

    def __init__(self):
        self.keys: list = []
        self.values: list[set[int]] = []
        self.next: "_Leaf | None" = None


class _Internal:
    __slots__ = ("keys", "children")

    def __init__(self, keys: list, children: list):
        self.keys = keys            # keys[i] is the smallest key under children[i + 1]
        self.children = children    # always len(keys) + 1 of them


class BPlusTree:
    """Maps keys to sets of ints. `order` = maximum children per node."""

    def __init__(self, order: int = 64):
        if order < 3:
            raise ValueError("order must be at least 3")
        self.order = order
        self.root: _Leaf | _Internal = _Leaf()
        self._len = 0

    def __len__(self) -> int:
        """Number of distinct keys."""
        return self._len

    @property
    def height(self) -> int:
        node, h = self.root, 1
        while isinstance(node, _Internal):
            node, h = node.children[0], h + 1
        return h

    # -- search ---------------------------------------------------------------------------
    def _descend(self, key) -> tuple[_Leaf, list[_Internal]]:
        """The leaf where `key` belongs, plus the internal nodes on the way."""
        node, path = self.root, []
        while isinstance(node, _Internal):
            path.append(node)
            node = node.children[bisect.bisect_right(node.keys, key)]
        return node, path

    def get(self, key) -> set[int]:
        leaf, _ = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            return set(leaf.values[i])
        return set()

    def items(self, lo=None, hi=None, lo_inclusive: bool = True,
              hi_inclusive: bool = True) -> Iterator[tuple[object, set[int]]]:
        """(key, values) for keys between lo and hi, in order, walking the leaves."""
        if lo is None:
            leaf = self.root
            while isinstance(leaf, _Internal):
                leaf = leaf.children[0]
            i = 0
        else:
            leaf, _ = self._descend(lo)
            i = (bisect.bisect_left if lo_inclusive else bisect.bisect_right)(leaf.keys, lo)
        while leaf is not None:
            while i < len(leaf.keys):
                key = leaf.keys[i]
                if hi is not None and (key > hi or (key == hi and not hi_inclusive)):
                    return
                yield key, leaf.values[i]
                i += 1
            leaf, i = leaf.next, 0

    # -- insert ---------------------------------------------------------------------------
    def insert(self, key, value: int) -> None:
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

    def _split_leaf(self, leaf: _Leaf, path: list[_Internal]) -> None:
        mid = len(leaf.keys) // 2
        right = _Leaf()
        right.keys, leaf.keys = leaf.keys[mid:], leaf.keys[:mid]
        right.values, leaf.values = leaf.values[mid:], leaf.values[:mid]
        right.next, leaf.next = leaf.next, right
        self._insert_in_parent(leaf, right.keys[0], right, path)

    def _insert_in_parent(self, left, separator, right, path: list[_Internal]) -> None:
        if not path:                                     # the root split: grow upwards
            self.root = _Internal([separator], [left, right])
            return
        parent = path.pop()
        i = parent.children.index(left)
        parent.keys.insert(i, separator)
        parent.children.insert(i + 1, right)
        if len(parent.children) > self.order:
            mid = len(parent.keys) // 2
            up = parent.keys[mid]
            sibling = _Internal(parent.keys[mid + 1:], parent.children[mid + 1:])
            parent.keys, parent.children = parent.keys[:mid], parent.children[:mid + 1]
            self._insert_in_parent(parent, up, sibling, path)

    # -- delete ---------------------------------------------------------------------------
    def remove(self, key, value: int) -> None:
        """Remove `value` from `key`; drop the key when its set is empty.

        Nodes are never merged ("lazy deletion"): simple, and fine for
        workloads that insert more than they delete. See the exercises.
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
        lines, level = [], [self.root]
        while level:
            lines.append("   ".join(
                "[" + " ".join(map(str, n.keys)) + "]" for n in level))
            level = [c for n in level if isinstance(n, _Internal) for c in n.children]
        return "\n".join(lines)


class BTreeIndex(HashIndex):
    """An ordered index on a B+ tree: O(log n) inserts, lookups and range starts."""
    kind = "btree"

    def __init__(self, name: str, columns: Iterable[str], unique: bool = False,
                 order: int = 64):
        super().__init__(name, columns, unique)
        self.tree = BPlusTree(order)

    def add(self, rowid: int, row: Mapping[str, object]) -> None:
        key = self.key_of(row)
        if key is not None:
            self.tree.insert(key, rowid)

    def remove(self, rowid: int, row: Mapping[str, object]) -> None:
        key = self.key_of(row)
        if key is not None:
            self.tree.remove(key, rowid)

    def lookup(self, key: Key) -> set[int]:
        return self.tree.get(tuple(key))

    def range(self, lo: Key | None, hi: Key | None,
              lo_inclusive: bool = True, hi_inclusive: bool = True) -> list[int]:
        return [rowid for _, rowids in self.tree.items(lo, hi, lo_inclusive, hi_inclusive)
                for rowid in sorted(rowids)]

    def distinct_keys(self) -> int:
        return len(self.tree)
```

## `minidb/table.py`

Table storage. Developed in [Chapter 8](08-unit-of-work-i.md).

```python
"""In-memory storage for one table: rows by rowid, plus indexes.

Table does no validation; see changes.py for that.
"""
from collections.abc import Callable, Iterable, Iterator, Mapping
from types import MappingProxyType

from minidb.errors import SchemaError, UniqueViolation
from minidb.index import HashIndex
from minidb.schema import TableSchema
import threading
from minidb.index import SortedIndex
from minidb.btree import BTreeIndex
INDEX_KINDS = {"hash": HashIndex, "sorted": SortedIndex}

type Row = dict[str, object]
type Predicate = Callable[[Mapping[str, object]], bool]
type Where = Predicate | Mapping[str, object] | None


class Table:
    def __init__(self, schema: TableSchema):
        self.schema = schema
        self.name = schema.name
        self.columns = schema.column_names
        self.rows: dict[int, Row] = {}
        self.indexes: dict[str, HashIndex] = {}
        self.version = 0                          # last commit that changed this table
        self.row_versions: dict[int, int] = {}    # rowid -> last commit that changed it
        self._next_rowid = 1
        self._rowid_latch = threading.Lock()
        if schema.primary_key:
            self.create_index("pk", schema.primary_key, unique=True)
        for cols in schema.unique:
            self.create_index("unique_" + "_".join(cols), cols, unique=True)

    def __len__(self) -> int:
        return len(self.rows)

    # -- indexes -------------------------------------------------------------------
    def create_index(self, name: str, columns: Iterable[str], unique: bool = False,
                     kind: str = "hash") -> HashIndex:
        if name in self.indexes:
            raise SchemaError(f"{self.name}: index {name!r} already exists")
        columns = tuple(columns)
        for c in columns:
            self.schema.column(c)
        index = INDEX_KINDS[kind](name, columns, unique)
        for rowid, row in self.rows.items():
            if unique and (key := index.key_of(row)) and index.lookup(key):
                raise UniqueViolation(
                    f"{self.name}: cannot create unique index {name!r}: "
                    f"duplicate key {key}")
            index.add(rowid, row)
        self.indexes[name] = index
        return index

    def range(self, column: str, lo=None, hi=None,
              lo_inclusive: bool = True, hi_inclusive: bool = True) -> list[int]:
        """Rowids with lo <= column <= hi, via an ordered index on that column."""
        index = next((i for i in self.indexes.values()
                      if i.columns == (column,) and i.kind != "hash"), None)
        if index is None:
            raise SchemaError(f"{self.name}: no ordered index on {column!r}")
        return index.range(None if lo is None else (lo,), None if hi is None else (hi,),
                           lo_inclusive, hi_inclusive)

    def index_on(self, columns: Iterable[str]) -> HashIndex | None:
        wanted = set(columns)
        return next((i for i in self.indexes.values() if set(i.columns) == wanted), None)

    def unique_keys(self) -> list[tuple[str, ...]]:
        return [i.columns for i in self.indexes.values() if i.unique]

    # -- primitives: no validation ---------------------------------------------------
    def put(self, rowid: int, row: Row) -> None:
        old = self.rows.get(rowid)
        for index in self.indexes.values():
            if old is not None:
                index.remove(rowid, old)
            index.add(rowid, row)
        self.rows[rowid] = row

    def remove(self, rowid: int) -> None:
        old = self.rows.pop(rowid)
        for index in self.indexes.values():
            index.remove(rowid, old)

    def new_rowid(self) -> int:
        with self._rowid_latch:
            rowid = self._next_rowid
            self._next_rowid += 1
            return rowid

    # -- reads -------------------------------------------------------------------------
    def row(self, rowid: int) -> Row:
        """The stored row itself (KeyError if absent). Never mutate it."""
        return self.rows[rowid]

    def get(self, rowid: int) -> Row | None:
        row = self.rows.get(rowid)
        return dict(row) if row is not None else None

    def scan(self) -> Iterator[tuple[int, Row]]:
        for rowid, row in self.rows.items():
            yield rowid, dict(row)

    def lookup(self, key: Mapping[str, object]) -> set[int]:
        """Rowids whose columns equal `key`, using an index on exactly those columns."""
        index = self.index_on(key)
        if index is None:
            raise SchemaError(f"{self.name}: no index on {sorted(key)}")
        return index.lookup(tuple(key[c] for c in index.columns))

    def match(self, where: Where = None) -> list[int]:
        if where is None:
            return list(self.rows)
        if callable(where):
            return [rid for rid, row in self.rows.items()
                    if where(MappingProxyType(row))]
        return self._match_equal(where)

    def _match_equal(self, equal: Mapping[str, object]) -> list[int]:
        wanted = {c: self.schema.column(c).prepare(v) for c, v in equal.items()}
        best = max((i for i in self.indexes.values() if set(i.columns) <= set(wanted)),
                   key=lambda i: len(i.columns), default=None)
        if best is not None:
            candidates = best.lookup(tuple(wanted[c] for c in best.columns))
        else:
            candidates = self.rows.keys()
        return [rid for rid in candidates
                if all(self.rows[rid][c] == v and v is not None for c, v in wanted.items())]

    def select(self, where: Where = None) -> list[Row]:
        return [dict(self.rows[rid]) for rid in self.match(where)]


INDEX_KINDS["btree"] = BTreeIndex
```

## `minidb/changes.py`

Planning and validating changes. Developed in [Chapter 8](08-unit-of-work-i.md).

```python
"""Planning writes: turn operations into validated lists of Changes.

Planners read from a *state* (anything with .table(name) and
.foreign_keys) and never modify it.
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from minidb.errors import ForeignKeyViolation, UniqueViolation
from minidb.schema import ForeignKey

type Row = dict[str, object]


@dataclass(frozen=True)
class Change:
    """In `table`, row `rowid` went from `before` to `after` (None = absent)."""
    table: str
    rowid: int
    before: Row | None
    after: Row | None

    @property
    def kind(self) -> str:
        if self.before is None:
            return "insert"
        return "delete" if self.after is None else "update"

    def inverted(self) -> "Change":
        return Change(self.table, self.rowid, self.after, self.before)


# -- the three operations --------------------------------------------------------------
def plan_insert(state, table: str, values: Mapping[str, object], *,
                check: bool = True) -> list[Change]:
    t = state.table(table)
    row = t.schema.prepare_row(values)
    if check:
        check_unique(t, [(None, row)])
        check_parents_exist(state, t, [row])
    return [Change(table, t.new_rowid(), None, row)]


def plan_update(state, table: str, changes: Mapping[str, object], where=None, *,
                rowids: Iterable[int] | None = None, check: bool = True) -> list[Change]:
    t = state.table(table)
    targets = t.match(where) if rowids is None else rowids
    old = {rid: t.row(rid) for rid in targets}
    new = {rid: t.schema.prepare_row(changes, base=row) for rid, row in old.items()}
    if check:
        check_unique(t, list(new.items()))
        check_parents_exist(state, t, new.values())
        check_no_orphans(state, t, old, new)
    return [Change(table, rid, old[rid], new[rid]) for rid in new]


def plan_delete(state, table: str, where=None, *,
                rowids: Iterable[int] | None = None, check: bool = True) -> list[Change]:
    """A delete and everything it implies (cascades, SET NULL), or raise."""
    t = state.table(table)
    targets = t.match(where) if rowids is None else rowids
    deleted: dict[tuple[str, int], Row] = {}
    stack = [(table, rid) for rid in targets]
    while stack:
        name, rid = stack.pop()
        if (name, rid) in deleted:
            continue
        row = deleted[(name, rid)] = state.table(name).row(rid)
        for fk in references_to(state, name):
            if fk.on_delete == "cascade":
                stack.extend((fk.table, c) for c in children(state, fk, row))
    nulled: dict[tuple[str, int], tuple[Row, Row]] = {}
    for (name, rid), row in deleted.items():
        for fk in references_to(state, name):
            child = state.table(fk.table)
            survivors = [c for c in children(state, fk, row)
                         if (fk.table, c) not in deleted]
            if not survivors:
                continue
            if fk.on_delete == "restrict" and check:
                raise ForeignKeyViolation(
                    f"{fk.name}: {name} row {fk.child_key(row)} is still "
                    f"referenced by {len(survivors)} {fk.table} row(s)")
            if fk.on_delete == "set null":
                for c in survivors:
                    before = child.row(c)
                    base = nulled.get((fk.table, c), (before, before))[1]
                    after = child.schema.prepare_row(dict.fromkeys(fk.columns), base=base)
                    nulled[(fk.table, c)] = (before, after)
    return ([Change(n, rid, row, None) for (n, rid), row in deleted.items()] +
            [Change(n, rid, b, a) for (n, rid), (b, a) in nulled.items()])


# -- constraint checks -------------------------------------------------------------------
def check_unique(t, batch: list[tuple[int | None, Row]]) -> None:
    """No two rows may share a unique key after applying `batch`.

    `batch` pairs each rowid (None for a new row) with the row it will hold.
    """
    changing = {rid for rid, _ in batch if rid is not None}
    for columns in t.unique_keys():
        seen: set[tuple] = set()
        for _, row in batch:
            key = tuple(row[c] for c in columns)
            if any(v is None for v in key):
                continue
            if key in seen or t.lookup(dict(zip(columns, key))) - changing:
                shown = ", ".join(f"{c}={v!r}" for c, v in zip(columns, key))
                raise UniqueViolation(f"{t.name}: duplicate key ({shown})")
            seen.add(key)


def references_from(state, table: str) -> list[ForeignKey]:
    return [fk for fk in state.foreign_keys if fk.table == table]


def references_to(state, table: str) -> list[ForeignKey]:
    return [fk for fk in state.foreign_keys if fk.ref_table == table]


def children(state, fk: ForeignKey, parent_row: Row) -> set[int]:
    return state.table(fk.table).lookup(fk.child_key(parent_row))


def check_parents_exist(state, child, rows: Iterable[Row],
                        fks: list[ForeignKey] | None = None) -> None:
    for fk in fks if fks is not None else references_from(state, child.name):
        parent = state.table(fk.ref_table)
        for row in rows:
            key = fk.parent_key(row)
            if key is not None and not parent.lookup(key):
                raise ForeignKeyViolation(f"{fk.name}: no {parent.name} row with {key}")


def check_no_orphans(state, parent, old: dict[int, Row], new: dict[int, Row]) -> None:
    for fk in references_to(state, parent.name):
        for rid, before in old.items():
            if fk.child_key(before) != fk.child_key(new[rid]) and children(state, fk, before):
                raise ForeignKeyViolation(
                    f"{fk.name}: cannot change {parent.name} key "
                    f"{fk.child_key(before)}, it is still referenced")


def net_changes(changes: Iterable[Change]) -> list[Change]:
    """Collapse a sequence of changes to one per row: first before, last after."""
    net: dict[tuple[str, int], Change] = {}
    for c in changes:
        key = (c.table, c.rowid)
        if key in net:
            net[key] = Change(c.table, c.rowid, net[key].before, c.after)
        else:
            net[key] = c
    return [c for c in net.values() if c.before is not None or c.after is not None]


def check_deferred(state, changes: Iterable[Change]) -> None:
    """Multi-row constraints over a transaction's net effect, in its final state."""
    by_table: dict[str, list[Change]] = {}
    for c in net_changes(changes):
        by_table.setdefault(c.table, []).append(c)
    for name, cs in by_table.items():
        t = state.table(name)
        written = [(c.rowid, c.after) for c in cs if c.after is not None]
        check_unique(t, written)
        check_parents_exist(state, t, [row for _, row in written])
        for c in cs:
            if c.before is not None:
                check_not_dangling(state, t, c.before)


def check_not_dangling(state, parent, old_row: Row) -> None:
    """If `old_row`'s key is gone, nothing may still reference it."""
    for fk in references_to(state, parent.name):
        key = {r: old_row[r] for r in fk.ref_columns}
        if any(v is None for v in key.values()) or parent.lookup(key):
            continue                          # NULL key, or a row still has it
        if children(state, fk, old_row):
            raise ForeignKeyViolation(
                f"{fk.name}: {parent.name} row {key} is gone but still referenced")
```

## `minidb/query.py`

Query operators and builder. Developed in [Chapter 7](07-query-primitives.md).

```python
"""Query operators (the iterator model) and a fluent query builder."""
import itertools
from collections.abc import Callable, Iterator
from typing import Any


class Row(dict):
    """A result row keyed by qualified names ('u.age').

    Unqualified names ('age') also work when they are unambiguous.
    """

    def __missing__(self, key: str):
        if "." not in key:
            found = [k for k in self if k.rpartition(".")[2] == key]
            if len(found) == 1:
                return self[found[0]]
            if found:
                raise KeyError(f"ambiguous column {key!r}: one of {sorted(found)}")
        raise KeyError(key)


class Operator:
    """Base class. Subclasses implement __iter__, columns() and label."""
    children: tuple["Operator", ...] = ()

    def __iter__(self) -> Iterator[Row]:
        raise NotImplementedError

    def columns(self) -> list[str]:
        return self.children[0].columns()

    @property
    def label(self) -> str:
        return type(self).__name__

    def explain(self, indent: int = 0) -> str:
        estimate = getattr(self, "estimate", None)
        line = "  " * indent + self.label
        if estimate is not None:
            line += f"  [~{estimate:,.0f} rows]"
        return "\n".join([line] + [c.explain(indent + 1) for c in self.children])


class Scan(Operator):
    """Leaf: every row of a table, with names qualified by `alias`."""

    def __init__(self, table, alias: str | None = None):
        self.table = table
        self.alias = alias or table.name

    def __iter__(self):
        names = [(c, f"{self.alias}.{c}") for c in self.table.columns]
        for _, row in self.table.scan():
            yield Row({q: row[c] for c, q in names})

    def columns(self):
        return [f"{self.alias}.{c}" for c in self.table.columns]

    @property
    def label(self):
        return f"Scan {self.table.name} AS {self.alias}"


class Filter(Operator):
    """σ: keep rows for which `predicate(row)` is true."""

    def __init__(self, child: Operator, predicate: Callable[[Row], Any]):
        self.children = (child,)
        self.predicate = predicate

    def __iter__(self):
        return (row for row in self.children[0] if self.predicate(row) is True)

    @property
    def label(self):
        return f"Filter {getattr(self.predicate, '__name__', self.predicate)}"


class Project(Operator):
    """π: compute output columns. `outputs` maps a name to a column or a function."""

    def __init__(self, child: Operator, outputs: dict[str, str | Callable[[Row], Any]]):
        self.children = (child,)
        self.outputs = outputs

    def __iter__(self):
        getters = [(name, src if callable(src) else (lambda r, c=src: r[c]))
                   for name, src in self.outputs.items()]
        for row in self.children[0]:
            yield Row({name: get(row) for name, get in getters})

    def columns(self):
        return list(self.outputs)

    @property
    def label(self):
        return f"Project {', '.join(self.outputs)}"


class NestedLoopJoin(Operator):
    """⋈: every pair (l, r) with on(l | r) true. kind='left' keeps unmatched l."""

    def __init__(self, left: Operator, right: Operator,
                 on: Callable[[Row], Any] | None = None, kind: str = "inner"):
        if kind not in ("inner", "left"):
            raise ValueError("kind must be 'inner' or 'left'")
        self.children = (left, right)
        self.on, self.kind = on, kind

    def __iter__(self):
        left, right = self.children
        inner = list(right)                        # materialize once: blocking
        nulls = dict.fromkeys(right.columns())
        for l in left:
            matched = False
            for r in inner:
                row = Row(l | r)
                if self.on is None or self.on(row) is True:
                    matched = True
                    yield row
            if not matched and self.kind == "left":
                yield Row(l | nulls)

    def columns(self):
        return self.children[0].columns() + self.children[1].columns()

    @property
    def label(self):
        return f"NestedLoopJoin ({self.kind})"


class Sort(Operator):
    """Order rows by keys [(column or function, descending)]. NULLs sort first."""

    def __init__(self, child: Operator, keys: list[tuple[str | Callable, bool]]):
        self.children = (child,)
        self.keys = keys

    def __iter__(self):
        rows = list(self.children[0])              # blocking
        for key, descending in reversed(self.keys):
            get = key if callable(key) else (lambda r, c=key: r[c])
            rows.sort(key=lambda r: _nulls_first(get(r)), reverse=descending)
        return iter(rows)

    @property
    def label(self):
        return "Sort " + ", ".join(f"{k}{' DESC' if d else ''}" for k, d in self.keys)


def _nulls_first(value):
    # (False, None) < (True, anything): NULL sorts before every value,
    # and None itself is never compared with a real value.
    return (value is not None, value)


class Limit(Operator):
    def __init__(self, child: Operator, count: int | None, offset: int = 0):
        self.children = (child,)
        self.count, self.offset = count, offset

    def __iter__(self):
        stop = None if self.count is None else self.offset + self.count
        return itertools.islice(self.children[0], self.offset, stop)

    @property
    def label(self):
        return f"Limit {self.count} offset {self.offset}"


class Distinct(Operator):
    def __init__(self, child: Operator):
        self.children = (child,)

    def __iter__(self):
        seen = set()
        for row in self.children[0]:
            key = tuple(row.items())
            if key not in seen:
                seen.add(key)
                yield row


class AggregateFunction:
    """Base for aggregates. `column=None` means 'the whole row' (COUNT(*))."""

    def __init__(self, column: str | None = None):
        self.column = column

    def start(self):
        return None

    def step(self, state, value):
        raise NotImplementedError

    def finish(self, state):
        return state

    def __repr__(self):
        return f"{type(self).__name__.upper()}({self.column or '*'})"


class Count(AggregateFunction):
    def start(self):
        return 0

    def step(self, state, value):
        return state + 1


class Sum(AggregateFunction):
    def step(self, state, value):
        return value if state is None else state + value


class Min(AggregateFunction):
    def step(self, state, value):
        return value if state is None or value < state else state


class Max(AggregateFunction):
    def step(self, state, value):
        return value if state is None or value > state else state


class Avg(AggregateFunction):
    def start(self):
        return (0, 0)

    def step(self, state, value):
        return (state[0] + value, state[1] + 1)

    def finish(self, state):
        total, n = state
        return None if n == 0 else total / n


class Aggregate(Operator):
    """γ: group rows by `group_by` columns and compute `aggregates` per group."""

    def __init__(self, child: Operator, group_by: list[str],
                 aggregates: dict[str, AggregateFunction]):
        self.children = (child,)
        self.group_by, self.aggregates = list(group_by), aggregates

    def __iter__(self):
        funcs = list(self.aggregates.values())
        groups: dict[tuple, list] = {}                      # hash aggregation
        for row in self.children[0]:                        # blocking
            key = tuple(row[c] for c in self.group_by)
            states = groups.get(key)
            if states is None:
                states = groups[key] = [f.start() for f in funcs]
            for i, f in enumerate(funcs):
                value = row if f.column is None else row[f.column]
                if value is not None:                       # aggregates skip NULLs
                    states[i] = f.step(states[i], value)
        if not groups and not self.group_by:                # aggregate of no rows
            groups[()] = [f.start() for f in funcs]         # still yields one row
        for key, states in groups.items():
            out = Row(zip(self.group_by, key))
            out.update((name, f.finish(s))
                       for (name, f), s in zip(self.aggregates.items(), states))
            yield out

    def columns(self):
        return self.group_by + list(self.aggregates)

    @property
    def label(self):
        aggs = ", ".join(f"{n}={f!r}" for n, f in self.aggregates.items())
        return f"Aggregate by {self.group_by or '()'}: {aggs}"


class Query:
    """Immutable, fluent query builder. Each method returns a new Query."""

    def __init__(self, db, table: str, alias: str | None = None):
        self._db = db
        self._from = (table, alias)
        self._joins: tuple = ()
        self._where: tuple = ()
        self._group: tuple | None = None
        self._aggregates: dict = {}
        self._having: tuple = ()
        self._order: tuple = ()
        self._select: dict | None = None
        self._distinct = False
        self._limit: tuple | None = None

    def _with(self, **changes) -> "Query":
        q = object.__new__(Query)
        q.__dict__ = self.__dict__ | {"_" + k: v for k, v in changes.items()}
        return q

    # -- building -------------------------------------------------------------------
    def join(self, table: str, on: Callable[[Row], Any], alias: str | None = None,
             kind: str = "inner") -> "Query":
        return self._with(joins=self._joins + ((table, alias, on, kind),))

    def where(self, predicate: Callable[[Row], Any]) -> "Query":
        return self._with(where=self._where + (predicate,))

    def group_by(self, *columns: str, **aggregates: AggregateFunction) -> "Query":
        return self._with(group=columns, aggregates=aggregates)

    def having(self, predicate: Callable[[Row], Any]) -> "Query":
        return self._with(having=self._having + (predicate,))

    def order_by(self, *keys: str | Callable) -> "Query":
        """'name' ascending, '-name' descending, or a function of the row."""
        parsed = tuple((k[1:], True) if isinstance(k, str) and k.startswith("-")
                       else (k, False) for k in keys)
        return self._with(order=self._order + parsed)

    def select(self, *columns: str, **computed: str | Callable[[Row], Any]) -> "Query":
        """select('u.name', total='o.total', double=lambda r: 2 * r['x'])"""
        outputs = {c.rpartition(".")[2]: c for c in columns}
        if len(outputs) != len(columns):
            raise ValueError("duplicate output names; use keyword aliases")
        return self._with(select=outputs | computed)

    def distinct(self) -> "Query":
        return self._with(distinct=True)

    def limit(self, count: int | None, offset: int = 0) -> "Query":
        return self._with(limit=(count, offset))

    # -- planning -------------------------------------------------------------------
    def plan(self) -> Operator:
        """The physical plan chosen by the cost-based planner."""
        from minidb.planner import Planner        # imported here: planner imports query
        return Planner(self).plan()

    def plan_naive(self) -> Operator:
        """Chapter 7's plan: joins in written order, every filter on top."""
        table, alias = self._from
        op: Operator = Scan(self._db.table(table), alias)
        for jtable, jalias, on, kind in self._joins:
            op = NestedLoopJoin(op, Scan(self._db.table(jtable), jalias), on, kind)
        for predicate in self._where:
            op = Filter(op, predicate)
        return self.finish_plan(op)

    def finish_plan(self, op: Operator) -> Operator:
        if self._group is not None:
            op = Aggregate(op, list(self._group), self._aggregates)
        for predicate in self._having:
            op = Filter(op, predicate)
        if self._order:
            op = Sort(op, list(self._order))
        if self._select is not None:
            op = Project(op, self._select)
        if self._distinct:
            op = Distinct(op)
        if self._limit is not None:
            op = Limit(op, *self._limit)
        return op

    # -- running --------------------------------------------------------------------
    def __iter__(self) -> Iterator[Row]:
        with self._db.reading():
            rows = list(self.plan())          # materialize while protected
        return iter(rows)

    def all(self) -> list[dict]:
        with self._db.reading():
            return [dict(row) for row in self.plan()]

    def first(self) -> dict | None:
        rows = self.limit(1).all()
        return rows[0] if rows else None

    def explain(self) -> str:
        return self.plan().explain()
```

## `minidb/expr.py`

Expression trees. Developed in [Chapter 14](14-query-planning.md).

```python
"""Expression trees: predicates the planner can look inside.

    col("age") > 30            Compare('>', Col('age'), Const(30))
    (col("a") == 1) & ~col("b").is_null()

Expressions are callable, so they work anywhere a predicate does, and
they implement SQL's three-valued logic: None means UNKNOWN.
"""
import operator
from collections.abc import Mapping


class Expr:
    __hash__ = object.__hash__        # we override ==, but keep identity hashing

    def eval(self, row: Mapping):
        raise NotImplementedError

    def __call__(self, row: Mapping):
        return self.eval(row)

    def columns(self) -> set[str]:
        return set()

    # -- building expressions with operators -----------------------------------------
    def __eq__(self, other): return Compare("=", self, _wrap(other))
    def __ne__(self, other): return Compare("!=", self, _wrap(other))
    def __lt__(self, other): return Compare("<", self, _wrap(other))
    def __le__(self, other): return Compare("<=", self, _wrap(other))
    def __gt__(self, other): return Compare(">", self, _wrap(other))
    def __ge__(self, other): return Compare(">=", self, _wrap(other))
    def __and__(self, other): return And(self, _wrap(other))
    def __or__(self, other): return Or(self, _wrap(other))
    def __invert__(self): return Not(self)
    def __add__(self, other): return Arith("+", self, _wrap(other))
    def __sub__(self, other): return Arith("-", self, _wrap(other))
    def __mul__(self, other): return Arith("*", self, _wrap(other))
    def __truediv__(self, other): return Arith("/", self, _wrap(other))
    def __radd__(self, other): return Arith("+", _wrap(other), self)
    def __rsub__(self, other): return Arith("-", _wrap(other), self)
    def __rmul__(self, other): return Arith("*", _wrap(other), self)

    def is_null(self): return IsNull(self)
    def is_not_null(self): return Not(IsNull(self))
    def isin(self, *values): return In(self, values)

    def __bool__(self):
        raise TypeError("use & | ~ to combine expressions, not and/or/not")


def _wrap(value) -> Expr:
    return value if isinstance(value, Expr) else Const(value)


class Col(Expr):
    def __init__(self, name: str):
        self.name = name

    def eval(self, row):
        return row[self.name]

    def columns(self):
        return {self.name}

    def __repr__(self):
        return self.name


class Const(Expr):
    def __init__(self, value):
        self.value = value

    def eval(self, row):
        return self.value

    def __repr__(self):
        return "NULL" if self.value is None else repr(self.value)


_COMPARE = {"=": operator.eq, "!=": operator.ne, "<": operator.lt,
            "<=": operator.le, ">": operator.gt, ">=": operator.ge}
_FLIPPED = {"=": "=", "!=": "!=", "<": ">", "<=": ">=", ">": "<", ">=": "<="}


class Compare(Expr):
    def __init__(self, op: str, left: Expr, right: Expr):
        self.op, self.left, self.right = op, left, right

    def eval(self, row):
        a, b = self.left.eval(row), self.right.eval(row)
        if a is None or b is None:
            return None                                   # UNKNOWN
        return _COMPARE[self.op](a, b)

    def columns(self):
        return self.left.columns() | self.right.columns()

    def flipped(self) -> "Compare":
        """b < a  for  a > b: lets the planner put the column on the left."""
        return Compare(_FLIPPED[self.op], self.right, self.left)

    def __repr__(self):
        return f"({self.left!r} {self.op} {self.right!r})"


class And(Expr):
    def __init__(self, *items: Expr):
        self.items = items

    def eval(self, row):
        result = True
        for item in self.items:
            v = item.eval(row)
            if v is False:
                return False
            if v is None:
                result = None
        return result

    def columns(self):
        return set().union(*(i.columns() for i in self.items))

    def __repr__(self):
        return "(" + " AND ".join(map(repr, self.items)) + ")"


class Or(Expr):
    def __init__(self, *items: Expr):
        self.items = items

    def eval(self, row):
        result = False
        for item in self.items:
            v = item.eval(row)
            if v is True:
                return True
            if v is None:
                result = None
        return result

    def columns(self):
        return set().union(*(i.columns() for i in self.items))

    def __repr__(self):
        return "(" + " OR ".join(map(repr, self.items)) + ")"


class Not(Expr):
    def __init__(self, item: Expr):
        self.item = item

    def eval(self, row):
        v = self.item.eval(row)
        return None if v is None else not v

    def columns(self):
        return self.item.columns()

    def __repr__(self):
        return f"NOT {self.item!r}"


class IsNull(Expr):
    def __init__(self, item: Expr):
        self.item = item

    def eval(self, row):
        return self.item.eval(row) is None                # never UNKNOWN

    def columns(self):
        return self.item.columns()

    def __repr__(self):
        return f"{self.item!r} IS NULL"


class In(Expr):
    def __init__(self, item: Expr, values):
        self.item, self.values = item, tuple(values)

    def eval(self, row):
        v = self.item.eval(row)
        if v is None:
            return None
        if v in self.values:
            return True
        return None if None in self.values else False

    def columns(self):
        return self.item.columns()

    def __repr__(self):
        return f"{self.item!r} IN {self.values!r}"


_ARITH = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}


class Arith(Expr):
    def __init__(self, op: str, left: Expr, right: Expr):
        self.op, self.left, self.right = op, left, right

    def eval(self, row):
        a, b = self.left.eval(row), self.right.eval(row)
        return None if a is None or b is None else _ARITH[self.op](a, b)

    def columns(self):
        return self.left.columns() | self.right.columns()

    def __repr__(self):
        return f"({self.left!r} {self.op} {self.right!r})"


def col(name: str) -> Col:
    return Col(name)


def lit(value) -> Const:
    return Const(value)


def conjuncts(predicate) -> list:
    """Split a predicate on AND: (a & b) & c -> [a, b, c]."""
    if isinstance(predicate, And):
        return [c for item in predicate.items for c in conjuncts(item)]
    return [predicate]
```

## `minidb/planner.py`

Cost-based planner. Developed in [Chapter 14](14-query-planning.md).

```python
"""A small cost-based planner: access paths, filter pushdown, join order.

It turns a Query into a tree of physical operators. Predicates written as
Expr objects can be analysed; plain Python callables are opaque and are
applied last, exactly where the user's query put them.
"""
from minidb.errors import DatabaseError
from minidb.expr import And, Col, Compare, Const, Expr, In, IsNull, Not, Or, conjuncts
from minidb.query import Filter, NestedLoopJoin, Operator, Row, Scan

# System R's default selectivities, for when we know nothing better
EQ_SELECTIVITY = 1 / 10
RANGE_SELECTIVITY = 1 / 3
OTHER_SELECTIVITY = 1 / 2


# -- physical operators that need indexes or hashing ----------------------------------------
class IndexLookup(Operator):
    """Rows whose indexed columns equal `key`: no scan."""

    def __init__(self, table, alias: str, index_name: str, key: dict):
        self.table, self.alias, self.index_name, self.key = table, alias, index_name, key

    def __iter__(self):
        for rid in self.table.lookup(self.key):
            row = self.table.row(rid)
            yield Row({f"{self.alias}.{c}": row[c] for c in self.table.columns})

    def columns(self):
        return [f"{self.alias}.{c}" for c in self.table.columns]

    @property
    def label(self):
        return f"IndexLookup {self.table.name} AS {self.alias} using {self.index_name} {self.key}"


class IndexRange(Operator):
    """Rows whose column lies between `lo` and `hi`, via a sorted index."""

    def __init__(self, table, alias: str, index_name: str, column: str,
                 lo, hi, lo_inclusive: bool, hi_inclusive: bool):
        self.table, self.alias, self.index_name, self.column = table, alias, index_name, column
        self.bounds = (lo, hi, lo_inclusive, hi_inclusive)

    def __iter__(self):
        for rid in self.table.range(self.column, *self.bounds):
            row = self.table.row(rid)
            yield Row({f"{self.alias}.{c}": row[c] for c in self.table.columns})

    def columns(self):
        return [f"{self.alias}.{c}" for c in self.table.columns]

    @property
    def label(self):
        lo, hi, li, hi_inc = self.bounds
        left = "" if lo is None else f"{lo!r} {'<=' if li else '<'} "
        right = "" if hi is None else f" {'<=' if hi_inc else '<'} {hi!r}"
        return f"IndexRange {self.table.name} AS {self.alias} using {self.index_name}: {left}{self.column}{right}"


class HashJoin(Operator):
    """Equi-join in O(|left| + |right|): hash the smaller side, probe with the other."""

    def __init__(self, left: Operator, right: Operator, left_keys: list[Expr],
                 right_keys: list[Expr], build: str = "right"):
        self.children = (left, right)
        self.left_keys, self.right_keys, self.build = left_keys, right_keys, build

    def __iter__(self):
        left, right = self.children
        if self.build == "right":
            build, build_keys, probe, probe_keys = right, self.right_keys, left, self.left_keys
        else:
            build, build_keys, probe, probe_keys = left, self.left_keys, right, self.right_keys
        buckets: dict[tuple, list[Row]] = {}
        for row in build:                                    # blocking on the build side
            key = tuple(k.eval(row) for k in build_keys)
            if not any(v is None for v in key):              # NULL never joins
                buckets.setdefault(key, []).append(row)
        for row in probe:
            key = tuple(k.eval(row) for k in probe_keys)
            for match in buckets.get(key, ()):
                yield Row(row | match)

    def columns(self):
        return self.children[0].columns() + self.children[1].columns()

    @property
    def label(self):
        on = " AND ".join(f"{l!r} = {r!r}" for l, r in zip(self.left_keys, self.right_keys))
        return f"HashJoin (build {self.build}) on {on}"


# -- the planner -------------------------------------------------------------------------
class Relation:
    """One FROM/JOIN item: a table (or a unit of work's view of it) and its alias."""

    def __init__(self, table, alias: str):
        self.table, self.alias = table, alias
        self.base = getattr(table, "base", table)            # unwrap a TableView
        self.columns = set(table.columns)

    def ndv(self, column: str) -> int | None:
        """Number of distinct values in `column`, if we know or can cheaply tell."""
        stats = getattr(self.base, "stats", {})
        if column in stats:
            return stats[column]
        index = self.base.index_on([column])
        return max(index.distinct_keys(), 1) if index is not None else None


class Planner:
    def __init__(self, query):
        self.q = query
        table, alias = query._from
        rels = [Relation(query._db.table(table), alias or table)]
        rels += [Relation(query._db.table(t), a or t) for t, a, _, _ in query._joins]
        self.rels = {r.alias: r for r in rels}

    # -- column resolution ---------------------------------------------------------------
    def resolve(self, name: str) -> tuple[str, str] | None:
        """'u.age' or 'age' -> (alias, column), if unambiguous."""
        if "." in name:
            alias, _, column = name.partition(".")
            rel = self.rels.get(alias)
            return (alias, column) if rel and column in rel.columns else None
        found = [(a, name) for a, r in self.rels.items() if name in r.columns]
        return found[0] if len(found) == 1 else None

    def aliases(self, expr: Expr) -> set[str] | None:
        out = set()
        for name in expr.columns():
            hit = self.resolve(name)
            if hit is None:
                return None
            out.add(hit[0])
        return out

    # -- cardinality estimation --------------------------------------------------------------
    def selectivity(self, e) -> float:
        if isinstance(e, Compare):
            c = e if isinstance(e.left, Col) else e.flipped()
            if isinstance(c.left, Col) and isinstance(c.right, Col):
                if c.op != "=":
                    return RANGE_SELECTIVITY
                ndvs = [self._ndv(c.left.name), self._ndv(c.right.name)]
                known = [n for n in ndvs if n]
                return 1 / max(known) if known else EQ_SELECTIVITY
            if isinstance(c.left, Col):
                eq = 1 / n if (n := self._ndv(c.left.name)) else EQ_SELECTIVITY
                if c.op == "=":
                    return eq
                return 1 - eq if c.op == "!=" else RANGE_SELECTIVITY
            return OTHER_SELECTIVITY
        if isinstance(e, And):
            result = 1.0
            for item in e.items:
                result *= self.selectivity(item)              # independence assumption
            return result
        if isinstance(e, Or):
            result = 0.0
            for item in e.items:
                s = self.selectivity(item)
                result = result + s - result * s
            return result
        if isinstance(e, Not):
            return 1 - self.selectivity(e.item)
        if isinstance(e, IsNull):
            return EQ_SELECTIVITY
        if isinstance(e, In) and isinstance(e.item, Col):
            eq = 1 / n if (n := self._ndv(e.item.name)) else EQ_SELECTIVITY
            return min(1.0, len(e.values) * eq)
        return OTHER_SELECTIVITY

    def _ndv(self, name: str) -> int | None:
        hit = self.resolve(name)
        return self.rels[hit[0]].ndv(hit[1]) if hit else None

    # -- access paths: how to read one table ---------------------------------------------------
    def access_path(self, rel: Relation, preds: list[Expr]) -> tuple[Operator, float]:
        n = len(rel.base)
        eq: dict[str, tuple[object, Expr]] = {}
        ranges: dict[str, list[tuple[str, object, Expr]]] = {}
        canonical = []
        for p in preds:
            c = p.flipped() if isinstance(p, Compare) and not isinstance(p.left, Col) else p
            if isinstance(c, Compare) and isinstance(c.left, Col) and \
                    isinstance(c.right, Const) and c.right.value is not None:
                column = self.resolve(c.left.name)[1]
                try:                    # normalize the constant like a stored value
                    value = rel.table.schema.column(column).prepare(c.right.value)
                except DatabaseError:
                    value = None        # not a valid value: compare as written
                if value is not None:
                    p = Compare(c.op, c.left, Const(value))
                    if c.op == "=":
                        eq[column] = (value, p)
                    elif c.op in ("<", "<=", ">", ">="):
                        ranges.setdefault(column, []).append((c.op, value, p))
            canonical.append(p)
        preds = canonical

        best_cost, best_op, consumed = float(n), Scan(rel.table, rel.alias), []
        best_op.estimate = n
        for index in rel.base.indexes.values():
            if set(index.columns) <= eq.keys():                       # equality lookup
                matches = n / max(index.distinct_keys(), 1)
                if 1 + matches < best_cost:
                    best_cost, consumed = 1 + matches, [eq[c][1] for c in index.columns]
                    best_op = IndexLookup(rel.table, rel.alias, index.name,
                                          {c: eq[c][0] for c in index.columns})
                    best_op.estimate = matches
            if index.kind != "hash" and len(index.columns) == 1 \
                    and index.columns[0] in ranges:                   # range scan
                column = index.columns[0]
                lo = hi = None
                lo_inc = hi_inc = True
                for op, value, _ in ranges[column]:
                    if op in (">", ">=") and (lo is None or value > lo or (value == lo and op == ">")):
                        lo, lo_inc = value, op == ">="
                    elif op in ("<", "<=") and (hi is None or value < hi or (value == hi and op == "<")):
                        hi, hi_inc = value, op == "<="
                matches = n * RANGE_SELECTIVITY ** ((lo is not None) + (hi is not None))
                if 1 + matches < best_cost:
                    best_cost, consumed = 1 + matches, [p for _, _, p in ranges[column]]
                    best_op = IndexRange(rel.table, rel.alias, index.name, column,
                                         lo, hi, lo_inc, hi_inc)
                    best_op.estimate = matches

        estimate = float(n)
        for p in preds:
            estimate *= self.selectivity(p)
        op = best_op
        residual = [p for p in preds if not any(p is c for c in consumed)]
        if residual:
            op = Filter(op, residual[0] if len(residual) == 1 else And(*residual))
            op.estimate = estimate
        return op, estimate

    # -- join ordering: greedy, smallest intermediate result first ------------------------------
    def join(self, paths: dict[str, tuple[Operator, float]],
             multi: list[tuple[Expr, set[str]]]) -> tuple[Operator, float]:
        remaining = dict(paths)
        start = min(remaining, key=lambda a: remaining[a][1])
        op, est = remaining.pop(start)
        joined, pending = {start}, list(multi)
        while remaining:
            def score(alias):
                usable = [e for e, al in pending if alias in al and al <= joined | {alias}]
                sel = 1.0
                for e in usable:
                    sel *= self.selectivity(e)
                return (not usable, est * remaining[alias][1] * sel)   # prefer connected
            alias = min(remaining, key=score)
            out_est = score(alias)[1]
            right, right_est = remaining.pop(alias)
            usable = [(e, al) for e, al in pending if alias in al and al <= joined | {alias}]
            pending = [(e, al) for e, al in pending if not any(e is u for u, _ in usable)]
            left_keys, right_keys, others = [], [], []
            for e, _ in usable:
                if isinstance(e, Compare) and e.op == "=" and \
                        isinstance(e.left, Col) and isinstance(e.right, Col):
                    sides = (self.resolve(e.left.name)[0], self.resolve(e.right.name)[0])
                    if sides[1] == alias and sides[0] in joined:
                        left_keys.append(e.left); right_keys.append(e.right); continue
                    if sides[0] == alias and sides[1] in joined:
                        left_keys.append(e.right); right_keys.append(e.left); continue
                others.append(e)
            if left_keys:
                build = "right" if right_est <= est else "left"
                op = HashJoin(op, right, left_keys, right_keys, build)
                if others:
                    op = Filter(op, others[0] if len(others) == 1 else And(*others))
            else:
                on = None if not others else others[0] if len(others) == 1 else And(*others)
                op = NestedLoopJoin(op, right, on)
            joined.add(alias)
            est = out_est
            op.estimate = est
        for e, _ in pending:                                  # shouldn't happen, but be safe
            op = Filter(op, e)
        return op, est

    # -- putting it together -----------------------------------------------------------------
    def plan(self) -> Operator:
        q = self.q
        if any(kind != "inner" for _, _, _, kind in q._joins):
            return q.plan_naive()                # outer joins: keep the written order
        local = {a: [] for a in self.rels}
        multi, opaque = [], []
        predicates = list(q._where) + [on for _, _, on, _ in q._joins if on is not None]
        for predicate in predicates:
            for c in (conjuncts(predicate) if isinstance(predicate, Expr) else [predicate]):
                aliases = self.aliases(c) if isinstance(c, Expr) else None
                if not aliases:
                    opaque.append(c)             # callables, unresolvable or constant
                elif len(aliases) == 1:
                    local[next(iter(aliases))].append(c)
                else:
                    multi.append((c, aliases))
        paths = {a: self.access_path(self.rels[a], local[a]) for a in self.rels}
        op, est = self.join(paths, multi)
        for predicate in opaque:
            op = Filter(op, predicate)
        return q.finish_plan(op)
```

## `minidb/locks.py`

Readers–writer locks. Developed in [Chapter 11](11-readers-writer-locks.md).

```python
"""Readers–writer locks: any number of readers, or exactly one writer."""
import threading
from contextlib import contextmanager


class RWLock:
    """Interface. Subclasses implement the four acquire/release methods."""

    def acquire_read(self) -> None: raise NotImplementedError
    def release_read(self) -> None: raise NotImplementedError
    def acquire_write(self) -> None: raise NotImplementedError
    def release_write(self) -> None: raise NotImplementedError

    @contextmanager
    def read(self):
        self.acquire_read()
        try:
            yield
        finally:
            self.release_read()

    @contextmanager
    def write(self):
        self.acquire_write()
        try:
            yield
        finally:
            self.release_write()


class ReaderPreferringLock(RWLock):
    """Courtois et al.'s first problem: readers never wait for waiting writers."""

    def __init__(self):
        self._cond = threading.Condition()
        self._readers = 0
        self._writer = False

    def acquire_read(self):
        with self._cond:
            self._cond.wait_for(lambda: not self._writer)
            self._readers += 1

    def release_read(self):
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    def acquire_write(self):
        with self._cond:
            self._cond.wait_for(lambda: not self._writer and self._readers == 0)
            self._writer = True

    def release_write(self):
        with self._cond:
            self._writer = False
            self._cond.notify_all()


class WriterPreferringLock(RWLock):
    """Courtois et al.'s second problem: a waiting writer blocks new readers."""

    def __init__(self):
        self._cond = threading.Condition()
        self._readers = 0
        self._writer = False
        self._writers_waiting = 0

    def acquire_read(self):
        with self._cond:
            self._cond.wait_for(lambda: not self._writer and self._writers_waiting == 0)
            self._readers += 1

    def release_read(self):
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    def acquire_write(self):
        with self._cond:
            self._writers_waiting += 1
            self._cond.wait_for(lambda: not self._writer and self._readers == 0)
            self._writers_waiting -= 1
            self._writer = True

    def release_write(self):
        with self._cond:
            self._writer = False
            self._cond.notify_all()


class FairRWLock(RWLock):
    """Starvation-free RW lock: requests are admitted in arrival (ticket) order.

    Consecutive readers are admitted together; a writer waits for the readers
    ahead of it to leave, and nobody behind it can overtake it.
    """

    def __init__(self):
        self._cond = threading.Condition()
        self._next_ticket = 0          # handed to the next arrival
        self._serving = 0              # ticket at the head of the queue
        self._readers = 0              # readers inside
        self._writer = False           # writer inside?

    def _take_ticket(self) -> int:
        ticket = self._next_ticket
        self._next_ticket += 1
        return ticket

    def acquire_read(self):
        with self._cond:
            ticket = self._take_ticket()
            self._cond.wait_for(lambda: self._serving == ticket and not self._writer)
            self._readers += 1
            self._serving += 1
            self._cond.notify_all()            # the next ticket may be a reader too

    def release_read(self):
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()        # a writer may be waiting at the head

    def acquire_write(self):
        with self._cond:
            ticket = self._take_ticket()
            self._cond.wait_for(lambda: self._serving == ticket
                                and not self._writer and self._readers == 0)
            self._writer = True
            self._serving += 1

    def release_write(self):
        with self._cond:
            self._writer = False
            self._cond.notify_all()
```

## `minidb/uow.py`

Unit of Work. Developed in [Chapter 12](12-isolation.md).

```python
"""The Unit of Work: a private workspace, an identity map, atomic commit.

Version 3: optimistic concurrency control. A read-write unit of work holds
no lock while it runs. It records what it read (its *read set*), and at
commit, under the exclusive lock, checks that none of it has changed.
"""
from collections.abc import Iterator, Mapping
from contextlib import nullcontext
from types import MappingProxyType

from minidb import changes as ch
from minidb.changes import Change
from minidb.errors import ConflictError, DatabaseError
from minidb.query import Query

type Row = dict[str, object]


class TransactionError(DatabaseError):
    """The Unit of Work was used in the wrong state (e.g. after commit)."""


class TableView:
    """A table as one unit of work sees it: committed rows + private overlay.

    Every read of committed data happens under a short shared latch and is
    recorded in the read set, so commit can check it is still true.
    """

    def __init__(self, uow, table):
        self.uow, self.base = uow, table
        self.name, self.schema, self.columns = table.name, table.schema, table.columns
        self.overlay: dict[int, Row | None] = {}          # rowid -> row, None = deleted
        # -- the read set ------------------------------------------------------------
        self.scanned_version: int | None = None            # table version at first scan
        self.row_reads: dict[int, int | None] = {}         # rowid -> row version read
        self.key_reads: dict[tuple, frozenset[int]] = {}   # equality read -> rowids seen

    # -- reads of committed data (latched and recorded) ---------------------------------
    def _base_row(self, rowid: int) -> Row | None:
        with self.uow._latch():
            row = self.base.rows.get(rowid)
            self.row_reads.setdefault(rowid, self.base.row_versions.get(rowid))
        return row

    def _base_items(self) -> list[tuple[int, Row]]:
        with self.uow._latch():
            items = list(self.base.rows.items())
            if self.scanned_version is None:
                self.scanned_version = self.base.version
        return items

    def _base_equal(self, kind: str, key: Mapping[str, object]) -> set[int]:
        with self.uow._latch():
            found = (self.base.lookup(key) if kind == "lookup"
                     else set(self.base.match(key)))
        self.key_reads.setdefault((kind, _freeze(key)), frozenset(found))
        return found

    # -- the interface used by planners and queries ------------------------------------
    def row(self, rowid: int) -> Row:
        row = self.overlay[rowid] if rowid in self.overlay else self._base_row(rowid)
        if row is None:
            raise KeyError(rowid)
        return row

    def get(self, rowid: int) -> Row | None:
        try:
            return dict(self.row(rowid))
        except KeyError:
            return None

    def scan(self) -> Iterator[tuple[int, Row]]:
        items = self._base_items()
        seen = set()
        for rowid, row in items:
            seen.add(rowid)
            if rowid in self.overlay:
                row = self.overlay[rowid]
                if row is None:
                    continue
            yield rowid, dict(row)
        for rowid, row in list(self.overlay.items()):     # rows inserted here
            if row is not None and rowid not in seen:
                yield rowid, dict(row)

    def match(self, where=None) -> list[int]:
        if where is None or callable(where):
            return [rid for rid, row in self.scan()
                    if where is None or where(MappingProxyType(row))]
        wanted = {c: self.schema.column(c).prepare(v) for c, v in where.items()}
        found = [rid for rid in self._base_equal("match", wanted) if rid not in self.overlay]
        found += [rid for rid, row in self.overlay.items()
                  if row is not None and _equal(row, wanted)]
        return found

    def lookup(self, key: Mapping[str, object]) -> set[int]:
        found = {rid for rid in self._base_equal("lookup", key) if rid not in self.overlay}
        found |= {rid for rid, row in self.overlay.items()
                  if row is not None and _equal(row, key)}
        return found

    def select(self, where=None) -> list[Row]:
        return [dict(self.row(rid)) for rid in self.match(where)]

    def unique_keys(self) -> list[tuple[str, ...]]:
        return self.base.unique_keys()

    def index_on(self, columns):
        return self.base.index_on(columns)

    def new_rowid(self) -> int:
        return self.base.new_rowid()

    def __len__(self) -> int:
        return sum(1 for _ in self.scan())

    # -- validation (caller holds the exclusive lock) ------------------------------------
    def conflicts(self) -> str | None:
        """Describe the first read that is no longer true, or None."""
        b = self.base
        if self.scanned_version is not None and b.version != self.scanned_version:
            return f"{self.name} changed since it was scanned"
        for rowid, version in self.row_reads.items():
            if b.row_versions.get(rowid) != version:
                return f"{self.name} row {rowid} changed since it was read"
        for (kind, key), seen in self.key_reads.items():
            if kind == "range":
                now = set(b.range(*key))
            elif kind == "lookup":
                now = b.lookup(dict(key))
            else:
                now = set(b.match(dict(key)))
            if frozenset(now) != seen:
                return f"{self.name} rows matching {dict(key) if kind != 'range' else key} changed"
        return None

    def range(self, column: str, lo=None, hi=None,
              lo_inclusive: bool = True, hi_inclusive: bool = True) -> list[int]:
        args = (column, lo, hi, lo_inclusive, hi_inclusive)
        with self.uow._latch():
            found = self.base.range(*args)
        self.key_reads.setdefault(("range", args), frozenset(found))
        found = [rid for rid in found if rid not in self.overlay]
        found += [rid for rid, row in self.overlay.items()
                  if row is not None and _in_range(row[column], *args[1:])]
        return found


def _equal(row: Mapping, key: Mapping) -> bool:
    """SQL equality on every column of `key`: NULL never equals anything."""
    return all(v is not None and row[c] == v for c, v in key.items())


def _freeze(key: Mapping[str, object]) -> tuple:
    return tuple(sorted(key.items(), key=lambda kv: kv[0]))


class Record(dict):
    """A row loaded through a unit of work. Mutate it; commit saves it."""

    def __init__(self, table: str, rowid: int, row: Row):
        super().__init__(row)
        self.table, self.rowid = table, rowid

    def __repr__(self):
        return f"Record({self.table}#{self.rowid}, {dict.__repr__(self)})"


class UnitOfWork:
    """Plan into a private workspace; validate and apply at commit.

    Modes:
      default        optimistic: no lock while running, validate at commit
      readonly=True  shared lock for the whole unit of work; no writes
      exclusive=True exclusive lock for the whole unit of work; never conflicts
    """

    def __init__(self, db, *, deferred: bool = False, readonly: bool = False,
                 exclusive: bool = False):
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
        db._begin(self)

    def _latch(self):
        """The short lock around each read of committed data."""
        if self.readonly or self.exclusive or self._committing:
            return nullcontext()                  # we already hold the lock
        return self.db._lock.read()

    def reading(self):
        return nullcontext(self)                  # views latch each read themselves

    # -- the planner "state" interface ---------------------------------------------------
    @property
    def foreign_keys(self):
        return self.db.foreign_keys

    def table(self, name: str) -> TableView:
        view = self._views.get(name)
        if view is None:
            view = self._views[name] = TableView(self, self.db.table(name))
        return view

    # -- writes: plan now, against the workspace -------------------------------------------
    def insert(self, table: str, values: Mapping[str, object]) -> int:
        self._require_active(writing=True)
        self.flush()
        changes = ch.plan_insert(self, table, values, check=not self.deferred)
        self._record(changes)
        return changes[0].rowid

    def update(self, table: str, changes: Mapping[str, object], where=None) -> int:
        self._require_active(writing=True)
        self.flush()
        planned = ch.plan_update(self, table, changes, where, check=not self.deferred)
        self._record(planned)
        return len(planned)

    def delete(self, table: str, where=None) -> int:
        self._require_active(writing=True)
        self.flush()
        planned = ch.plan_delete(self, table, where, check=not self.deferred)
        self._record(planned)
        return sum(1 for c in planned if c.table == table and c.kind == "delete")

    def _record(self, changes: list[Change]) -> None:
        for c in changes:
            self.table(c.table).overlay[c.rowid] = c.after
            self._changes.append(c)
            key = (c.table, c.rowid)
            if key in self._identity:
                if c.after is None:
                    del self._identity[key], self._snapshots[key]
                else:
                    record = self._identity[key]
                    record.clear()
                    record.update(c.after)
                    self._snapshots[key] = dict(c.after)

    # -- reads -------------------------------------------------------------------------
    def get(self, table: str, rowid: int) -> Record | None:
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

    def find(self, table: str, where=None) -> list[Record]:
        self.flush()
        return [self.get(table, rid) for rid in self.table(table).match(where)]

    def select(self, table: str, where=None) -> list[Row]:
        self.flush()
        return self.table(table).select(where)

    def query(self, table: str, alias: str | None = None) -> Query:
        self.flush()
        return Query(self, table, alias)

    # -- dirty checking ---------------------------------------------------------------------
    def flush(self) -> None:
        for key, record in list(self._identity.items()):
            before = self._snapshots[key]
            if record != before:
                self._require_active(writing=True)
                diff = {c: v for c, v in record.items() if before.get(c, _MISSING) != v}
                planned = ch.plan_update(self, key[0], diff, rowids=[key[1]],
                                         check=not self.deferred)
                self._record(planned)

    # -- finishing ---------------------------------------------------------------------
    def commit(self) -> None:
        self._require_active()
        self.flush()
        if self.readonly:
            pass                                  # nothing to write, nothing to check
        elif self.exclusive:
            self._apply()                         # nobody else ran: nothing to validate
        else:
            with self.db._lock.write():           # the only exclusive section
                self._committing = True
                try:
                    self._validate()
                    self._apply()
                finally:
                    self._committing = False
        self.state = "committed"
        self.db._end(self)

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
        self._require_active()
        self._views.clear()
        self._changes.clear()
        self._identity.clear()
        self.state = "rolled back"
        self.db._end(self)

    def _require_active(self, writing: bool = False) -> None:
        if self.state != "active":
            raise TransactionError(f"unit of work is already {self.state}")
        if writing and self.readonly:
            raise TransactionError("cannot write in a read-only unit of work")

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
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


_MISSING = object()


def _in_range(value, lo, hi, lo_inclusive, hi_inclusive) -> bool:
    if value is None:
        return False
    if lo is not None and (value < lo or (value == lo and not lo_inclusive)):
        return False
    return not (hi is not None and (value > hi or (value == hi and not hi_inclusive)))
```

## `minidb/storage.py`

Formats, snapshot and write-ahead log. Developed in [Chapter 13](13-persistence.md).

```python
"""Durability: pluggable formats, an atomic snapshot and a write-ahead log."""
import hashlib
import json
import os
import struct
import threading
import zlib
from collections.abc import Iterator
from pathlib import Path


class Format:
    """Serializes primitives (dict, list, str, int, float, bool, None) to bytes."""
    name = "abstract"
    suffix = ".bin"

    def dumps(self, obj) -> bytes:
        raise NotImplementedError

    def loads(self, data: bytes):
        raise NotImplementedError


class JsonFormat(Format):
    name = "json"
    suffix = ".json"

    def dumps(self, obj) -> bytes:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")

    def loads(self, data: bytes):
        return json.loads(data.decode("utf-8"))


def encode_row(schema, row: dict) -> list:
    return [c.type.to_primitive(row[c.name]) for c in schema.columns]


def decode_row(schema, values: list) -> dict:
    if len(values) != len(schema.columns):
        raise ValueError(f"{schema.name}: stored row has {len(values)} values")
    return {c.name: c.type.from_primitive(v) for c, v in zip(schema.columns, values)}


def schema_fingerprint(db) -> str:
    """A hash of everything declarative about the schema (not checks or defaults)."""
    parts = []
    for name in sorted(db.tables):
        s = db.tables[name].schema
        parts.append((name, [(c.name, repr(c.type), c.nullable) for c in s.columns],
                      s.primary_key, sorted(s.unique)))
    parts.append(sorted((fk.table, fk.columns, fk.ref_table, fk.ref_columns, fk.on_delete)
                        for fk in db.foreign_keys))
    return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]


_FRAME = struct.Struct(">II")        # payload length, crc32


class Storage:
    """A directory holding `snapshot<suffix>` and `wal.log`."""

    def __init__(self, directory: str | os.PathLike, format: Format | None = None,
                 *, sync: bool = True):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.format = format or JsonFormat()
        self.sync = sync
        self.snapshot_path = self.dir / f"snapshot{self.format.suffix}"
        self.log_path = self.dir / "wal.log"
        self._latch = threading.Lock()           # serializes file operations
        self._log = None

    # -- snapshot ----------------------------------------------------------------------
    def write_snapshot(self, state: dict) -> None:
        tmp = self.snapshot_path.with_name(self.snapshot_path.name + ".tmp")
        with self._latch:
            with open(tmp, "wb") as f:
                f.write(self.format.dumps(state))
                self._fsync(f)
            os.replace(tmp, self.snapshot_path)             # atomic switch
            self._fsync_dir()

    def read_snapshot(self) -> dict | None:
        if not self.snapshot_path.exists():
            return None
        return self.format.loads(self.snapshot_path.read_bytes())

    # -- log ------------------------------------------------------------------------------
    def append(self, record: dict) -> None:
        payload = self.format.dumps(record)
        frame = _FRAME.pack(len(payload), zlib.crc32(payload)) + payload
        with self._latch:
            if self._log is None:
                self._log = open(self.log_path, "ab")
            self._log.write(frame)
            self._fsync(self._log)

    def read_log(self) -> Iterator[dict]:
        """Yield intact records; cut off a torn or corrupt tail."""
        if not self.log_path.exists():
            return
        data = self.log_path.read_bytes()
        pos = 0
        while pos + _FRAME.size <= len(data):
            length, crc = _FRAME.unpack_from(data, pos)
            payload = data[pos + _FRAME.size: pos + _FRAME.size + length]
            if len(payload) < length or zlib.crc32(payload) != crc:
                break                                        # torn write
            yield self.format.loads(payload)
            pos += _FRAME.size + length
        if pos < len(data):
            with self._latch, open(self.log_path, "r+b") as f:
                f.truncate(pos)
                self._fsync(f)

    def truncate_log(self) -> None:
        with self._latch:
            if self._log is not None:
                self._log.close()
                self._log = None
            with open(self.log_path, "wb") as f:
                self._fsync(f)

    def close(self) -> None:
        with self._latch:
            if self._log is not None:
                self._log.close()
                self._log = None

    # -- fsync helpers --------------------------------------------------------------------
    def _fsync(self, f) -> None:
        f.flush()
        if self.sync:
            os.fsync(f.fileno())

    def _fsync_dir(self) -> None:
        if not self.sync or os.name != "posix":
            return                                # Windows can't open directories
        fd = os.open(self.dir, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
```

## `minidb/database.py`

The Database façade. Developed in [Chapter 13](13-persistence.md).

```python
"""The public entry point: tables, cross-table constraints and CRUD."""
from dataclasses import replace

from minidb import changes as ch
from minidb.changes import Change
from minidb.errors import SchemaError
from minidb.query import Query
from minidb.schema import Check, Column, ForeignKey, TableSchema
from minidb.table import Row, Table, Where
from minidb.uow import UnitOfWork
import threading
from contextlib import contextmanager
from minidb.uow import TransactionError
from minidb.locks import FairRWLock
import random
import time
from minidb.errors import ConflictError
from minidb.storage import Storage, decode_row, encode_row, schema_fingerprint


class Database:
    def __init__(self):
        self.tables: dict[str, Table] = {}
        self.foreign_keys: list[ForeignKey] = []
        self.commit_seq = 0
        self.storage: Storage | None = None
        self._lock = FairRWLock()
        self._local = threading.local()

    # -- schema --------------------------------------------------------------------
    def create_table(self, name: str, columns: list[Column], *,
                     primary_key: str | tuple[str, ...] = (),
                     unique: tuple[str | tuple[str, ...], ...] = (),
                     checks: list[Check] = (),
                     foreign_keys: list[ForeignKey] = ()) -> Table:
        if name in self.tables:
            raise SchemaError(f"table {name!r} already exists")
        schema = TableSchema(name, tuple(columns), tuple(checks),
                             primary_key, tuple(unique))
        table = self.tables[name] = Table(schema)
        try:
            for fk in foreign_keys:
                self._add_foreign_key(replace(fk, table=name))
        except Exception:
            del self.tables[name]
            self.foreign_keys = [f for f in self.foreign_keys if f.table != name]
            raise
        return table

    def _add_foreign_key(self, fk: ForeignKey) -> None:
        child, parent = self.table(fk.table), self.table(fk.ref_table)
        if not fk.ref_columns:
            if not parent.schema.primary_key:
                raise SchemaError(f"{parent.name} has no primary key to reference")
            fk = replace(fk, ref_columns=parent.schema.primary_key)
        if len(fk.columns) != len(fk.ref_columns):
            raise SchemaError(f"{fk.name}: column count mismatch")
        for c, r in zip(fk.columns, fk.ref_columns):
            if type(child.schema.column(c).type) is not type(parent.schema.column(r).type):
                raise SchemaError(f"{fk.name}: {c} and {parent.name}.{r} differ in type")
        target = parent.index_on(fk.ref_columns)
        if target is None or not target.unique:
            raise SchemaError(f"{fk.name}: {parent.name}{fk.ref_columns} is not a key")
        if child.index_on(fk.columns) is None:
            child.create_index(fk.name, fk.columns)
        ch.check_parents_exist(self, child, child.rows.values(), [fk])
        self.foreign_keys.append(fk)

    def drop_table(self, name: str) -> None:
        self.table(name)
        if any(fk.ref_table == name and fk.table != name for fk in self.foreign_keys):
            raise SchemaError(f"{name!r} is referenced by a foreign key")
        self.foreign_keys = [fk for fk in self.foreign_keys if fk.table != name]
        del self.tables[name]

    def table(self, name: str) -> Table:
        try:
            return self.tables[name]
        except KeyError:
            raise SchemaError(f"no such table: {name!r}") from None

    def create_index(self, table: str, name: str, columns: list[str],
                     unique: bool = False, kind: str = "hash") -> None:
        with self._lock.write():
            self.table(table).create_index(name, columns, unique, kind)

    # -- reads ---------------------------------------------------------------------
    def get(self, table: str, rowid: int) -> Row | None:
        with self.reading():
            return self.table(table).get(rowid)

    def select(self, table: str, where: Where = None) -> list[Row]:
        with self.reading():
            return self.table(table).select(where)

    def query(self, table: str, alias: str | None = None) -> Query:
        return Query(self, table, alias)

    # -- writes ----------------------------------------------------------------------
    def insert(self, table: str, values: Row) -> int:
        return self.transaction(lambda uow: uow.insert(table, values))

    def update(self, table: str, changes: Row, where: Where = None) -> int:
        return self.transaction(lambda uow: uow.update(table, changes, where))

    def delete(self, table: str, where: Where = None) -> int:
        return self.transaction(lambda uow: uow.delete(table, where))

    def apply(self, changes: list[Change]) -> None:
        """Write validated changes as one commit. The caller holds the write lock."""
        seq = self.commit_seq + 1
        if self.storage is not None:                        # write-ahead rule
            self.storage.append({"seq": seq, "changes": [
                [c.table, c.rowid,
                 None if c.after is None
                 else encode_row(self.tables[c.table].schema, c.after)]
                for c in changes]})
        self.commit_seq = seq
        for c in changes:
            self._apply_one(c.table, c.rowid, c.after, seq)

    def _apply_one(self, table: str, rowid: int, row: Row | None, seq: int) -> None:
        t = self.tables[table]
        if row is None:
            if rowid in t.rows:
                t.remove(rowid)
            t.row_versions.pop(rowid, None)
        else:
            t.put(rowid, row)
            t.row_versions[rowid] = seq
            t._next_rowid = max(t._next_rowid, rowid + 1)
        t.version = seq

    def unit_of_work(self, *, deferred: bool = False, readonly: bool = False,
                     exclusive: bool = False) -> UnitOfWork:
        return UnitOfWork(self, deferred=deferred, readonly=readonly, exclusive=exclusive)

    def transaction(self, fn, *, retries: int = 5, deferred: bool = False):
        """Run fn(uow) and commit, retrying on ConflictError.

        `fn` may run several times, so it must not have side effects outside
        the database. After `retries` optimistic attempts, the final attempt
        runs exclusively and cannot conflict: every transaction finishes.
        """
        for attempt in range(retries + 1):
            uow = self.unit_of_work(deferred=deferred, exclusive=(attempt == retries))
            try:
                result = fn(uow)
                uow.commit()
                return result
            except ConflictError:
                uow.rollback()
                time.sleep(random.uniform(0, 0.0005 * 2 ** attempt))   # back off
            except BaseException:
                if uow.state == "active":
                    uow.rollback()
                raise

    # -- concurrency control ------------------------------------------------------------
    def _active_uow(self):
        return getattr(self._local, "uow", None)

    def _begin(self, uow) -> None:
        """Called by a new UnitOfWork. Optimistic ones take no lock at all."""
        if self._active_uow() is not None:
            raise TransactionError("this thread already has an active unit of work")
        if uow.readonly:
            self._lock.acquire_read()
        elif uow.exclusive:
            self._lock.acquire_write()
        self._local.uow = uow

    def _end(self, uow) -> None:
        self._local.uow = None
        if uow.readonly:
            self._lock.release_read()
        elif uow.exclusive:
            self._lock.release_write()

    @contextmanager
    def reading(self):
        """Hold the lock in shared mode for one read outside any unit of work."""
        if self._active_uow() is not None:
            raise TransactionError("inside a unit of work, read through the unit of work")
        with self._lock.read():
            yield self

    # -- persistence ---------------------------------------------------------------------
    def attach(self, storage: Storage) -> None:
        """Load saved data and log all future commits. Call after create_table()."""
        with self._lock.write():
            if self.storage is not None:
                raise SchemaError("storage already attached")
            if any(len(t) for t in self.tables.values()):
                raise SchemaError("attach storage before inserting data")
            state = storage.read_snapshot()
            if state is not None:
                if state["fingerprint"] != schema_fingerprint(self):
                    raise SchemaError("stored data was written with a different schema")
                self._load_state(state)
            for record in storage.read_log():
                if record["seq"] <= self.commit_seq:
                    continue                    # already in the snapshot
                for table, rowid, values in record["changes"]:
                    row = None if values is None else decode_row(
                        self.tables[table].schema, values)
                    self._apply_one(table, rowid, row, record["seq"])
                self.commit_seq = record["seq"]
            self.storage = storage

    def checkpoint(self) -> None:
        """Write a snapshot and empty the log. Writers wait; readers don't."""
        with self._lock.read():
            state = {
                "format": 1,
                "fingerprint": schema_fingerprint(self),
                "commit_seq": self.commit_seq,
                "tables": {name: {"next_rowid": t._next_rowid,
                                  "rows": [[rid, encode_row(t.schema, row)]
                                           for rid, row in t.rows.items()]}
                           for name, t in self.tables.items()},
            }
            self.storage.write_snapshot(state)
            self.storage.truncate_log()

    def _load_state(self, state: dict) -> None:
        self.commit_seq = state["commit_seq"]
        for name, data in state["tables"].items():
            t = self.tables[name]
            for rowid, values in data["rows"]:
                t.put(rowid, decode_row(t.schema, values))
                t.row_versions[rowid] = self.commit_seq
            t._next_rowid = data["next_rowid"]
            t.version = self.commit_seq

    def close(self) -> None:
        if self.storage is not None:
            self.storage.close()

    def analyze(self) -> None:
        """Collect per-column distinct-value counts for the planner (like SQL ANALYZE)."""
        with self.reading():
            for t in self.tables.values():
                t.stats = {c: len({row[c] for row in t.rows.values()} - {None})
                           for c in t.columns}
```

## `minidb/sql.py`

SQL front end. Developed in [Appendix A](appendix-a-sql-parser.md).

```python
"""A SQL front end for a useful subset of SQL, compiled onto minidb's API."""
import re
from dataclasses import dataclass
from decimal import Decimal

from minidb.errors import DatabaseError
from minidb.expr import And, Arith, Col, Compare, Const, Expr, In, IsNull, Not, Or
from minidb.query import Avg, Count, Max, Min, Sum
from minidb.schema import Check, Column, ForeignKey
from minidb.types import Boolean, Date, Integer, Numeric, Real, Text, Timestamp


class SQLError(DatabaseError):
    """The SQL text could not be parsed or compiled."""


# -- 1. tokens ------------------------------------------------------------------------------
KEYWORDS = {
    "SELECT", "DISTINCT", "FROM", "AS", "JOIN", "INNER", "LEFT", "OUTER", "ON", "WHERE",
    "GROUP", "BY", "HAVING", "ORDER", "ASC", "DESC", "LIMIT", "OFFSET", "AND", "OR",
    "NOT", "IS", "NULL", "IN", "TRUE", "FALSE", "INSERT", "INTO", "VALUES", "UPDATE",
    "SET", "DELETE", "CREATE", "TABLE", "INDEX", "UNIQUE", "PRIMARY", "KEY", "DEFAULT",
    "REFERENCES", "CHECK", "CASCADE", "RESTRICT", "USING", "BEGIN", "COMMIT", "ROLLBACK",
}

_TOKEN = re.compile(r"""
      (?P<space>\s+|--[^\n]*)
    | (?P<number>\d+\.\d*|\.\d+|\d+)
    | (?P<string>'(?:[^']|'')*')
    | (?P<name>[A-Za-z_][A-Za-z_0-9]*)
    | (?P<quoted>"(?:[^"]|"")+")
    | (?P<op><=|>=|<>|!=|[=<>(),.*+\-/;?])
""", re.VERBOSE)


@dataclass
class Token:
    kind: str        # 'number' 'string' 'name' 'keyword' 'op' 'end'
    value: object
    pos: int


def tokenize(sql: str) -> list[Token]:
    tokens, pos = [], 0
    while pos < len(sql):
        m = _TOKEN.match(sql, pos)
        if m is None:
            raise SQLError(f"unexpected character {sql[pos]!r} at position {pos}")
        kind, text = m.lastgroup, m.group()
        if kind == "number":
            tokens.append(Token(kind, Decimal(text) if "." in text else int(text), pos))
        elif kind == "string":
            tokens.append(Token(kind, text[1:-1].replace("''", "'"), pos))
        elif kind == "name":
            upper = text.upper()
            tokens.append(Token("keyword", upper, pos) if upper in KEYWORDS
                          else Token("name", text, pos))
        elif kind == "quoted":
            tokens.append(Token("name", text[1:-1].replace('""', '"'), pos))
        elif kind == "op":
            tokens.append(Token("op", "!=" if text == "<>" else text, pos))
        pos = m.end()
    tokens.append(Token("end", None, pos))
    return tokens


# -- 2. syntax tree for statements ------------------------------------------------------------
@dataclass(eq=False, repr=False)       # keep Expr's == (it builds a Compare)
class AggCall(Expr):
    """COUNT(*), SUM(x), ... inside an expression; evaluated after grouping."""
    func: str
    column: str | None

    @property
    def key(self) -> str:
        return f"{self.func}({self.column or '*'})"

    def eval(self, row):
        return row[self.key]

    def __repr__(self):
        return self.key


@dataclass
class Select:
    items: list               # [(Expr, alias or None)] or ["*"]
    distinct: bool
    table: tuple              # (name, alias)
    joins: list               # [(name, alias, on, kind)]
    where: Expr | None
    group_by: list
    having: Expr | None
    order_by: list            # [(Expr, descending)]
    limit: int | None
    offset: int


@dataclass
class Insert:
    table: str
    columns: list | None
    rows: list


@dataclass
class Update:
    table: str
    assignments: dict
    where: Expr | None


@dataclass
class Delete:
    table: str
    where: Expr | None


@dataclass
class CreateTable:
    name: str
    columns: list
    primary_key: tuple
    unique: list
    checks: list
    foreign_keys: list


@dataclass
class CreateIndex:
    name: str
    table: str
    columns: list
    unique: bool
    kind: str


@dataclass
class TransactionControl:
    action: str               # BEGIN, COMMIT, ROLLBACK


# -- 3. the parser ----------------------------------------------------------------------------
class Parser:
    """Recursive descent for statements; Pratt (precedence climbing) for expressions."""

    def __init__(self, sql: str, params=()):
        self.tokens = tokenize(sql)
        self.i = 0
        self.params = list(params)
        self.used_params = 0

    # -- token helpers ------------------------------------------------------------------
    def peek(self, offset: int = 0) -> Token:
        return self.tokens[min(self.i + offset, len(self.tokens) - 1)]

    def next(self) -> Token:
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, *values) -> Token | None:
        tok = self.peek()
        if tok.kind in ("keyword", "op") and tok.value in values:
            self.i += 1
            return tok
        return None

    def expect(self, *values) -> Token:
        tok = self.accept(*values)
        if tok is None:
            got = self.peek()
            raise SQLError(f"expected {' or '.join(values)} at position {got.pos}, "
                           f"got {got.value!r}")
        return tok

    def name(self) -> str:
        tok = self.next()
        if tok.kind != "name":
            raise SQLError(f"expected a name at position {tok.pos}, got {tok.value!r}")
        return tok.value

    def name_list(self) -> list[str]:
        self.expect("(")
        names = [self.name()]
        while self.accept(","):
            names.append(self.name())
        self.expect(")")
        return names

    # -- statements -----------------------------------------------------------------------
    def statement(self):
        tok = self.peek()
        if tok.kind != "keyword":
            raise SQLError(f"expected a statement at position {tok.pos}")
        handler = {"SELECT": self.select, "INSERT": self.insert, "UPDATE": self.update,
                   "DELETE": self.delete, "CREATE": self.create,
                   "BEGIN": self.tx, "COMMIT": self.tx, "ROLLBACK": self.tx}.get(tok.value)
        if handler is None:
            raise SQLError(f"unsupported statement {tok.value}")
        stmt = handler()
        self.accept(";")
        if self.peek().kind != "end":
            raise SQLError(f"unexpected {self.peek().value!r} at position {self.peek().pos}")
        if self.used_params != len(self.params):
            raise SQLError(f"{len(self.params)} parameters given, {self.used_params} used")
        return stmt

    def tx(self):
        return TransactionControl(self.next().value)

    def select(self) -> Select:
        self.expect("SELECT")
        distinct = bool(self.accept("DISTINCT"))
        items = []
        if self.accept("*"):
            items = ["*"]
        else:
            while True:
                e = self.expr()
                alias = self.name() if self.accept("AS") else (
                    self.name() if self.peek().kind == "name" else None)
                items.append((e, alias))
                if not self.accept(","):
                    break
        self.expect("FROM")
        table = self.table_ref()
        joins = []
        while True:
            if self.accept("JOIN") or (self.accept("INNER") and self.expect("JOIN")):
                kind = "inner"
            elif self.accept("LEFT"):
                self.accept("OUTER")
                self.expect("JOIN")
                kind = "left"
            else:
                break
            name, alias = self.table_ref()
            self.expect("ON")
            joins.append((name, alias, self.expr(), kind))
        where = self.expr() if self.accept("WHERE") else None
        group_by = []
        if self.accept("GROUP"):
            self.expect("BY")
            group_by = [self.column_name()]
            while self.accept(","):
                group_by.append(self.column_name())
        having = self.expr() if self.accept("HAVING") else None
        order_by = []
        if self.accept("ORDER"):
            self.expect("BY")
            while True:
                e = self.expr()
                descending = bool(self.accept("DESC"))
                if not descending:
                    self.accept("ASC")
                order_by.append((e, descending))
                if not self.accept(","):
                    break
        limit, offset = None, 0
        if self.accept("LIMIT"):
            limit = self.integer()
            if self.accept("OFFSET"):
                offset = self.integer()
        return Select(items, distinct, table, joins, where, group_by, having,
                      order_by, limit, offset)

    def table_ref(self) -> tuple[str, str | None]:
        name = self.name()
        if self.accept("AS"):
            return name, self.name()
        return (name, self.name()) if self.peek().kind == "name" else (name, None)

    def column_name(self) -> str:
        name = self.name()
        return f"{name}.{self.name()}" if self.accept(".") else name

    def integer(self) -> int:
        e = self.primary()
        if not isinstance(e, Const) or not isinstance(e.value, int):
            raise SQLError("expected an integer")
        return e.value

    def insert(self) -> Insert:
        self.expect("INSERT")
        self.expect("INTO")
        table = self.name()
        columns = self.name_list() if self.peek().value == "(" else None
        self.expect("VALUES")
        rows = []
        while True:
            self.expect("(")
            row = [self.constant()]
            while self.accept(","):
                row.append(self.constant())
            self.expect(")")
            rows.append(row)
            if not self.accept(","):
                break
        return Insert(table, columns, rows)

    def constant(self):
        e = self.expr()
        if not isinstance(e, Const):
            raise SQLError("VALUES must contain constants")
        return e.value

    def update(self) -> Update:
        self.expect("UPDATE")
        table = self.name()
        self.expect("SET")
        assignments = {}
        while True:
            column = self.name()
            self.expect("=")
            assignments[column] = self.expr()
            if not self.accept(","):
                break
        where = self.expr() if self.accept("WHERE") else None
        return Update(table, assignments, where)

    def delete(self) -> Delete:
        self.expect("DELETE")
        self.expect("FROM")
        table = self.name()
        return Delete(table, self.expr() if self.accept("WHERE") else None)

    def create(self):
        self.expect("CREATE")
        unique = bool(self.accept("UNIQUE"))
        if self.accept("INDEX"):
            name = self.name()
            self.expect("ON")
            table = self.name()
            columns = self.name_list()
            kind = "hash"
            if self.accept("USING"):
                kind = self.name().lower()
            return CreateIndex(name, table, columns, unique, kind)
        if unique:
            raise SQLError("expected INDEX after CREATE UNIQUE")
        self.expect("TABLE")
        stmt = CreateTable(self.name(), [], (), [], [], [])
        self.expect("(")
        while True:
            if self.accept("PRIMARY"):
                self.expect("KEY")
                stmt.primary_key = tuple(self.name_list())
            elif self.accept("UNIQUE"):
                stmt.unique.append(tuple(self.name_list()))
            elif self.accept("CHECK"):
                stmt.checks.append(self.check_expr())
            else:
                self.column_def(stmt)
            if not self.accept(","):
                break
        self.expect(")")
        return stmt

    def check_expr(self) -> Expr:
        self.expect("(")
        e = self.expr()
        self.expect(")")
        return e

    def column_def(self, stmt: CreateTable) -> None:
        name = self.name()
        type_ = self.type_name()
        options = {}
        while True:
            if self.accept("NOT"):
                self.expect("NULL")
                options["nullable"] = False
            elif self.accept("NULL"):
                options["nullable"] = True
            elif self.accept("PRIMARY"):
                self.expect("KEY")
                stmt.primary_key = (name,)
            elif self.accept("UNIQUE"):
                stmt.unique.append((name,))
            elif self.accept("DEFAULT"):
                options["default"] = self.constant()
            elif self.accept("CHECK"):
                stmt.checks.append(self.check_expr())
            elif self.accept("REFERENCES"):
                ref_table = self.name()
                ref_cols = self.name_list() if self.peek().value == "(" else ()
                on_delete = "restrict"
                if self.accept("ON"):
                    self.expect("DELETE")
                    if self.accept("CASCADE"):
                        on_delete = "cascade"
                    elif self.accept("SET"):
                        self.expect("NULL")
                        on_delete = "set null"
                    else:
                        self.expect("RESTRICT")
                stmt.foreign_keys.append(ForeignKey((name,), ref_table, tuple(ref_cols), on_delete))
            else:
                break
        stmt.columns.append(Column(name, type_, **options))

    def type_name(self):
        name = self.name().upper()
        args = []
        if self.accept("("):
            args = [self.integer()]
            while self.accept(","):
                args.append(self.integer())
            self.expect(")")
        if name in ("INT", "INTEGER", "BIGINT"):
            return Integer()
        if name in ("REAL", "FLOAT", "DOUBLE"):
            return Real()
        if name in ("TEXT", "VARCHAR", "CHAR"):
            return Text(*args[:1])
        if name in ("BOOL", "BOOLEAN"):
            return Boolean()
        if name in ("NUMERIC", "DECIMAL"):
            return Numeric(*args) if args else Numeric()
        if name == "DATE":
            return Date()
        if name == "TIMESTAMP":
            return Timestamp()
        raise SQLError(f"unknown type {name}")

    # -- expressions: precedence climbing ------------------------------------------------
    # binding power of each infix operator: higher binds tighter
    INFIX = {"OR": 10, "AND": 20, "=": 40, "!=": 40, "<": 40, "<=": 40, ">": 40,
             ">=": 40, "IS": 40, "IN": 40, "NOT": 40, "+": 50, "-": 50, "*": 60, "/": 60}

    def expr(self, min_bp: int = 0) -> Expr:
        left = self.prefix()
        while True:
            tok = self.peek()
            op = tok.value if tok.kind in ("op", "keyword") else None
            bp = self.INFIX.get(op)
            if bp is None or bp <= min_bp:
                return left
            self.next()
            if op == "OR":
                left = Or(left, self.expr(bp))
            elif op == "AND":
                left = And(left, self.expr(bp))
            elif op == "IS":
                negate = bool(self.accept("NOT"))
                self.expect("NULL")
                left = Not(IsNull(left)) if negate else IsNull(left)
            elif op in ("IN", "NOT"):
                if op == "NOT":
                    self.expect("IN")
                left = In(left, self.in_list()) if op == "IN" else Not(In(left, self.in_list()))
            elif op in ("+", "-", "*", "/"):
                left = Arith(op, left, self.expr(bp))
            else:
                left = Compare(op, left, self.expr(bp))

    def in_list(self) -> list:
        self.expect("(")
        values = [self.constant()]
        while self.accept(","):
            values.append(self.constant())
        self.expect(")")
        return values

    def prefix(self) -> Expr:
        if self.accept("NOT"):
            return Not(self.expr(30))
        if self.accept("-"):
            operand = self.expr(70)
            if isinstance(operand, Const) and operand.value is not None:
                return Const(-operand.value)
            return Arith("-", Const(0), operand)
        return self.primary()

    def primary(self) -> Expr:
        tok = self.next()
        if tok.kind in ("number", "string"):
            return Const(tok.value)
        if tok.kind == "keyword" and tok.value in ("TRUE", "FALSE", "NULL"):
            return Const({"TRUE": True, "FALSE": False, "NULL": None}[tok.value])
        if tok.value == "?":
            if self.used_params >= len(self.params):
                raise SQLError("not enough parameters")
            self.used_params += 1
            return Const(self.params[self.used_params - 1])
        if tok.value == "(":
            e = self.expr()
            self.expect(")")
            return e
        if tok.kind == "name":
            if self.peek().value == "(" and tok.value.upper() in AGGREGATES:
                self.next()
                column = None if self.accept("*") else self.column_name()
                self.expect(")")
                return AggCall(tok.value.upper(), column)
            if self.accept("."):
                return Col(f"{tok.value}.{self.name()}")
            return Col(tok.value)
        raise SQLError(f"unexpected {tok.value!r} at position {tok.pos}")


AGGREGATES = {"COUNT": Count, "SUM": Sum, "AVG": Avg, "MIN": Min, "MAX": Max}


# -- 4. execution ------------------------------------------------------------------------------
class Connection:
    """Runs SQL against a Database. Statements autocommit unless inside BEGIN/COMMIT."""

    def __init__(self, db):
        self.db = db
        self.uow = None

    def execute(self, sql: str, params=()):
        stmt = Parser(sql, params).statement()
        if isinstance(stmt, TransactionControl):
            return self._transaction_control(stmt.action)
        if isinstance(stmt, (CreateTable, CreateIndex)):
            if self.uow is not None:
                raise SQLError("DDL is not allowed inside a transaction")
            return self._ddl(stmt)
        if self.uow is not None:
            return self._run(stmt, self.uow)
        if isinstance(stmt, Select):
            with self.db.unit_of_work(readonly=True) as uow:
                return self._run(stmt, uow)
        return self.db.transaction(lambda uow: self._run(stmt, uow))

    def _transaction_control(self, action: str):
        if action == "BEGIN":
            if self.uow is not None:
                raise SQLError("already in a transaction")
            self.uow = self.db.unit_of_work()
        else:
            if self.uow is None:
                raise SQLError(f"{action} without BEGIN")
            uow, self.uow = self.uow, None
            if action == "COMMIT":
                try:
                    uow.commit()
                except BaseException:
                    uow.rollback()
                    raise
            else:
                uow.rollback()
        return None

    def _ddl(self, stmt):
        if isinstance(stmt, CreateIndex):
            self.db.create_index(stmt.table, stmt.name, stmt.columns, stmt.unique, stmt.kind)
            return None
        checks = [Check(f"check_{i + 1}", e) for i, e in enumerate(stmt.checks)]
        self.db.create_table(stmt.name, stmt.columns, primary_key=stmt.primary_key,
                             unique=tuple(stmt.unique), checks=checks,
                             foreign_keys=stmt.foreign_keys)
        return None

    def _run(self, stmt, uow):
        if isinstance(stmt, Insert):
            names = stmt.columns or list(uow.table(stmt.table).columns)
            for values in stmt.rows:
                if len(values) != len(names):
                    raise SQLError(f"{len(names)} columns but {len(values)} values")
                uow.insert(stmt.table, dict(zip(names, values)))
            return len(stmt.rows)
        if isinstance(stmt, Update):
            records = uow.find(stmt.table, stmt.where)
            for record in records:                     # evaluate against the old row,
                new = {c: e.eval(record) for c, e in stmt.assignments.items()}
                record.update(new)                     # then let dirty checking save it
            uow.flush()
            return len(records)
        if isinstance(stmt, Delete):
            return uow.delete(stmt.table, stmt.where)
        return self._select(stmt, uow)

    def _select(self, s: Select, uow) -> list[dict]:
        q = uow.query(s.table[0], s.table[1])
        for name, alias, on, kind in s.joins:
            q = q.join(name, on, alias, kind)
        if s.where is not None:
            q = q.where(s.where)
        aggs = {}
        for e in _all_exprs(s):
            for call in _agg_calls(e):
                aggs[call.key] = AGGREGATES[call.func](call.column)
        if s.group_by or aggs:
            q = q.group_by(*s.group_by, **aggs)
        if s.having is not None:
            q = q.having(s.having)
        if s.order_by:
            aliases = {} if s.items == ["*"] else {a: e for e, a in s.items if a}
            q = q.order_by(*[_sort_key(aliases.get(e.name, e) if isinstance(e, Col) else e, d)
                             for e, d in s.order_by])
        if s.items != ["*"]:
            outputs = {}
            for e, alias in s.items:
                name = alias or (e.name.rpartition(".")[2] if isinstance(e, Col) else repr(e))
                outputs[name] = e
            q = q.select(**outputs)
        if s.distinct:
            q = q.distinct()
        if s.limit is not None or s.offset:
            q = q.limit(s.limit, s.offset)
        return q.all()


def _sort_key(e: Expr, descending: bool):
    if isinstance(e, (Col, AggCall)):            # by name: works in either direction
        return ("-" if descending else "") + (e.name if isinstance(e, Col) else e.key)
    if descending:
        raise SQLError("ORDER BY <expression> DESC is not supported; use an alias")
    return e


def _all_exprs(s: Select):
    if s.items != ["*"]:
        yield from (e for e, _ in s.items)
    if s.having is not None:
        yield s.having
    yield from (e for e, _ in s.order_by)


def _agg_calls(e):
    if isinstance(e, AggCall):
        yield e
    for child in ("left", "right", "item"):
        if isinstance(getattr(e, child, None), Expr):
            yield from _agg_calls(getattr(e, child))
    for item in getattr(e, "items", ()):
        yield from _agg_calls(item)


def connect(db) -> Connection:
    return Connection(db)
```

## `tests/test_minidb.py`

Test suite. Developed in [Appendix B](appendix-b-testing.md).

```python
"""Tests for minidb: unit, property-based, model-based, concurrency and crash tests."""
import os
import random
import shutil
import tempfile
import threading
import time
import unittest

from minidb import *
from minidb.btree import BPlusTree, BTreeIndex
from minidb.index import SortedIndex
from minidb.locks import FairRWLock


# -- an integrity checker: the invariants every test can assert ------------------------------
def index_entries(index) -> int:
    if isinstance(index, BTreeIndex):
        return sum(len(rowids) for _, rowids in index.tree.items())
    if isinstance(index, SortedIndex):
        return len(index._sorted)
    return sum(len(rowids) for rowids in index._entries.values())


def check_integrity(db: Database) -> None:
    """Raise AssertionError if any index, key or reference is inconsistent."""
    for t in db.tables.values():
        for index in t.indexes.values():
            keyed = 0
            for rowid, row in t.rows.items():
                key = index.key_of(row)
                if key is None:
                    continue
                keyed += 1
                found = index.lookup(key)
                assert rowid in found, f"{t.name}.{index.name}: row {rowid} missing"
                assert not index.unique or len(found) == 1, f"{index.name}: duplicate {key}"
            assert keyed == index_entries(index), f"{t.name}.{index.name}: stale entries"
        for row in t.rows.values():
            t.schema.prepare_row({}, base=row)          # re-runs NOT NULL and CHECKs
    for fk in db.foreign_keys:
        parent = db.tables[fk.ref_table]
        for row in db.tables[fk.table].rows.values():
            key = fk.parent_key(row)
            assert key is None or parent.lookup(key), f"{fk.name}: orphan {row}"


# -- unit tests -----------------------------------------------------------------------------
class TypeTests(unittest.TestCase):
    def test_integer_rejects_bool(self):
        with self.assertRaises(DomainError):
            Integer().normalize(True)

    def test_numeric_rounds_half_even(self):
        self.assertEqual(str(Numeric(6, 2).normalize("2.665")), "2.66")

    def test_round_trip_through_primitives(self):
        for t, v in [(Numeric(8, 2), "12.30"), (Date(), "2026-11-18"),
                     (Timestamp(), "2026-11-18T10:00:00+00:00"), (Real(), 0.1)]:
            value = t.normalize(v)
            self.assertEqual(t.from_primitive(t.to_primitive(value)), value)


# -- property-based: compare a data structure with a trivially correct model -----------------
class BTreeProperties(unittest.TestCase):
    def test_matches_a_dict(self):
        for order in (3, 4, 7, 32):
            rnd, tree, model = random.Random(order), BPlusTree(order), {}
            for _ in range(5000):
                k, v = rnd.randrange(500), rnd.randrange(4)
                if rnd.random() < 0.6:
                    tree.insert(k, v)
                    model.setdefault(k, set()).add(v)
                else:
                    tree.remove(k, v)
                    if v in model.get(k, ()):
                        model[k].discard(v)
                        if not model[k]:
                            del model[k]
            self.assertEqual([(k, s) for k, s in tree.items()], sorted(model.items()))
            lo, hi = 100, 300
            self.assertEqual([k for k, _ in tree.items(lo, hi, False, True)],
                             [k for k in sorted(model) if lo < k <= hi])


# -- model-based: random operations on minidb and on a dict, compared after each step ----------
class ModelBasedTest(unittest.TestCase):
    def test_random_operations(self):
        rnd = random.Random(42)
        db = Database()
        db.create_table("users", [Column("id", Integer()), Column("email", Text()),
                                  Column("age", Integer(), check=lambda a: a >= 0)],
                        primary_key="id", unique=["email"])
        db.create_index("users", "by_age", ["age"], kind="btree")
        model: dict[int, dict] = {}
        for step in range(1500):
            uid, email, age = rnd.randrange(60), f"u{rnd.randrange(60)}@x", rnd.randrange(-3, 90)
            op = rnd.choice(["insert", "update", "delete"])
            row = {"id": uid, "email": email, "age": age}
            if op == "insert":
                if age < 0:
                    expected = CheckViolation
                elif uid in model or any(r["email"] == email for r in model.values()):
                    expected = UniqueViolation
                else:
                    expected, model[uid] = None, row
                action = lambda: db.insert("users", row)
            elif op == "update":
                taken = any(r["email"] == email and i != uid for i, r in model.items())
                if uid in model and age < 0:
                    expected = CheckViolation
                elif uid in model and taken:
                    expected = UniqueViolation
                else:
                    expected = None
                    if uid in model:
                        model[uid] = model[uid] | {"email": email, "age": age}
                action = lambda: db.update("users", {"email": email, "age": age}, {"id": uid})
            else:
                expected = None
                model.pop(uid, None)
                action = lambda: db.delete("users", {"id": uid})
            if expected is None:
                action()
            else:
                with self.assertRaises(expected, msg=f"step {step}: {op} {row}"):
                    action()
            if step % 50 == 0:
                check_integrity(db)
        self.assertEqual(sorted(db.select("users"), key=lambda r: r["id"]),
                         [model[k] for k in sorted(model)])
        check_integrity(db)


# -- concurrency: invariants, fairness ----------------------------------------------------------
class ConcurrencyTests(unittest.TestCase):
    def test_transfers_preserve_total(self):
        db = Database()
        db.create_table("acct", [Column("id", Integer()), Column("bal", Integer(min=0))],
                        primary_key="id")
        for i in range(5):
            db.insert("acct", {"id": i, "bal": 100})

        def worker(seed):
            rnd = random.Random(seed)
            for _ in range(100):
                a, b = rnd.sample(range(5), 2)
                def move(uow):
                    src, dst = uow.find("acct", {"id": a})[0], uow.find("acct", {"id": b})[0]
                    if src["bal"] >= 10:
                        src["bal"] -= 10
                        dst["bal"] += 10
                db.transaction(move)

        threads = [threading.Thread(target=worker, args=(s,)) for s in range(6)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(r["bal"] for r in db.select("acct")), 500)
        check_integrity(db)

    def test_fair_lock_bounds_writer_wait(self):
        lock, stop, waited = FairRWLock(), threading.Event(), []

        def reader(offset):
            time.sleep(offset)
            while not stop.is_set():
                with lock.read():
                    time.sleep(0.005)

        readers = [threading.Thread(target=reader, args=(i * 0.002,)) for i in range(4)]
        for r in readers: r.start()
        time.sleep(0.05)
        t0 = time.perf_counter()
        with lock.write():
            waited.append(time.perf_counter() - t0)
        stop.set()
        for r in readers: r.join()
        self.assertLess(waited[0], 0.1)       # a reader-preferring lock waits until stop


# -- crash recovery: every possible torn write recovers to a prefix of the commits --------------
class CrashTests(unittest.TestCase):
    def test_every_truncation_recovers_a_prefix(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)

        def open_db(path):
            db = Database()
            db.create_table("t", [Column("id", Integer()), Column("v", Text())], primary_key="id")
            db.attach(Storage(path, sync=False))
            return db

        db = open_db(folder)
        states = [[]]                                      # state after each commit
        for i in range(12):
            if i % 4 == 3:
                db.delete("t", {"id": i - 2})
            else:
                db.insert("t", {"id": i, "v": "x" * i})
            states.append(sorted(r["id"] for r in db.select("t")))
        db.close()
        log = open(os.path.join(folder, "wal.log"), "rb").read()
        for cut in range(0, len(log) + 1, 3):
            copy = tempfile.mkdtemp()
            try:
                with open(os.path.join(copy, "wal.log"), "wb") as f:
                    f.write(log[:cut])
                recovered = open_db(copy)
                ids = sorted(r["id"] for r in recovered.select("t"))
                self.assertEqual(ids, states[recovered.commit_seq], f"cut at byte {cut}")
                recovered.close()
            finally:
                shutil.rmtree(copy)


if __name__ == "__main__":
    unittest.main()
```

---

[🏠 Contents](index.md) · [Next: References →](references.md)
