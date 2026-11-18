[🏠 Contents](index.md) · [← Previous: Appendix C — The Complete Code](appendix-c-complete-code.md)

# Appendix D — Answers to the Exercises

This appendix answers every question and exercise in the book. Where an answer includes code, the code uses the same conventions as the chapters ([§1.4](01-relational-model.md#14-how-to-read-the-code-in-this-book)). Each answer's listings were applied to a copy of the package *as it stands at the end of that chapter*, and the result was checked like the chapters themselves: `ruff format`, `ruff check`, `pyrefly check`, docstring doctests and every `>>>` session. The answers to one exercise are independent of the others: each starts again from the chapter's code.

Research questions are answered briefly, with a pointer to the source. Many design questions have more than one good answer; the one given is a reasonable choice, not the only one.

## Chapter 1 — What a Relational Database Is

### 1.1

"What is the total of all order amounts?" Suppose two orders both have `total = 25`. Projected onto `total` *as a set*, the relation is `{25}`, and its sum is 25. As a bag it is `[25, 25]`, and its sum is 50, the correct answer. Any aggregate that counts or adds (`COUNT`, `SUM`, `AVG`) changes meaning when duplicates disappear. That is the main reason SQL tables are bags, and why SQL makes you ask for `DISTINCT` explicitly.

### 1.2

`lrow | rrow` builds the joined row from both rows' attributes. If both have `id`, the right row's value silently overwrites the left's: the joined row has one `id`, and you can no longer tell which table it came from. The fix is to *qualify* attribute names with the relation they come from (`users.id`, `orders.id`) before merging, which is what [Chapter 7](07-query-primitives.md#72-rows-with-qualified-names) does with aliases.

### 1.3

Both operators need *union-compatible* relations: the same attributes, with the same domains. Otherwise "the same tuple" means nothing.

```python
# examples/toy.py (append)
def union(r: Relation, s: Relation) -> Relation:
    """Return the rows in ``r`` or in ``s``, without duplicates.

    >>> union([{"a": 1}], [{"a": 1}, {"a": 2}])
    [{'a': 1}, {'a': 2}]

    :param r: a relation.
    :param s: a relation with the same attributes as ``r``.
    :return: the rows of both, each once.
    :raises ValueError: if the relations are not union-compatible.
    """
    _check_compatible(r, s)
    seen: set[tuple[tuple[str, object], ...]] = set()
    out: Relation = []
    for row in r + s:
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def difference(r: Relation, s: Relation) -> Relation:
    """Return the rows of ``r`` that are not in ``s``.

    >>> difference([{"a": 1}, {"a": 2}], [{"a": 1}])
    [{'a': 2}]

    :param r: a relation.
    :param s: a relation with the same attributes as ``r``.
    :return: the rows of ``r`` missing from ``s``.
    :raises ValueError: if the relations are not union-compatible.
    """
    _check_compatible(r, s)
    other = {tuple(sorted(row.items())) for row in s}
    return [row for row in r if tuple(sorted(row.items())) not in other]


def _check_compatible(r: Relation, s: Relation) -> None:
    headings = {frozenset(row) for row in r + s}
    if len(headings) > 1:
        raise ValueError("relations are not union-compatible")
```

### 1.4

*Advantage:* a lambda can express any condition Python can, with no new language to learn and no parser to write. *Disadvantage:* the database can only call it, not look inside it. It can't see that `lambda u: u["id"] == 7` is an equality on `id` that an index could answer, so every query has to scan everything. [Chapter 14](14-query-planning.md) solves this by making predicates data (expression trees) while keeping them callable.

### 1.5

a) **Durability**: a confirmed commit was lost. b) **Isolation**: the report saw a transaction's intermediate state. (It would also be an atomicity failure if the transfer had crashed half way and stayed that way.) c) **Consistency**: a constraint (quantity ≥ 0) was broken.

### 1.6

Codd names **ordering dependence** (programs relying on the order in which records are stored), **indexing dependence** (programs relying on which indexes exist) and **access path dependence** (programs relying on the pointer structures, trees or networks, that link records). The relational model removes all three: order is something you request, indexes are invisible to queries, and there are no paths to navigate.

## Chapter 2 — Tables and CRUD

### 2.1

A rowid is a name for a row, and names outlive the things they name: in an index, an undo log, a write-ahead log, a transaction's read set, or an application's cache. Suppose row 3 is deleted and a new row reuses rowid 3, and then the system crashes. Recovery replays a log record written *before* the delete, "update row 3", and applies it to the new, unrelated row. The same mix-up happens when an undo log restores "row 3" or a cache serves the old row 3's data. Never reusing rowids makes every reference either right or obviously dangling.

### 2.2

The test keeps a reference to the stored dict, updates through the table, and checks that the old dict is unchanged:

```python
>>> from minidb.table import Table
>>> t = Table("t", ["n"])
>>> _ = t.insert({"n": 1})
>>> stored = t.rows[1]
>>> t.update({"n": 2})
1
>>> stored                     # an in-place update would show {'n': 2}
{'n': 1}
>>> t.rows[1] is stored
False
```

### 2.3

The callable must be called *after* the matching rows are decided, once per row, and before any row is written. Calling it inside the modify loop is fine here, because each call only reads its own old row, but computing all new rows first keeps the rule obvious, and matters once validation can fail ([Chapter 3](03-types-and-normalization.md)).

```python
# src/minidb/table.py (replace Table.update)
    def update(
        self,
        changes: Mapping[str, object] | Callable[[Mapping[str, object]], Mapping[str, object]],
        where: Where = None,
    ) -> int:
        """Set new values on every row that satisfies ``where``.

        >>> t = Table("t", ["n"])
        >>> _ = t.insert({"n": 1})
        >>> t.update(lambda row: {"n": row["n"] + 1})
        1
        >>> t.select()
        [{'n': 2}]

        :param changes: the new values by column name, or a function that
            computes them from the old row.
        :param where: decides which rows change; ``None`` (the default)
            changes every row.
        :return: the number of rows changed.
        :raises SchemaError: if the changes name an unknown column.
        """
        targets = self.match(where)  # 1. decide
        new_rows: dict[int, Row] = {}
        for rowid in targets:  # 2. compute every new row
            row_changes = changes(MappingProxyType(self.rows[rowid])) if callable(changes) else changes
            self._check_columns(row_changes)
            new_rows[rowid] = self.rows[rowid] | dict(row_changes)
        self.rows.update(new_rows)  # 3. modify
        return len(targets)
```

### 2.4

```python
# src/minidb/database.py (add to Database)
    def count(self, table: str, where: Where = None) -> int:
        """Count the rows of ``table`` that satisfy ``where``, without copying any.

        >>> db = Database()
        >>> _ = db.create_table("t", ["n"])
        >>> for n in range(5):
        ...     _ = db.insert("t", {"n": n})
        >>> db.count("t", lambda row: row["n"] % 2 == 0)
        3

        :param table: the table's name.
        :param where: decides which rows count; ``None`` (the default) counts all.
        :return: the number of matching rows.
        """
        t = self.table(table)
        if where is None:
            return len(t)
        return sum(1 for row in t.rows.values() if where(MappingProxyType(row)))
```

```python
# src/minidb/database.py (imports)
from types import MappingProxyType
```

### 2.5

```python
for rowid, row in list(self.rows.items()):   # iterate over a copy
    if where is None or where(MappingProxyType(row)):
        self.rows[rowid] = row | dict(changes)
```

It does *not* suffer from the Halloween problem. The copy is taken before any change, so each row is visited exactly once, whatever the update does. (Replacing a value for an existing key also doesn't change a dict's size, so even iterating the live dict would be safe here.) If instead the loop followed a structure ordered by the updated column, an index on salary say, a row whose salary increases moves *ahead* of the cursor. The loop meets it again and updates it again, and again, until it no longer matches. That is exactly the System R story.

### 2.6

The generator iterates over the live dict, so an insert while it is suspended changes the dict's size, and the next `next()` raises `RuntimeError: dictionary changed size during iteration`:

```python
>>> from minidb.table import Table
>>> t = Table("t", ["n"])
>>> _ = t.insert({"n": 1})
>>> _ = t.insert({"n": 2})
>>> rows = t.scan()
>>> next(rows)
(1, {'n': 1})
>>> _ = t.insert({"n": 3})
>>> next(rows)
Traceback (most recent call last):
  ...
RuntimeError: dictionary changed size during iteration
```

A snapshot (`list(self.rows.items())` at the start) fixes it, and gives the caller a consistent view as of the start of the scan. It costs O(n) time and memory before the first row is produced, which destroys the benefit of a lazy scan when the caller only wants the first few rows. A middle way is to copy only the rowids and look each row up lazily, skipping rows deleted in the meantime. It's still O(n) memory, but ints are cheap. Transactions solve the problem properly ([Chapters 9](09-unit-of-work-ii.md)–[12](12-isolation.md)).

### 2.7

With `("age", ">", 40)` the database can see *which column* and *which comparison* are involved, so it can use an index on `age` instead of scanning. It can also estimate how many rows will match, reorder conditions to evaluate cheap or selective ones first, push a condition down below a join, or serialize the query to send it elsewhere. [Chapter 14](14-query-planning.md) does the first, second and fourth.

## Chapter 3 — Types and Normalization

### 3.1

`isinstance` accepts subclasses. `True` (and `False`) would pass as integers, since `bool` subclasses `int`, and a `datetime` would pass as a `date`, since `datetime` subclasses `date`. Both lead to subtle bugs: `True == 1`, so a unique index would treat `True` and `1` as the same key, and comparing a `date` with a `datetime` raises `TypeError`. An `IntEnum` member is another example: it would be stored as an int, but would print differently.

### 3.2

A normalizer that appends a unit suffix changes the value every time it runs, and every update re-runs normalizers on the columns it touches:

```python
>>> from minidb import Column, Database, Integer, Text
>>> def add_unit(value):
...     return f"{value} kg" if isinstance(value, str) else value
>>> db = Database()
>>> _ = db.create_table("parcels", [Column("id", Integer()), Column("weight", Text(), normalizers=(add_unit,))])
>>> _ = db.insert("parcels", {"id": 1, "weight": "3"})
>>> row = db.get("parcels", 1)
>>> db.update("parcels", {"weight": row["weight"]})       # write back what we read
1
>>> db.get("parcels", 1)["weight"]
'3 kg kg'
```

Reading a value and writing it back unchanged must be a no-op. With a non-idempotent normalizer it corrupts data.

### 3.3

Case-folding is a separate policy, so it belongs in a normalizer (`normalizers=(lower,)`). The type then only states the domain, and stays strict: `"DRAFT"` is rejected unless the column asks for lower-casing.

```python
# src/minidb/types.py (append)
@dataclass(frozen=True, init=False)
class Choice(Type[str]):
    """Hold one of a fixed set of strings: an enumeration.

    >>> status = Choice("draft", "sent", "paid")
    >>> status.normalize("sent")
    'sent'
    >>> status.validate("DRAFT")
    Traceback (most recent call last):
      ...
    minidb.errors.DomainError: 'DRAFT' is not a valid Choice(allowed=('draft', 'sent', 'paid')): expected one of draft, sent, paid

    :param allowed: the valid values.
    """

    allowed: tuple[str, ...]
    exact_types: ClassVar[tuple[type, ...]] = (str,)

    def __init__(self, *allowed: str) -> None:
        object.__setattr__(self, "allowed", allowed)

    @override
    def coerce(self, value: object) -> str:
        if not isinstance(value, str):
            raise self.error(value)
        return value

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, str) and value not in self.allowed:
            raise self.error(value, f"expected one of {', '.join(self.allowed)}")
```

### 3.4

A stored value must be immutable for the same reason rows are copied on the way out ([§2.3](02-tables-and-crud.md#copies-out-never-references)): a shallow copy of a row shares its values, so a caller could change a nested list inside a stored row and bypass every check, and the change would not even update the indexes. Values also have to be hashable to be index keys.

Our `Value` union has no tuple or mapping types, so the simplest immutable canonical form that fits it is *canonical JSON text*: sorted keys and fixed separators, so that equal documents are equal strings. Strings are immutable and hashable, and comparisons and indexes work on them unchanged.

```python
# src/minidb/types.py (append)
@dataclass(frozen=True)
class Json(Type[str]):
    """Hold a JSON document, stored as canonical JSON text.

    Dicts, lists and JSON text are all accepted; the stored form has sorted
    keys and no spaces, so equal documents are equal strings.

    >>> Json().normalize({"b": [1, 2], "a": None}) == Json().normalize('{"a": null, "b": [1,2]}')
    True

    :raises DomainError: if the input is not JSON-serializable, or not valid JSON text.
    """

    exact_types: ClassVar[tuple[type, ...]] = (str,)

    @override
    def coerce(self, value: object) -> str:
        try:
            document: object = json.loads(value) if isinstance(value, str) else value
            return json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except TypeError, ValueError:
            raise self.error(value, "not a JSON document") from None
```

```python
# src/minidb/types.py (imports)
import json
```

Readers call `json.loads` on the stored string to get a fresh, private copy of the document.

### 3.5

`"99.995"` rounds half-even to `100.00`, which has three digits before the point, more than `NUMERIC(4, 2)` allows. The error says "too many digits", but the user wrote five digits with two before the point and can't see why. A better message shows the rounded value and the limit:

```python
# src/minidb/types.py (replace Numeric.validate)
    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if not isinstance(value, Decimal):
            return
        if value.as_tuple().exponent != -self.scale:
            raise self.error(value, f"expected exactly {self.scale} decimal places")
        limit = Decimal(10) ** (self.precision - self.scale)
        if abs(value) >= limit:
            raise self.error(
                value,
                f"NUMERIC({self.precision}, {self.scale}) holds values below {limit} in magnitude "
                f"(after rounding to {self.scale} decimal places)",
            )
```

```python
>>> from minidb.types import Numeric
>>> t = Numeric(4, 2)
>>> t.validate(t.normalize("99.995"))
Traceback (most recent call last):
  ...
minidb.errors.DomainError: Decimal('100.00') is not a valid Numeric(precision=4, scale=2): NUMERIC(4, 2) holds values below 100 in magnitude (after rounding to 2 decimal places)
```

### 3.6

Python's `float('nan') != float('nan')` can't be changed, so "NaN equals NaN" has to come from somewhere else: normalize every NaN to *one shared object*. `dict` and `set` lookups check identity before equality, so that one object then finds itself in a hash index. Sorting is harder: comparisons with NaN are always false, so `Sort` would put NaNs in arbitrary places, and `MIN`/`MAX` would depend on input order. Every place that compares values (`Sort`, aggregates, sorted indexes, the B-tree, range scans and `Compare` in expressions) would need a NaN-aware key that puts NaN last, so the choice would leak into the whole system.

```python
# src/minidb/types.py (replace Real)
@dataclass(frozen=True)
class Real(Type[float]):
    """Hold floating-point numbers; NaN only with ``allow_nan``, and never infinities.

    All NaNs are normalized to the single object :data:`NAN`, so a NaN equals
    itself wherever identity is checked first (dicts, sets, indexes).

    >>> Real(allow_nan=True).normalize("nan") is NAN
    True

    :param allow_nan: whether NaN is a valid value; ``False`` by default.
    """

    allow_nan: bool = False
    exact_types: ClassVar[tuple[type, ...]] = (float,)

    @override
    def coerce(self, value: object) -> float:
        if isinstance(value, bool):
            raise self.error(value, "booleans are not numbers")
        if isinstance(value, int | float | Decimal):
            number = float(value)
        elif isinstance(value, str):
            number = self._parse(value)
        else:
            raise self.error(value)
        return NAN if math.isnan(number) else number

    def _parse(self, value: str) -> float:
        try:
            return float(value.strip())
        except ValueError:
            raise self.error(value) from None

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if not isinstance(value, float) or math.isfinite(value):
            return
        if not (self.allow_nan and value is NAN):
            raise self.error(value, "NaN and infinities are not allowed")


NAN = float("nan")
```

### 3.7

The customer's name and address are repeated in every order of that customer, and the product's price in every order of that product. Changing an address means changing many rows, and missing one leaves the data contradicting itself. Normalized:

- `customers(customer_id, name, address)`, key `customer_id`;
- `products(product_id, name, price)`, key `product_id`;
- `orders(order_id, customer_id → customers, placed_at)`, key `order_id`;
- `order_lines(order_id → orders, product_id → products, quantity, unit_price)`, key `(order_id, product_id)`.

`unit_price` is deliberately copied into `order_lines`: it is the price *at the time of the order*, a different fact from the product's current price.

## Chapter 4 — Constraints

### 4.1

`NULL OR TRUE` is TRUE; `NULL AND FALSE` is FALSE; `NOT (NULL = NULL)` is `NOT UNKNOWN`, which is UNKNOWN. A `CHECK` passes unless it is FALSE, so the first and third pass and only the second is rejected.

### 4.2

Run every non-callable default through the column's pipeline when the schema is built. Callable defaults can't be checked at definition time: their value is only known when they are called (`now()` returns something different every time), and calling them early might have side effects. They are still checked on every insert.

```python
# src/minidb/schema.py (replace TableSchema.__post_init__)
    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise SchemaError(f"duplicate column names in {self.name!r}")
        object.__setattr__(self, "by_name", {c.name: c for c in self.columns})
        for c in self.columns:
            if not callable(c.default):
                self._check_default(c)

    def _check_default(self, c: Column) -> None:
        """Reject a constant default that its own column would refuse."""
        try:
            value = c.prepare(c.default)
        except DomainError as e:
            raise SchemaError(f"{self.name}.{c.name}: invalid default: {e}") from None
        if value is not None and c.check is not None and c.check(value) is False:
            raise SchemaError(f"{self.name}.{c.name}: default {value!r} fails the column's check")
```

```python
>>> from minidb import Column, Database, Integer
>>> Database().create_table("t", [Column("qty", Integer(), default=-1, check=lambda q: q >= 0)])
Traceback (most recent call last):
  ...
minidb.errors.SchemaError: t.qty: default -1 fails the column's check
```

### 4.3

```python
# src/minidb/schema.py (append)
def unknown_if_null(*cols: str) -> Callable[[RowCheck], RowCheck]:
    """Wrap a row check so that it returns ``None`` (UNKNOWN) when any of ``cols`` is NULL.

    >>> check = unknown_if_null("a")(lambda row: row["a"] > 0)
    >>> check({"a": None}), check({"a": 1})
    (None, True)

    :param cols: the columns the check reads.
    :return: a decorator for row checks.
    """

    def decorate(predicate: RowCheck) -> RowCheck:
        @functools.wraps(predicate)
        def wrapped(row: Mapping[str, Value | None]) -> object:
            if any(row[c] is None for c in cols):
                return None
            return predicate(row)

        return wrapped

    return decorate
```

```python
# src/minidb/schema.py (imports)
import functools
```

```python
>>> from minidb import Check
>>> from minidb.schema import unknown_if_null
>>> rule = Check("discount_le_price", unknown_if_null("discount", "price")(lambda r: r["discount"] <= r["price"]))
>>> rule.predicate({"discount": None, "price": 5}) is None
True
```

### 4.4

Give `Check` a `columns: frozenset[str]` field. `prepare_row` already knows the updated columns (`values`), so it can run only the checks whose `columns` intersect them, plus every check on inserts. An index from column to checks makes the selection cheap. If a declaration is incomplete, a check that reads `discount` but declares only `price` is skipped when only `discount` changes, and the constraint can be silently broken. The data then violates a rule that the database claims to enforce, and later updates to `price` start failing for reasons nobody can see. A safer variant computes the columns automatically: from an expression's `columns()` ([Chapter 14](14-query-planning.md)), or by running the check once against a recording mapping that notes which keys it reads.

### 4.5

The normalized value is the one that is stored, so it is the one the constraint is about. Checking the raw input would let two equal stored values get different verdicts. Example: `Column("code", Text(), normalizers=(strip,), check=lambda s: len(s) == 3)`. The input `" ABC "` fails on the raw value (length 5) and passes on the normalized `"ABC"`, which is what will be stored. In the other direction, `check=lambda s: s == s.strip()` passes on any normalized value and fails on raw padded input.

### 4.6

```python
>>> import datetime as dt
>>> from minidb import Column, Database, Integer, Timestamp
>>> def now() -> dt.datetime:
...     return dt.datetime.now(dt.UTC)
>>> db = Database()
>>> _ = db.create_table("events", [Column("id", Integer()), Column("at", Timestamp(), default=now)])
>>> _ = db.insert("events", {"id": 1})
>>> db.get("events", 1)["at"].tzinfo
datetime.timezone.utc
```

Each row's default is computed when that row is prepared, so 1,000 rows inserted by one statement get 1,000 slightly different timestamps. That's usually wrong. The rows were inserted "at the same time" as far as the application is concerned, and queries such as "everything inserted by this statement" can't find them by timestamp. PostgreSQL's `now()` returns the *transaction's* start time, so everything a transaction does carries one timestamp, consistent across tables and statements. In minidb that would mean taking the time once in the Unit of Work ([Chapter 9](09-unit-of-work-ii.md)) and passing it to `prepare_row`.

### 4.7

When a constraint is re-enabled, minidb must **validate every existing row**, because rows written while it was disabled may violate it, and refuse to re-enable (or report the offending rows) if any do. For uniqueness and foreign keys that means rebuilding or re-checking the indexes, exactly like `create_index` on existing data ([Chapter 5](05-keys-and-indexes.md)). PostgreSQL's `ALTER TABLE … VALIDATE CONSTRAINT` does exactly this, and it can run without blocking writes, because new writes are already being checked.

## Chapter 5 — Keys and Indexes

### 5.1

`delete_rows` removes rows one by one, and each `remove` calls `index.remove`, which discards the rowid from the very set being iterated. With the internal set, iteration fails with `RuntimeError: Set changed size during iteration`, or, if the set were replaced rather than mutated, could skip rows. More generally, a caller that keeps the result while the table changes would see it change under its feet.

### 5.2

Yes, `(1, NULL)` may appear any number of times. Under the SQL standard a key containing NULL is never equal to another key, so the UNIQUE constraint can't be violated. That is what our index does, since `key_of` returns `None` and the row isn't indexed. PostgreSQL 15's `UNIQUE NULLS NOT DISTINCT` treats NULLs as equal for uniqueness purposes, so a second `(1, NULL)` is rejected. In minidb that would mean indexing keys with NULLs in unique indexes, but still never matching them in lookups.

### 5.3

Two rows with ids 1 and 2, and a batch that sets row 1's id to 2 and row 2's id to 1 (a swap). Without the subtraction, checking the new key 2 for row 1 finds row 2 in the index, which still holds the *old* key, and rejects the batch, although row 2 is changing its key in the same batch. Even a batch that sets row 1's id to 1 (no change) would be rejected without the subtraction, because row 1 finds itself.

### 5.4

```python
# src/minidb/table.py (add to Table)
    def insert_many(self, rows: Iterable[Mapping[str, object]]) -> list[int]:
        """Validate and insert several rows: all of them, or none.

        >>> from minidb.schema import Column, TableSchema
        >>> from minidb.types import Integer
        >>> t = Table(TableSchema("t", (Column("id", Integer()),), primary_key=("id",)))
        >>> t.insert_many([{"id": 1}, {"id": 2}])
        [1, 2]
        >>> t.insert_many([{"id": 3}, {"id": 3}])
        Traceback (most recent call last):
          ...
        minidb.errors.UniqueError: t: duplicate key (id=3) violates 'pk'
        >>> len(t)
        2

        :param rows: the new rows' values.
        :return: their rowids, in order.
        :raises ConstraintError: if any row breaks a constraint.
        """
        prepared = [self.schema.prepare_row(values) for values in rows]
        self.check_unique([(None, row) for row in prepared])
        rowids = [self.new_rowid() for _ in prepared]
        for rowid, row in zip(rowids, prepared, strict=True):
            self.put(rowid, row)
        return rowids
```

### 5.5

It is already atomic. The new index is built in a local variable and only added to `self.indexes` after every row has been added successfully. If a duplicate is found, the exception leaves the half-built index unreferenced, and it is garbage collected. The order of the last two statements is what makes this so: register the index only after it is complete.

### 5.6

```python
# examples/index_cost.py
"""Time inserts into a table with 0, 1, 3 and 6 secondary indexes."""

import timeit

from minidb import Column
from minidb import Database
from minidb import Integer

ROWS = 100_000


def time_inserts(indexes: int) -> float:
    """Insert ``ROWS`` rows into a fresh table with ``indexes`` hash indexes.

    :param indexes: how many secondary indexes to create.
    :return: the time taken, in seconds.
    """
    db = Database()
    db.create_table("t", [Column(f"c{i}", Integer()) for i in range(6)])
    for i in range(indexes):
        db.create_index("t", f"i{i}", [f"c{i}"])

    def run() -> None:
        for n in range(ROWS):
            db.insert("t", {f"c{i}": n + i for i in range(6)})

    return timeit.timeit(run, number=1)


def main() -> None:
    """Print the time and the time per index for each configuration."""
    base = time_inserts(0)
    print(f"{'indexes':>8}{'time':>9}{'extra per index':>17}")
    for k in (0, 1, 3, 6):
        t = base if k == 0 else time_inserts(k)
        per = "" if k == 0 else f"{(t - base) / k * 1e6 / ROWS:>11.2f} µs/row"
        print(f"{k:>8}{t:>8.2f}s{per:>17}")


if __name__ == "__main__":
    main()
```

On the machine used for the book (100,000 rows each time):

```text
 indexes     time  extra per index
       0    0.60s
       1    0.63s       0.31 µs/row
       3    0.89s       0.97 µs/row
       6    1.14s       0.90 µs/row
```

The cost per index is roughly constant, about a microsecond per row per index (the first is cheaper than its share, partly noise): one key extraction, one dict lookup and one set insertion. The fixed part of each insert (validation, rowid allocation, building the row) is about 6 µs and dominates, so even six indexes make an insert less than twice as slow. Indexes on many columns, or B-trees with expensive splits, would show a larger per-index cost.

### 5.7

Suppose `wanted = {"country": "UK", "user_id": 7}`, with one index on `(country, city)` that covers only `country`, and another on `user_id`. Both cover one requested column, so they tie. Now drop `city` from the first, so the indexes are `(country)` and `(user_id)`. `country = 'UK'` matches half the table, and `user_id = 7` matches one row. "Most columns" can't tell them apart, and "first found" may pick the terrible one. Covering more columns isn't the goal either: an index on `(country, active)` covers two columns but might match millions of rows, while `user_id` matches one. What the choice needs is the **selectivity** of each index, roughly the table size divided by the number of distinct keys, so as to pick the index with the fewest expected matches. That is what [Chapter 14](14-query-planning.md) does.

### 5.8

A clustered index (SQLite, InnoDB) makes **primary-key lookups and range scans by primary key** cheap: the row is in the index leaf, so one tree descent finds it, and neighbouring keys are neighbouring rows on disk. Secondary indexes store the primary key and need a second lookup. A heap (PostgreSQL) makes **inserts** cheap, since rows go wherever there is room. It also makes **secondary indexes** uniform and direct, because they point at a physical row location. Updates that don't change indexed columns can stay on the same page (PostgreSQL's HOT updates). [Petrov 2019](references.md#petrov2019) discusses both in chapter 1.

## Chapter 6 — Referential Integrity

### 6.1

A foreign key says "this row belongs to *that* row". If the referenced columns were not unique, a child value could match several parents, or none of them in particular. A cascade or restrict would have to guess which parent the child belongs to, and deleting one of two matching parents would leave the reference still "satisfied" by the other, though it no longer means what it did. Uniqueness makes "the parent" a function of the child row.

### 6.2

Python's recursion limit is about 1,000 frames by default. A self-referential chain such as categories with `parent_id`, or a linked list of versions 5,000 deep, would raise `RecursionError` in a recursive cascade, half way through planning. Raising the limit risks crashing the interpreter's C stack. An explicit stack (a Python list) grows on the heap and handles any depth.

### 6.3

Add an `on_update` action to `ForeignKey`, and plan key updates like deletes: find the children of every row whose referenced key changes, and plan updates that rewrite their foreign-key columns, recursively. If a cascaded update changes a column that is itself referenced (the child's own key), its children must be cascaded, restricted or checked in turn. That is the "recursively", and the `seen` set prevents infinite loops in cycles. Here is the cascade, planned before anything is written:

```python
# src/minidb/schema.py (replace ForeignKey)
@dataclass(frozen=True)
class ForeignKey:
    """Declare that ``table.columns`` must match ``ref_table.ref_columns``, or be NULL.

    :param columns: the referencing columns; a single name is also accepted.
    :param ref_table: the referenced table.
    :param ref_columns: the referenced key; ``()`` (the default) for its primary key.
    :param on_delete: ``"restrict"`` (the default), ``"cascade"`` or ``"set null"``.
    :param on_update: ``"restrict"`` (the default) or ``"cascade"``: whether
        changing a referenced key is refused, or copied into the children.
    :param table: the child table; :meth:`Database.create_table` fills it in.
    :raises SchemaError: for an unknown action.
    """

    columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...] = ()
    on_delete: OnDelete = "restrict"
    on_update: Literal["restrict", "cascade"] = "restrict"
    table: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", as_key(self.columns))
        object.__setattr__(self, "ref_columns", as_key(self.ref_columns))
        if self.on_delete not in ON_DELETE_ACTIONS or self.on_update not in ("restrict", "cascade"):
            raise SchemaError(f"unknown referential action in {self!r}")

    @property
    def name(self) -> str:
        """Return the constraint's name, derived from the child table and columns."""
        return f"fk_{self.table}_{'_'.join(self.columns)}"

    def parent_key(self, child_row: Mapping[str, Value | None]) -> dict[str, Value | None] | None:
        """Return ``{ref_column: value}`` for the parent ``child_row`` points at, or ``None``."""
        values = [child_row[c] for c in self.columns]
        if any(v is None for v in values):
            return None
        return dict(zip(self.ref_columns, values, strict=True))

    def child_key(self, parent_row: Mapping[str, Value | None]) -> dict[str, Value | None]:
        """Return ``{column: value}`` that the children of ``parent_row`` have."""
        return {c: parent_row[r] for c, r in zip(self.columns, self.ref_columns, strict=True)}
```

```python
# src/minidb/database.py (replace Database.update)
    def update(self, table: str, changes: Mapping[str, object], where: Where = None) -> int:
        """Update rows, cascading key changes to children declared ``on_update="cascade"``.

        :param table: the table's name.
        :param changes: the new values, by column name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: the number of rows changed in ``table`` itself.
        :raises ConstraintError: if a new row breaks a constraint.
        :raises ForeignKeyError: if a changed key is referenced with ``restrict``.
        """
        t = self.table(table)
        old = {rid: t.rows[rid] for rid in t.match(where)}
        new = {rid: t.schema.prepare_row(changes, base=row) for rid, row in old.items()}
        self._check_parents_exist(t, new.values())
        plan: dict[RowRef, Row] = {(table, rid): row for rid, row in new.items()}
        self._cascade_keys(table, old, new, plan)
        for name in {n for n, _ in plan}:
            self.tables[name].check_unique([(rid, r) for (n, rid), r in plan.items() if n == name])
        for (name, rid), row in plan.items():
            self.tables[name].put(rid, row)
        return len(new)

    def _cascade_keys(self, table: str, old: dict[int, Row], new: dict[int, Row], plan: dict[RowRef, Row]) -> None:
        """Add to ``plan`` the child updates that changing these keys implies."""
        for fk in self._references_to(table):
            for rid, before in old.items():
                if fk.child_key(before) != fk.child_key(new[rid]):
                    self._follow(fk, before, new[rid], plan)

    def _follow(self, fk: ForeignKey, before: Row, after: Row, plan: dict[RowRef, Row]) -> None:
        children = self._children(fk, before)
        if children and fk.on_update == "restrict":
            raise ForeignKeyError(f"{fk.name}: cannot change {fk.ref_table} key, it is still referenced")
        child = self.tables[fk.table]
        old = {c: child.rows[c] for c in children if (fk.table, c) not in plan}
        new = {c: child.schema.prepare_row(fk.child_key(after), base=row) for c, row in old.items()}
        plan.update({(fk.table, c): row for c, row in new.items()})
        self._cascade_keys(fk.table, old, new, plan)  # the children's own keys may have changed
```

```python
>>> from minidb import Column, Database, ForeignKey, Integer
>>> db = Database()
>>> _ = db.create_table("users", [Column("id", Integer())], primary_key="id")
>>> _ = db.create_table("orders", [Column("id", Integer()), Column("user_id", Integer())],
...     primary_key="id", foreign_keys=[ForeignKey(("user_id",), "users", on_update="cascade")])
>>> _ = db.insert("users", {"id": 1})
>>> _ = db.insert("orders", {"id": 10, "user_id": 1})
>>> db.update("users", {"id": 7}, where={"id": 1})
1
>>> db.select("orders")
[{'id': 10, 'user_id': 7}]
```

A complete version would also re-check the cascaded rows' other foreign keys, and treat the whole cascade as one batch per table for uniqueness. The `check_unique` loop above already does the latter.

### 6.4

It fails. The parent check looks the row up in the table's key index *before* the row is stored, so `{"id": 1, "manager_id": 1}` finds no employee 1. The fix is to let a row's own values satisfy its own references:

```python
# src/minidb/database.py (replace Database._check_parents_exist)
    def _check_parents_exist(self, child: Table, rows: Iterable[Row], fks: list[ForeignKey] | None = None) -> None:
        """Check, from the child side, that every non-NULL reference finds its parent.

        A row may reference itself: a self-referencing foreign key is also
        satisfied by the row's own key.
        """
        for fk in fks if fks is not None else self._references_from(child.name):
            parent = self.tables[fk.ref_table]
            for row in rows:
                key = fk.parent_key(row)
                if key is not None and not parent.lookup(key) and not _references_itself(fk, row, key):
                    raise ForeignKeyError(f"{fk.name}: no {parent.name} row with {key}")
```

```python
# src/minidb/database.py (append)
def _references_itself(fk: ForeignKey, row: Row, key: dict[str, Value | None]) -> bool:
    """Tell whether ``row`` is its own parent under ``fk``."""
    return fk.table == fk.ref_table and all(row[c] == v for c, v in key.items())
```

```python
# src/minidb/database.py (typing imports)
from minidb.values import Value
```

```python
>>> from minidb import Column, Database, ForeignKey, Integer
>>> db = Database()
>>> _ = db.create_table("emp", [Column("id", Integer()), Column("manager_id", Integer())],
...     primary_key="id", foreign_keys=[ForeignKey(("manager_id",), "emp")])
>>> db.insert("emp", {"id": 1, "manager_id": 1})
1
```

### 6.5

Not in minidb: one `update` call changes one table, so it can't also change the children in another table. (For a self-referencing table it can: `UPDATE emp SET id = id + 100, manager_id = manager_id + 100` changes both a key and every reference to it, and our row-by-row check would refuse it, wrongly.) In SQL the same statement is fine when the constraint is `NO ACTION` (the default), because the check happens at the end of the statement. With `RESTRICT` it is refused, because that check is immediate.

### 6.6

```python
# src/minidb/database.py (replace Database._check_no_orphans)
    def _check_no_orphans(self, parent: Table, old: dict[int, Row], new: dict[int, Row]) -> None:
        """Check, from the parent side of an update, that no referenced key changes."""
        for fk in self._references_to(parent.name):
            for rid, before in old.items():
                if fk.child_key(before) != fk.child_key(new[rid]) and self._children(fk, before):
                    key = {r: before[r] for r in fk.ref_columns}
                    raise ForeignKeyError(
                        f"{fk.name}: cannot change {parent.name} key {key}: "
                        f"{fk.table} rows still reference it through {', '.join(fk.columns)}"
                    )
```

### 6.7

`NO ACTION`. Pass 1 performs every cascade first. Pass 2 then refuses only if a referencing row *survives* the whole statement, so rows deleted by the same statement are allowed to have referenced each other. That is the "check at the end of the statement" semantics of `NO ACTION`. A true `RESTRICT` refuses as soon as any referenced row is about to be deleted, even if its children would be deleted too.

### 6.8

Without the child index, deleting each user scans all 100,000 orders to find its children: 10,000 × 100,000 = 10⁹ row checks, which takes many minutes in pure Python. With the index, each user costs one hash lookup, and the whole delete is dominated by the 10,000 deletions themselves. To measure the slow case without waiting for hours, the example below uses 2,000 users and 20,000 orders, and drops the automatic index to compare:

```python
# examples/fk_index_cost.py
"""Time deleting every user, with and without the index on orders.user_id."""

import time

from minidb import Column
from minidb import Database
from minidb import ForeignKey
from minidb import Integer

USERS, ORDERS = 2_000, 20_000


def build(*, indexed: bool) -> Database:
    """Create users and orders; ``ON DELETE CASCADE`` makes every delete find children.

    :param indexed: whether to keep the automatic index on ``orders.user_id``.
    :return: the filled database.
    """
    db = Database()
    db.create_table("users", [Column("id", Integer())], primary_key="id")
    db.create_table(
        "orders",
        [Column("id", Integer()), Column("user_id", Integer())],
        primary_key="id",
        foreign_keys=[ForeignKey(("user_id",), "users", on_delete="cascade")],
    )
    for i in range(USERS):
        db.insert("users", {"id": i})
    for i in range(ORDERS):
        db.insert("orders", {"id": i, "user_id": i % USERS})
    if not indexed:
        orders = db.table("orders")
        orders.indexes = {"pk": orders.indexes["pk"]}
        orders.lookup = lambda key: set(orders.match(key))  # find children by scanning
    return db


def main() -> None:
    """Print the time to delete every user in both configurations."""
    for indexed in (True, False):
        db = build(indexed=indexed)
        t0 = time.perf_counter()
        db.delete("users")
        print(f"child index {'on ' if indexed else 'off'}: {time.perf_counter() - t0:7.2f} s")


if __name__ == "__main__":
    main()
```

```text
child index on :    0.09 s
child index off:   23.38 s
```

Without the index the time grows with *users × orders*; with it, with *users + orders*. At the exercise's full size (10,000 users, 100,000 orders) the difference is about 25 times larger again.

## Chapter 7 — Query Primitives

### 7.1

`dict.get` doesn't call `__missing__`, so `row.get("age")` returns `None` even though `row["age"]` works: a silent NULL, the worst kind of wrong answer. Override `get`:

```python
# src/minidb/operators.py (add to Row)
    @override
    def get[T](self, key: str, default: T | None = None, /) -> Value | T | None:
        """Return the value of ``key``, qualified or not, or ``default``.

        >>> Row({"u.age": 36}).get("age")
        36

        :param key: a qualified or unqualified column name.
        :param default: the value for a missing column; ``None`` by default.
        :return: the column's value, or ``default``.
        :raises KeyError: if an unqualified ``key`` is ambiguous.
        """
        try:
            return self[key]
        except KeyError as e:
            if "ambiguous" in str(e):
                raise
            return default
```

`in` has the same problem: `"age" in row` calls `__contains__`, which is False. `setdefault` and `pop` also bypass `__missing__`. Only `get` and `__contains__` matter for readers; the mutating methods are best left alone, since operators build new rows rather than change old ones.

### 7.2

On the book's machine, a million `r["age"]` lookups on a seven-column row take about 0.58 s: each one fails the dict lookup, calls `__missing__` and scans every key. Looking up the qualified name through a precomputed `{"age": "u.age"}` mapping takes 0.035 s, about 16 times faster.

The table depends only on the *shape* of the rows (their column names), not on any row's values, so it should be computed once per operator and shared by all its rows. One place for it is the operator: `columns()` already knows the names, so each operator can build `{unqualified: qualified}` for the names that are unique, once, in `__iter__`. The rows then need a reference to it. A `Row` subclass with a `__slots__` attribute pointing at the shared table costs one pointer per row, and `__missing__` becomes one dict lookup. `NestedLoopJoin` merges its children's tables, dropping names that become ambiguous, and `Project` builds a new one. A better place still is *before* execution: the planner resolves every name in the query once, and the operators only ever see qualified names. That is what real databases do, during *binding*.

### 7.3

`Union` streams: it yields each row the first time it sees it, so the memory it needs is the set of distinct rows seen, but it never makes a consumer wait. `Intersect` and `Except` must read their *right* input completely before they can decide about the first left row, so they are blocking on the right, and streaming on the left.

```python
# src/minidb/operators.py (append)
class _SetOperation(Operator):
    """Combine two inputs with the same number of columns, as sets.

    Rows are compared by their values, in column order; the output uses the
    left input's column names.

    :param left: the first input.
    :param right: the second input.
    :raises ValueError: if the inputs have different numbers of columns.
    """

    def __init__(self, left: Operator, right: Operator) -> None:
        if len(left.columns()) != len(right.columns()):
            raise ValueError("set operations need inputs with the same number of columns")
        self.children = (left, right)


class Union(_SetOperation):
    """Yield the rows of either input, each distinct row once."""

    @override
    def __iter__(self) -> Iterator[Row]:
        names = self.columns()
        seen: set[tuple[Value | None, ...]] = set()
        for child in self.children:
            for row in child:
                key = tuple(row.values())
                if key not in seen:
                    seen.add(key)
                    yield Row(zip(names, key, strict=True))


class _Filtered(_SetOperation):
    """Yield the distinct left rows whose presence on the right is ``keep``."""

    keep: ClassVar[bool]

    @override
    def __iter__(self) -> Iterator[Row]:
        left, right = self.children
        other = {tuple(row.values()) for row in right}  # blocking on the right
        seen: set[tuple[Value | None, ...]] = set()
        for row in left:
            key = tuple(row.values())
            if (key in other) == self.keep and key not in seen:
                seen.add(key)
                yield row


class Intersect(_Filtered):
    """Yield the distinct rows that appear in both inputs."""

    keep = True


class Except(_Filtered):
    """Yield the distinct rows of the left input that are not in the right one."""

    keep = False
```

```python
# src/minidb/operators.py (imports)
from typing import ClassVar
```

```python
>>> from minidb import Column, Database, Integer
>>> from minidb.operators import Except, Intersect, Scan, Union
>>> db = Database()
>>> for name, ns in (("a", (1, 2, 2, 3)), ("b", (2, 3, 4))):
...     _ = db.create_table(name, [Column("n", Integer())])
...     for n in ns:
...         _ = db.insert(name, {"n": n})
>>> a, b = Scan(db.table("a")), Scan(db.table("b"))
>>> [r["n"] for r in Union(a, b)], [r["n"] for r in Intersect(a, b)], [r["n"] for r in Except(a, b)]
([1, 2, 3, 4], [2, 3], [1])
```

### 7.4

`itertools.groupby` does exactly what sort aggregation needs: it splits a sorted input into runs of equal keys.

```python
# src/minidb/operators.py (append)
class SortAggregate(Aggregate):
    """Aggregate an input that is already sorted by the group key.

    Each group is a run of consecutive rows, so only one group's
    accumulators exist at a time, and groups come out in key order, as
    soon as each one ends. On unsorted input a key appears in several
    groups.
    """

    @override
    def __iter__(self) -> Iterator[Row]:
        runs = itertools.groupby(self.children[0], key=lambda row: tuple(row[c] for c in self.group_by))
        empty = True
        for key, rows in runs:
            empty = False
            accs = self._fresh()
            for row in rows:
                self._accumulate(accs, row)
            yield self._output(key, accs)
        if empty and not self.group_by:  # aggregate of no rows
            yield self._output((), self._fresh())

    def _output(self, key: tuple[Value | None, ...], accs: list[Accumulator]) -> Row:
        out = Row(zip(self.group_by, key, strict=True))
        out.update((name, acc.result()) for name, acc in zip(self.aggregates, accs, strict=True))
        return out

    @property
    @override
    def label(self) -> str:
        return "Sort" + super().label
```

```python
>>> from minidb import Column, Database, Integer
>>> from minidb.operators import Count, Scan, Sort, SortAggregate
>>> db = Database()
>>> _ = db.create_table("t", [Column("g", Integer())])
>>> for g in (2, 1, 2, 1, 1):
...     _ = db.insert("t", {"g": g})
>>> list(SortAggregate(Sort(Scan(db.table("t")), [("t.g", False)]), ["t.g"], {"n": Count()}))
[{'t.g': 1, 'n': 3}, {'t.g': 2, 'n': 2}]
```

Sort aggregation wins when the input *already arrives sorted* by the group key (from a sorted index, a sort that the query needs anyway for `ORDER BY`, or a merge join), so the sort costs nothing. It needs memory for one group instead of all of them, which matters with millions of groups. It streams: the first group comes out before the last row is read. And its output is sorted, which a following `ORDER BY` on the same key can use. If the input isn't sorted, the sort costs O(n log n), and hash aggregation's O(n) is better whenever the groups fit in memory.

### 7.5

`heapq.nsmallest(n, rows, key)` keeps a heap of the `n` best rows while it reads the input once, and is documented to give the same result as `sorted(rows, key=key)[:n]`, ties included. Mixed ascending and descending keys can't be expressed as one key tuple (you can't negate a string), so the key is built from a comparison function:

```python
# src/minidb/operators.py (append)
class TopN(Operator):
    """Yield the first ``n`` rows in sort order, without sorting the whole input.

    :param child: the input.
    :param keys: ``(column name or function, descending)`` pairs, as for :class:`Sort`.
    :param n: how many rows to keep.
    """

    def __init__(self, child: Operator, keys: list[SortKey], n: int) -> None:
        self.children = (child,)
        self.keys, self.n = keys, n
        self._getters = [(_getter(k), descending) for k, descending in keys]

    @override
    def __iter__(self) -> Iterator[Row]:
        return iter(heapq.nsmallest(self.n, self.children[0], key=functools.cmp_to_key(self._compare)))

    def _compare(self, a: Row, b: Row) -> int:
        for get, descending in self._getters:
            x, y = _nulls_first(get(a)), _nulls_first(get(b))
            if x != y:
                sign = -1 if descending else 1
                return sign if x > y else -sign
        return 0

    @property
    @override
    def label(self) -> str:
        return f"TopN {self.n} by " + ", ".join(f"{k}{' DESC' if d else ''}" for k, d in self.keys)
```

```python
# src/minidb/operators.py (imports)
import functools
import heapq
```

```python
>>> from minidb import Column, Database, Integer
>>> from minidb.operators import Scan, TopN
>>> db = Database()
>>> _ = db.create_table("t", [Column("n", Integer())])
>>> for n in (5, 1, 4, None, 3):
...     _ = db.insert("t", {"n": n})
>>> [r["n"] for r in TopN(Scan(db.table("t")), [("n", True)], 2)]
[5, 4]
```

For N input rows, `Sort` + `Limit` costs O(N log N) time and O(N) memory. `TopN` costs O(N log n) time and O(n) memory: for `LIMIT 10` over a million rows, it keeps ten rows instead of a million. It is still blocking, since the last input row might be the best one.

### 7.6

A `Numeric` column holds exact decimals, so its average should be an exact decimal too, not a float with binary rounding errors. `Decimal / int` already returns a `Decimal`, but with up to 28 significant digits (`Decimal("10.00") / 3` is `3.333333333333333333333333333`). Like PostgreSQL, we keep a few more decimal places than the input has. Here, four more:

```python
# src/minidb/operators.py (replace _AvgAcc)
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
        if isinstance(self.total, Decimal):  # exact in, exact out: 4 more decimal places
            exponent = cast("int", self.total.as_tuple().exponent)
            return (self.total / self.n).quantize(Decimal(1).scaleb(exponent - 4))
        return cast("Value", arithmetic(self.total) / arithmetic(self.n))
```

```python
# src/minidb/operators.py (imports)
from decimal import Decimal
```

```python
>>> from decimal import Decimal
>>> from minidb.operators import Avg
>>> acc = Avg("price").accumulator()
>>> for v in ("10.00", "10.00", "20.00"):
...     acc.add(Decimal(v))
>>> acc.result()
Decimal('13.333333')
```

Integer averages stay `float`s, as before.

### 7.7

A right join is a left join with the inputs swapped, but swapping changes the column order, so it is simpler to remember which right rows found a partner. A full outer join needs this memory too: a right row's lack of a match is only known after *every* left row has been tried, so the join keeps one flag per right row and emits the unmatched ones at the end.

```python
# src/minidb/operators.py (replace JoinKind)
type JoinKind = Literal["inner", "left", "right", "full"]
```

```python
# src/minidb/operators.py (replace NestedLoopJoin)
class NestedLoopJoin(Operator):
    """Join every pair of rows for which ``on`` is true.

    The right input is read once into a list: an operator may not be safely
    iterable twice, or may be expensive to re-run.

    :param left: the outer input.
    :param right: the inner input.
    :param on: the join condition; ``None`` (the default) joins every pair.
    :param kind: ``"inner"`` (the default); ``"left"``, ``"right"`` or
        ``"full"`` also keep the unmatched rows of the left input, the right
        input or both, padded with NULLs.
    :raises ValueError: for any other ``kind``.
    """

    def __init__(
        self, left: Operator, right: Operator, on: RowPredicate | None = None, kind: JoinKind = "inner"
    ) -> None:
        if kind not in ("inner", "left", "right", "full"):
            raise ValueError("kind must be 'inner', 'left', 'right' or 'full'")
        self.children = (left, right)
        self.on, self.kind = on, kind

    @override
    def __iter__(self) -> Iterator[Row]:
        left, right = self.children
        inner = list(right)  # materialize once: blocking
        matched = [False] * len(inner)
        right_nulls = dict.fromkeys(right.columns())
        for lrow in left:
            rows = self._pairs(lrow, inner, matched)
            yield from rows
            if not rows and self.kind in ("left", "full"):
                yield Row(lrow | right_nulls)
        if self.kind in ("right", "full"):
            left_nulls = dict.fromkeys(left.columns())
            yield from (Row(left_nulls | r) for r, m in zip(inner, matched, strict=True) if not m)

    def _pairs(self, lrow: Row, inner: list[Row], matched: list[bool]) -> list[Row]:
        """Return the joined rows for ``lrow``, flagging the right rows that matched."""
        rows: list[Row] = []
        for i, r in enumerate(inner):
            if self._matches(row := Row(lrow | r)):
                matched[i] = True
                rows.append(row)
        return rows

    def _matches(self, row: Row) -> bool:
        return self.on is None or self.on(row) is True

    @override
    def columns(self) -> list[str]:
        return self.children[0].columns() + self.children[1].columns()

    @property
    @override
    def label(self) -> str:
        return f"NestedLoopJoin ({self.kind})"
```

```python
>>> from minidb import Column, Database, Integer
>>> from minidb.operators import NestedLoopJoin, Scan
>>> db = Database()
>>> for name, ns in (("a", (1, 2)), ("b", (2, 3))):
...     _ = db.create_table(name, [Column("n", Integer())])
...     for n in ns:
...         _ = db.insert(name, {"n": n})
>>> on = lambda r: r["a.n"] == r["b.n"]
>>> list(NestedLoopJoin(Scan(db.table("a")), Scan(db.table("b")), on, "full"))
[{'a.n': 1, 'b.n': None}, {'a.n': 2, 'b.n': 2}, {'a.n': None, 'b.n': 3}]
```

### 7.8

While a scan iterates over `table.rows` (a dict), another thread deletes from it:

- The scan raises `RuntimeError: dictionary changed size during iteration`, half way through the query.
- On a free-threaded build, the dict's internal state may be seen mid-resize. CPython protects dicts with per-object locks, so it doesn't crash the interpreter, but the iteration still fails or skips entries.
- If the delete happened between two `next()` calls and the size stayed the same (one insert, one delete), the scan may skip a row or see a row inserted after it started: the result matches no single state of the table.
- An aggregate counts some deleted rows and not others, so `COUNT(*)` matches neither the before nor the after state.
- A join reads the right table once (materialized), and the left lazily, so it may pair rows from different moments: an order whose user was deleted after the right side was read.
- A cascading delete removes a parent and then its children, as separate steps. A scan between them sees children without a parent, a state that the foreign key says can't exist.
- An index lookup (in later chapters) may find a rowid whose row was just removed, and raise `KeyError`.

## Chapter 8 — The Unit of Work, Version 1

### 8.1

Write the undo log as c₁, …, cₖ, where each cᵢ took the state from Sᵢ₋₁ to Sᵢ. The changes were applied in order, so each `before` of cᵢ is exactly what the row was in Sᵢ₋₁, and its `after` what it is in Sᵢ. Applying `inverted(cₖ)` to Sₖ writes cₖ's `before` back, which gives Sₖ₋₁: the row is in the state cₖ left it, so the inverse's precondition holds, and all other rows are untouched. By induction, applying the inverses from k down to 1 reaches S₀. A row changed several times is no problem: each inverse undoes one step, in reverse order, and the earliest `before` is applied last. The argument relies on each `Change` recording the **complete before-image** (the whole row, or absence for inserts), not a delta, so its inverse doesn't depend on any later state, and on the changes being **applied and inverted in exactly the recorded order**.

### 8.2

Yes. `apply` re-validates constraints: if the undo restores a row whose unique key has since been taken by someone else, or whose parent was deleted, it raises. That can't happen while the Unit of Work holds the database exclusively, and in version 1 nothing else runs in between. It can also fail for reasons outside the data, such as `MemoryError`, or a `KeyboardInterrupt` arriving in the middle. If it does fail, the database is in an unknown, half-undone state, and nothing correct can be done automatically. The right reaction is to **stop**: mark the database as corrupted and refuse further use, rather than let other transactions build on a broken state. Undo must therefore apply changes *without* checking constraints (they held before), which is what real systems do.

### 8.3

In version 1 the Unit of Work only *records* operations in `_pending`, and nothing touches the tables until `commit()`. So rollback just throws the list away: there is nothing to undo. It won't stay trivial once operations are applied as they happen, or once commit can fail half way. In [Chapter 9](09-unit-of-work-ii.md), changes go to an overlay, and rollback discards the overlay, which is still cheap. The undo log becomes essential where changes reach the tables: for a commit that fails half way, and for crash recovery ([Chapter 13](13-persistence.md)).

### 8.4

Not usually. Rowids only need to be *unique*, not dense: nobody relies on rowids being consecutive, and there are 2⁶³ of them. Gaps are what you get for not having to coordinate. Sequences behave the same way for the same reason. If a sequence rolled back, a transaction that took value 41 would block every other transaction wanting a number until it committed or aborted, because if it aborted, 41 must be given out again. Making sequences non-transactional lets thousands of concurrent inserts take numbers without waiting for each other. Applications that need gapless numbers (invoice numbers, in some legal systems) must use a counter row updated in the transaction, and accept that it serializes those transactions.

### 8.5

```python
# src/minidb/uow.py (add to UnitOfWork)
    def savepoint(self) -> int:
        """Mark the current position, to roll back to later.

        >>> from minidb import Column, Database, Integer
        >>> db = Database()
        >>> _ = db.create_table("t", [Column("n", Integer())])
        >>> with db.unit_of_work() as uow:
        ...     _ = uow.insert("t", {"n": 1})
        ...     sp = uow.savepoint()
        ...     _ = uow.insert("t", {"n": 2})
        ...     uow.rollback_to(sp)
        >>> db.select("t")
        [{'n': 1}]

        :return: the savepoint, for :meth:`rollback_to`.
        :raises TransactionError: if the Unit of Work has finished.
        """
        self._require_active()
        return len(self._pending)

    def rollback_to(self, savepoint: int) -> None:
        """Discard every operation recorded after ``savepoint``.

        :param savepoint: a value returned by :meth:`savepoint`.
        :raises TransactionError: if the Unit of Work has finished, or the
            savepoint is not one of its positions.
        """
        self._require_active()
        if not 0 <= savepoint <= len(self._pending):
            raise TransactionError(f"no such savepoint: {savepoint}")
        del self._pending[savepoint:]
```

Rolling back to a savepoint invalidates later savepoints. That's the SQL rule too, and here it happens automatically, because those positions are past the end of the list. With immediate application, a savepoint would be a position in the *undo* log instead: `rollback_to` applies the inverses of the changes after that position, newest first, and truncates the log. It is the same proof as [8.1](#81), stopped part way.

### 8.6

No. The dataclass is frozen, so you can't rebind `change.after`, but `change.after["qty"] = 0` mutates the dict it holds. It doesn't matter in practice, *because* rows are never updated in place ([§2.3](02-tables-and-crud.md#updates-replace-the-row)): every update creates a new dict, so the dict in a `Change` is never one that anything else changes, and nobody holding it has a reason to. Being sure would mean storing `MappingProxyType` views or tuples, at the cost of a copy per change.

### 8.7

Replicate **effects** (row-based). An operation's effect depends on the state it runs against, and on things that aren't data: `now()`, random numbers, `LIMIT` without `ORDER BY` (which rows?), triggers, and the order in which concurrent statements ran. If the replica's state or timing differs at all, the same operation produces a different result, and the copies drift apart silently. Effects say exactly which rows became what, so applying them reproduces the primary's state. The cost is volume: `UPDATE t SET x = 0` on a million rows is one statement but a million row images. MySQL offers both, and its documentation lists the statements that are unsafe for statement-based replication. Its default has been row-based since 5.7.7, and a *mixed* mode logs statements and switches to rows when a statement is unsafe.

## Chapter 9 — The Unit of Work, Version 2

### 9.1

`insert` plans `Change(t, 5, None, row)`: `_record` puts `overlay[5] = row` and appends the change. `delete` plans `Change(t, 5, row, None)`: `overlay[5] = None`, appended too. At commit, `net_changes` folds the two into `Change(t, 5, None, None)`, first before and last after, and drops it because both are `None`. Nothing reaches the tables. The rowid 5 was taken from the table's counter by `new_rowid` and is never given out again: a gap, as in [Exercise 8.4](#84).

### 9.2

Iterating the committed rows and looking each one up in the overlay costs one extra dict lookup per row and *no* extra memory, and the first row comes out at once. With 3 changes over 1,000,000 rows that is 1,000,000 cheap lookups plus 3 overlay rows. Building a merged dict first costs the same million lookups, plus a million-entry dict (tens of megabytes) built before the caller sees a single row, and thrown away afterwards. A `Limit 10` over the lazy scan stops after ten rows; over the merged dict, it still pays for all million.

### 9.3

The assignment succeeds: `Record` is a plain `dict`, so `record["nonexistent"] = 1` raises nothing. At the next flush (the next operation, query or commit), the dirty check finds the new key in the diff, plans an update with it, and `prepare_row` raises `SchemaError: unknown column`. The error points at that later operation, perhaps in another function, not at the line that made the mistake. It isn't the right moment. Since a `Record` knows its table, `__setitem__` could check the column name at once and raise there, at the cost of one set lookup per assignment.

### 9.4

Each view gets one `HashIndex` per index of its table, holding only overlay rows. Writes to the overlay go through a new `put`, which keeps those indexes current, so `UnitOfWork._record` changes too. `lookup` combines the base index (minus overlay rowids) with the overlay index, without scanning the overlay. (`match` with a dict could use them the same way.)

```python
# src/minidb/uow.py (replace TableView.__init__)
    def __init__(self, table: Table) -> None:
        self.base = table
        self.name, self.schema, self.columns = table.name, table.schema, table.columns
        self.overlay: dict[int, Row | None] = {}  # rowid -> row, None = deleted
        self.overlay_indexes = {name: HashIndex(name, i.columns) for name, i in table.indexes.items()}
```

```python
# src/minidb/uow.py (add to TableView)
    def put(self, rowid: int, row: Row | None) -> None:
        """Record this transaction's version of a row, keeping the overlay indexes current.

        :param rowid: the row's rowid.
        :param row: its new values, or ``None`` if this transaction deleted it.
        """
        old = self.overlay.get(rowid)
        for index in self.overlay_indexes.values():
            if old is not None:
                index.remove(rowid, old)
            if row is not None:
                index.add(rowid, row)
        self.overlay[rowid] = row
```

```python
# src/minidb/uow.py (replace TableView.lookup)
    def lookup(self, key: Mapping[str, Value | None]) -> set[int]:
        """Return the rowids whose columns equal ``key``, in O(1) per match.

        >>> from minidb import Column, Database, Integer
        >>> db = Database()
        >>> _ = db.create_table("t", [Column("id", Integer())], primary_key="id")
        >>> uow = db.unit_of_work()
        >>> rowid = uow.insert("t", {"id": 1})
        >>> uow.table("t").lookup({"id": 1}) == {rowid}
        True

        :param key: ``{column: value}``.
        :return: the matching rowids.
        :raises SchemaError: if no index covers exactly these columns.
        """
        found = {rid for rid in self.base.lookup(key) if rid not in self.overlay}
        index = self.base.index_on(key)
        assert index is not None  # the base lookup would have raised
        mine = self.overlay_indexes[index.name]
        return found | mine.lookup(tuple(key[c] for c in mine.columns))
```

```python
# src/minidb/uow.py (replace UnitOfWork._record)
    def _record(self, changes: list[Change]) -> None:
        """Put planned changes into the overlays, and keep loaded records current."""
        for c in changes:
            self.table(c.table).put(c.rowid, c.after)
            self._changes.append(c)
            key = (c.table, c.rowid)
            if key in self._identity:
                self._refresh(key, c.after)
```

```python
# src/minidb/uow.py (imports)
from minidb.index import HashIndex
```

The overlay indexes are built when the view is created, so an index created during the transaction is missing from them. Since `create_index` isn't transactional in minidb, that is one more reason not to change the schema inside a transaction.

### 9.5

Nothing is lost. `update` calls `flush()` *first*, which turns the pending change to `a` into a planned update. The update of `b` is then planned from that state, and `_refresh` writes its result (which includes the new `a`) back into the record and its snapshot. The second change to `a` is a new difference from the new snapshot, and the commit's flush saves it.

```python
>>> from minidb import Column, Database, Integer
>>> db = Database()
>>> _ = db.create_table("t", [Column("id", Integer()), Column("a", Integer()), Column("b", Integer())], primary_key="id")
>>> rowid = db.insert("t", {"id": 1, "a": 0, "b": 0})
>>> with db.unit_of_work() as uow:
...     record = uow.get("t", rowid)
...     record["a"] = 1
...     _ = uow.update("t", {"b": 2}, where={"id": 1})
...     seen = (record["a"], record["b"])
...     record["a"] = 5
>>> seen
(1, 2)
>>> db.get("t", rowid)
{'id': 1, 'a': 5, 'b': 2}
```

Without the flush at the start of `update`, `_refresh` would overwrite the record with a row planned from the *old* `a`, and the assignment `a = 1` would be silently lost: a lost update inside a single transaction.

### 9.6

A constraint is checked while planning if the transaction isn't deferred, *or* the constraint isn't deferrable. At commit, `check_deferred` checks everything over the final state, as before.

```python
# src/minidb/schema.py (add to ForeignKey)
    deferrable: bool = False
```

```python
# src/minidb/schema.py (add to TableSchema)
    unique_deferrable: bool = False
```

```python
# src/minidb/database.py (replace Database.create_table)
    def create_table(
        self,
        name: str,
        columns: Sequence[Column],
        *,
        primary_key: str | Sequence[str] = (),
        unique: Sequence[str | Sequence[str]] = (),
        checks: Sequence[Check] = (),
        foreign_keys: Sequence[ForeignKey] = (),
        unique_deferrable: bool = False,
    ) -> Table:
        """Create an empty table and return it; all or nothing.

        :param name: the new table's name.
        :param columns: its columns, in order.
        :param primary_key: the primary-key column or columns; none by default.
        :param unique: the columns of each UNIQUE constraint; none by default.
        :param checks: its row-level CHECK constraints; none by default.
        :param foreign_keys: its references to other tables; none by default.
        :param unique_deferrable: whether its primary key and unique
            constraints may be deferred to commit; ``False`` by default.
        :return: the new table.
        :raises SchemaError: if the table already exists, or the definition
            is invalid.
        """
        if name in self.tables:
            raise SchemaError(f"table {name!r} already exists")
        keys = tuple(as_key(u) for u in unique)
        schema = TableSchema(name, tuple(columns), tuple(checks), as_key(primary_key), keys, unique_deferrable)
        table = self.tables[name] = Table(schema)
        try:
            for fk in foreign_keys:
                self._add_foreign_key(replace(fk, table=name))
        except DatabaseError:
            self._forget_table(name)
            raise
        return table
```

```python
# src/minidb/changes.py (replace plan_insert)
def plan_insert(state: State, table: str, values: Mapping[str, object], *, check: bool = True) -> list[Change]:
    """Plan inserting one row.

    :param state: where to read the current data.
    :param table: the table's name.
    :param values: the new row's values, by column name.
    :param check: whether to check deferrable constraints now; ``True`` by
        default. Single-row and non-deferrable constraints are always checked.
    :return: the single insert change, with a newly allocated rowid.
    :raises ConstraintError: if the row breaks a constraint.
    """
    t = state.table(table)
    row = t.schema.prepare_row(values)
    if check or not t.schema.unique_deferrable:
        check_unique(t, [(None, row)])
    check_parents_exist(state, t, [row], _checked_now(references_from(state, table), check=check))
    return [Change(table, t.new_rowid(), None, row)]


def _checked_now(fks: Iterable[ForeignKey], *, check: bool) -> list[ForeignKey]:
    """Return the foreign keys to check now: all of them, or the non-deferrable ones."""
    return [fk for fk in fks if check or not fk.deferrable]
```

```python
# src/minidb/changes.py (replace plan_update)
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
    :param check: whether to check deferrable constraints now; ``True`` by
        default. Non-deferrable ones are always checked.
    :return: one update change per row.
    :raises ConstraintError: if a new row breaks a constraint.
    """
    t = state.table(table)
    targets = t.match(where) if rowids is None else rowids
    old = {rid: t.row(rid) for rid in targets}
    new = {rid: t.schema.prepare_row(changes, base=row) for rid, row in old.items()}
    if check or not t.schema.unique_deferrable:
        check_unique(t, list(new.items()))
    check_parents_exist(state, t, new.values(), _checked_now(references_from(state, table), check=check))
    check_no_orphans(state, t, old, new, _checked_now(references_to(state, table), check=check))
    return [Change(table, rid, old[rid], new[rid]) for rid in new]
```

```python
# src/minidb/changes.py (replace _restrict_or_null)
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
        if check or not fk.deferrable:
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
```

```python
# src/minidb/changes.py (replace check_no_orphans)
def check_no_orphans(
    state: State, parent: TableLike, old: dict[int, Row], new: dict[int, Row], fks: Sequence[ForeignKey] | None = None
) -> None:
    """Check, from the parent side of an update, that no referenced key changes.

    :param state: the database or view.
    :param parent: the table being updated.
    :param old: the rows before the update, by rowid.
    :param new: the rows after the update, by rowid.
    :param fks: the foreign keys to check; ``None`` (the default) for all
        that reference ``parent``.
    :raises ForeignKeyError: if a changed key is still referenced.
    """
    for fk in fks if fks is not None else references_to(state, parent.name):
        for rid, before in old.items():
            if fk.child_key(before) != fk.child_key(new[rid]) and children(state, fk, before):
                raise ForeignKeyError(
                    f"{fk.name}: cannot change {parent.name} key {fk.child_key(before)}, it is still referenced"
                )
```

In a deferred transaction, the non-deferrable foreign key still fails at once, while the deferrable primary key lets two rows swap ids:

```python
>>> from minidb import Column, Database, ForeignKey, Integer
>>> db = Database()
>>> _ = db.create_table("users", [Column("id", Integer())], primary_key="id", unique_deferrable=True)
>>> _ = db.create_table("orders", [Column("id", Integer()), Column("user_id", Integer())],
...     primary_key="id", foreign_keys=[ForeignKey(("user_id",), "users")])
>>> with db.unit_of_work(deferred=True) as uow:
...     _ = uow.insert("orders", {"id": 1, "user_id": 7})
Traceback (most recent call last):
  ...
minidb.errors.ForeignKeyError: fk_orders_user_id: no users row with {'id': 7}
>>> a, b = db.insert("users", {"id": 1}), db.insert("users", {"id": 2})
>>> with db.unit_of_work(deferred=True) as uow:
...     uow.get("users", a)["id"] = 2
...     uow.get("users", b)["id"] = 1
>>> db.select("users")
[{'id': 2}, {'id': 1}]
```

### 9.7

Give `Record` a `dirty` flag, set by `__setitem__` and `__delitem__`, and have `flush` diff only the dirty records against their snapshots, then clear the flags. A flush then costs O(dirty records) instead of O(loaded records). What it can miss is any change that doesn't go through `__setitem__`. C methods of `dict` such as `update`, `setdefault`, `pop`, `clear` and `|=` don't call it, so each must be overridden too. And a *mutable value* changed in place, such as `record["tags"].append("x")`, never touches the record at all. Our `Value` types are all immutable, which is one more reason for [Exercise 3.4](#34)'s rule. Systems that allow mutable values either keep snapshots for them (SQLAlchemy's `MutableList`) or ask for an explicit "flag modified".

### 9.8

Among others, SQLAlchemy's Unit of Work has:

- **Dependency-ordered flushes.** It sorts the pending operations topologically by the relationships between mapped classes, so parents are inserted before children and children deleted before parents, without the application ordering its calls.
- **Relationship cascades and lazy loading.** Adding an object to the session adds the objects it references (`save-update` cascade), and related collections load on first access.
- **Expiration and refresh.** After a commit, loaded objects are expired, so the next access reloads them from the database.
- **Optimistic version counters.** `version_id_col` adds `WHERE version = ?` to updates, and raises `StaleDataError` when another transaction changed the row.

See the "Unit of Work" and "Session Basics" sections of the SQLAlchemy documentation ([SQLAlchemy](references.md#sqlalchemy)).

## Chapter 10 — Concurrency, Part I

### 10.1

On Python 3.14, `dis` shows the statement as:

```text
LOAD_FAST_BORROW   0 (self)
COPY               1
LOAD_ATTR          0 (_next_rowid)
LOAD_SMALL_INT     1
BINARY_OP         13 (+=)
SWAP               2
STORE_ATTR         0 (_next_rowid)
```

The read (`LOAD_ATTR`), the addition (`BINARY_OP`) and the write (`STORE_ATTR`) are separate instructions. Thread A loads 5 and is switched out, or, on the free-threaded build, simply runs at the same time as B. Thread B loads 5 too, adds 1 and stores 6. A resumes with its 5 on its own stack, adds 1 and stores 6. Two calls, one increment: both threads were handed rowid 5, and the next one is 6 instead of 7. The GIL doesn't prevent this, because it can be switched between any two instructions. It only makes the window narrower.

### 10.2

Per-method locks make each *call* atomic, but a transfer is several calls: read both balances, write one, write the other. Another thread can run between any two of them and see (or overwrite) the intermediate state, in which money has left one account and not reached the other, or compute its own transfer from balances that are about to change. What's missing is **isolation**: the transaction's reads and writes must appear to happen at one instant, so the lock must be held from the first read to the last write. **Atomicity** across tables needs that too: a constraint check in one table and the write it guards in another must see the same state.

### 10.3

```python
# src/minidb/database.py (replace Database docstring)
    """Hold tables and the foreign keys between them, and run CRUD on them.

    :param lock_timeout: how many seconds a unit of work waits for the
        database lock before giving up; ``None`` (the default) waits forever.
    """
```

```python
# src/minidb/database.py (replace Database.__init__)
    def __init__(self, *, lock_timeout: float | None = None) -> None:
        self.tables: dict[str, Table] = {}
        self.foreign_keys: list[ForeignKey] = []
        self.lock_timeout = lock_timeout
        self._lock = threading.Lock()
        self._local = threading.local()  # .uow: this thread's active unit of work
```

```python
# src/minidb/database.py (replace Database.begin)
    def begin(self, uow: UnitOfWork) -> None:
        """Wait for exclusive access on behalf of a new unit of work.

        Units of work call this themselves; applications don't need to.

        >>> import threading
        >>> db = Database(lock_timeout=0.05)
        >>> holder = db.unit_of_work()
        >>> failures = []
        >>> def other() -> None:
        ...     try:
        ...         db.unit_of_work()
        ...     except TransactionError as e:
        ...         failures.append(str(e))
        >>> t = threading.Thread(target=other)
        >>> t.start()
        >>> t.join()
        >>> failures
        ['could not get the database lock within 0.05 s']

        :param uow: the unit of work that is starting.
        :raises TransactionError: if the thread already has an active one, or
            the lock isn't free within ``lock_timeout`` seconds.
        """
        if self.active_unit_of_work() is not None:
            raise TransactionError("this thread already has an active unit of work")
        if not self._lock.acquire(timeout=-1 if self.lock_timeout is None else self.lock_timeout):
            raise TransactionError(f"could not get the database lock within {self.lock_timeout} s")
        self._local.uow = uow
```

It solves none of the three problems; it changes what they look like. Problem 3, the forgotten transaction, stops blocking others *forever*: they fail after the timeout instead of hanging, which at least shows up in logs and can be retried. Problem 2, the slow transaction, is only turned into errors: the others still can't run while it holds the lock, and now they fail instead of waiting. Problem 1, readers blocking readers, is unaffected. The lock is still exclusive, and a timeout just makes readers fail where they would have waited.

### 10.4

Nothing releases it. The Unit of Work took the lock in its constructor, and only `commit` or `rollback` releases it; without a `with` block, an exception skips both. When the thread dies, the lock stays held, and every other thread waits forever (problem 3 of §10.6). Even when the `UnitOfWork` object is garbage collected, nothing happens, because nothing ties the lock to its lifetime.

Ways to notice:

- **A finalizer.** `weakref.finalize(uow, db.end_abandoned, ...)` runs when the object is collected and could release the lock and log a warning. Its caveats: collection may happen much later, or never (the object may be kept alive by the traceback of the exception that killed the thread, `sys.last_exc`, or a reference cycle), and it runs in whichever thread triggered collection.
- **Thread liveness.** Record the owning thread with the lock, and have waiters that time out (see [10.3](#103)) check `owner.is_alive()`. A dead owner means an abandoned transaction, which can be rolled back. That is safe in version 2, since nothing it did reached the tables.
- **An age limit.** Like PostgreSQL's `idle_in_transaction_session_timeout`, a watchdog can roll back transactions that have been open longer than some limit.

### 10.5

The thread holds the lock (exclusively, in this chapter), so `reading()` would wait for a lock that the same thread holds and deadlock with itself. Even if the lock allowed it, the read would show the *committed* state, without the transaction's own pending changes. A transaction that inserted a row and then read the table through the database wouldn't see its own insert: a very confusing bug. Refusing makes the mistake loud.

### 10.6

A **cursor** lets the client fetch the result in batches (`fetchmany`), so the server streams rows instead of materializing them, with memory proportional to one batch. To avoid holding locks between fetches, **MVCC** databases (PostgreSQL, Oracle, InnoDB) give the query a *snapshot*: it reads the row versions that were committed when it started, while writers create new versions next to them. Readers take no locks that block writers, and the old versions stay until the last snapshot that can see them ends. Systems without MVCC either hold shared locks for the life of the cursor (which blocks writers, as SQLite's rollback-journal mode does) or give up consistency with weaker isolation levels.

### 10.7

```python
# examples/aggregate_threads.py
"""Run four aggregate queries in parallel threads, with and without the database lock."""

import sys
import threading
import time
from typing import TYPE_CHECKING

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb.operators import Aggregate
from minidb.operators import Count
from minidb.operators import Scan
from minidb.operators import Sum

if TYPE_CHECKING:
    from collections.abc import Callable

ROWS, THREADS = 100_000, 4


def build() -> Database:
    """Create a table of ``ROWS`` rows.

    :return: the database.
    """
    db = Database()
    db.create_table("t", [Column("x", Integer())])
    for i in range(ROWS):
        db.insert("t", {"x": i})
    return db


def timed(work: Callable[[], object]) -> float:
    """Run ``work`` in ``THREADS`` threads at once.

    :param work: what each thread does.
    :return: the wall-clock time until all threads finish, in seconds.
    """
    threads = [threading.Thread(target=work) for _ in range(THREADS)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return time.perf_counter() - t0


def main() -> None:
    """Print the time with the lock held by each query, and with no lock."""
    db = build()
    locked = timed(lambda: db.query("t").group_by(n=Count(), s=Sum("x")).all())
    unlocked = timed(lambda: list(Aggregate(Scan(db.table("t")), [], {"n": Count(), "s": Sum("x")})))
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"GIL={gil}  through db.query: {locked:.2f}s   no lock: {unlocked:.2f}s")


if __name__ == "__main__":
    main()
```

On the book's machine:

```text
$ python3.14 -m examples.aggregate_threads
GIL=True  through db.query: 0.76s   no lock: 0.76s
$ python3.14t -m examples.aggregate_threads
GIL=False  through db.query: 0.84s   no lock: 0.46s
```

With the GIL, both take about the same time: only one thread runs Python code at a time anyway. On the free-threaded build, the queries without the lock run in parallel and finish in about half the time, close to the best possible on the book's two-core machine, while `db.query` takes the exclusive lock and runs them one after the other. The lock wastes every core but one, which is problem 1 of §10.6.

## Chapter 11 — Readers–Writer Locks

### 11.1

`_serving` names the ticket that may enter next. A reader that advanced it *before* its own `wait_for` would hand the turn to the next ticket while it hasn't been admitted itself. Its own predicate `self._serving == ticket` would then be false forever: the reader waits for a turn that has already passed, and so does everyone queued behind it. If instead it advanced `_serving` and then waited only for `not self._writer`, the ticket behind it (say a writer) would be allowed in while the reader was still waiting for an *earlier* writer to leave, and the two would race for entry. Order would be lost, and with it the no-starvation guarantee. Advancing after the wait means: "I am inside; the next one may now try."

### 11.2

All four methods change `_readers`, `_writer` and `_serving` only while holding `_cond`'s lock, and `wait_for` re-checks its predicate under that lock, so the check and the change that follows it happen atomically. The invariant is **`_writer` implies `_readers == 0`**, and it holds initially. A writer sets `_writer = True` only after its predicate `not self._writer and self._readers == 0`, so no reader is inside. A reader increments `_readers` only after `not self._writer`, so no writer is inside. Releases only make `_writer` false or `_readers` smaller, which can't break the invariant. So a reader and a writer are never inside at the same time, and neither are two writers, since a writer also requires `not self._writer`.

### 11.3

Each waiter gets its own `threading.Event` in a FIFO queue. The thread that releases the lock *hands it over*: it updates the counts on behalf of the threads at the head of the queue that can enter, and sets only their events. Nobody else wakes up, and nobody can overtake, because a new arrival that finds the queue non-empty must join it.

```python
# src/minidb/locks.py (append)
class QueuedRWLock(RWLockBase):
    """Admit requests in arrival order, waking only the threads that may enter.

    Every waiting thread has its own event in a FIFO queue. A release hands
    the lock to the head of the queue (all consecutive readers there, or
    one writer) and wakes just those threads.

    >>> lock = QueuedRWLock()
    >>> with lock.read(), lock.read():
    ...     pass
    >>> with lock.write():
    ...     pass
    """

    def __init__(self) -> None:
        self._mutex = threading.Lock()
        self._queue: deque[tuple[bool, threading.Event]] = deque()  # (is a writer, its event)
        self._readers = 0
        self._writer = False

    @override
    def acquire_read(self) -> None:
        with self._mutex:
            if not self._writer and not self._queue:
                self._readers += 1
                return
            event = self._enqueue(writer=False)
        event.wait()  # the releasing thread has counted us in

    @override
    def release_read(self) -> None:
        with self._mutex:
            self._readers -= 1
            self._admit()

    @override
    def acquire_write(self) -> None:
        with self._mutex:
            if not self._writer and self._readers == 0 and not self._queue:
                self._writer = True
                return
            event = self._enqueue(writer=True)
        event.wait()

    @override
    def release_write(self) -> None:
        with self._mutex:
            self._writer = False
            self._admit()

    def _enqueue(self, *, writer: bool) -> threading.Event:
        event = threading.Event()
        self._queue.append((writer, event))
        return event

    def _admit(self) -> None:
        """Hand the lock to the threads at the head of the queue that may have it."""
        while self._queue and not self._writer:
            writer, event = self._queue[0]
            if writer and self._readers:
                return  # the writer at the head waits for the readers inside
            self._queue.popleft()
            if writer:
                self._writer = True
            else:
                self._readers += 1
            event.set()
```

```python
# src/minidb/locks.py (imports)
from collections import deque
```

To measure it, 200 threads each take the write lock 20 times and hold it briefly, so up to 199 threads wait at every release:

```python
# examples/herd.py
"""Compare a broadcast-wakeup lock with a per-waiter queue under 200 contending threads."""

import threading
import time

from minidb.locks import FairRWLock
from minidb.locks import QueuedRWLock
from minidb.locks import RWLockBase

THREADS, ROUNDS = 200, 20


def contend(lock: RWLockBase) -> float:
    """Make ``THREADS`` threads take the write lock ``ROUNDS`` times each.

    :param lock: the lock to use.
    :return: the wall-clock time, in seconds.
    """
    start = threading.Barrier(THREADS)

    def work() -> None:
        start.wait()
        for _ in range(ROUNDS):
            with lock.write():
                time.sleep(0.0001)  # hold it long enough for the others to queue up

    threads = [threading.Thread(target=work) for _ in range(THREADS)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return time.perf_counter() - t0


def main() -> None:
    """Print the time each lock takes."""
    for lock in (FairRWLock(), QueuedRWLock()):
        print(f"{type(lock).__name__:>12}: {contend(lock):6.2f} s")


if __name__ == "__main__":
    main()
```

```text
  FairRWLock:  13.16 s
QueuedRWLock:   0.90 s
```

Each release of `FairRWLock` wakes every waiter, and all but one of them re-check their predicate and go back to sleep: O(waiters) wake-ups per release, so O(n²) in total for n threads. `QueuedRWLock` wakes exactly the thread that gets the lock, and is about 14 times faster here (12 times on the free-threaded build).

### 11.4

A thread that gives up must not leave its ticket in the queue, or `_serving` reaches it and waits for a thread that is no longer there. The lock remembers abandoned tickets and skips them whenever the head of the queue moves, including when the abandoned ticket is at the head already.

```python
# src/minidb/locks.py (replace FairRWLock)
class FairRWLock(RWLockBase):
    """Admit requests strictly in arrival (ticket) order, so nobody starves.

    Consecutive readers are admitted together; a writer waits for the
    readers ahead of it to leave, and nobody behind it can overtake it. A
    writer may give up after a timeout; its ticket is then skipped.

    >>> lock = FairRWLock()
    >>> with lock.read():
    ...     lock.acquire_write(timeout=0.01)
    Traceback (most recent call last):
      ...
    TimeoutError: no exclusive access within 0.01 s
    >>> with lock.write():  # the abandoned ticket doesn't block the queue
    ...     pass
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._next_ticket = 0  # handed to the next arrival
        self._serving = 0  # ticket at the head of the queue
        self._readers = 0  # readers inside
        self._writer = False  # writer inside?
        self._abandoned: set[int] = set()  # tickets whose owners gave up

    def _take_ticket(self) -> int:
        ticket = self._next_ticket
        self._next_ticket += 1
        return ticket

    def _advance(self) -> None:
        self._serving += 1
        self._skip_abandoned()

    def _skip_abandoned(self) -> None:
        while self._serving in self._abandoned:
            self._abandoned.remove(self._serving)
            self._serving += 1

    @override
    def acquire_read(self) -> None:
        with self._cond:
            ticket = self._take_ticket()
            self._cond.wait_for(lambda: self._serving == ticket and not self._writer)
            self._readers += 1
            self._advance()
            self._cond.notify_all()  # the next ticket may be a reader too

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()  # a writer may be waiting at the head

    @override
    def acquire_write(self, timeout: float | None = None) -> None:
        """Wait until the lock can be held exclusively, and take it.

        :param timeout: how many seconds to wait at most; ``None`` (the
            default) waits forever.
        :raises TimeoutError: if the lock wasn't available in time; the
            thread's place in the queue is then given up.
        """
        with self._cond:
            ticket = self._take_ticket()
            admitted = self._cond.wait_for(
                lambda: self._serving == ticket and not self._writer and self._readers == 0, timeout
            )
            if not admitted:
                self._abandoned.add(ticket)
                self._skip_abandoned()  # in case it was at the head
                self._cond.notify_all()
                raise TimeoutError(f"no exclusive access within {timeout} s")
            self._writer = True
            self._advance()

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._cond.notify_all()
```

`acquire_read` can get a timeout the same way. The Unit of Work then turns `TimeoutError` into `TransactionError`, as in [Exercise 10.3](#103).

### 11.5

Thread R holds a read lock (ticket 0). Writer W arrives, takes ticket 1, and waits for `_readers == 0`. R now asks for another read lock: it takes ticket 2 and waits for `_serving == 2`. But `_serving` is 1, W's ticket, and W waits for R to leave. R waits for W, and W waits for R: a deadlock. (Without W, the second read would succeed, so the bug only shows under contention.) minidb avoids the situation by never taking the lock twice in one thread: `Database.begin` refuses a second Unit of Work in a thread that already has one, `reading()` refuses inside a Unit of Work, and code inside the database never acquires the lock itself.

### 11.6

With R W R W R W …, `FairRWLock` admits readers together only when they are *consecutive* in the queue, so here every reader is alone: one reader, then one writer, then one reader. Readers get no parallelism at all, even though a hundred of them may be waiting.

A **phase-fair** lock alternates phases: when a writer leaves, *all* waiting readers enter together, however many writers are queued between them. Then the next writer goes, and so on. A writer waits for at most one read phase plus the writers ahead of it, and a reader for at most one write phase. Here the releasing writer counts the waiting readers in itself, so the next writer can't slip in before them:

```python
# src/minidb/locks.py (append)
class PhaseFairRWLock(RWLockBase):
    """Alternate between phases: one writer, then every reader that was waiting.

    Writers enter in arrival order. Readers that arrive while a writer is
    waiting or inside enter together as soon as that writer leaves, ahead
    of the next writer. A writer waits for at most one read phase plus the
    writers ahead of it, and a reader for at most one writer.

    >>> lock = PhaseFairRWLock()
    >>> with lock.read(), lock.read():
    ...     pass
    >>> with lock.write():
    ...     pass
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._readers = 0
        self._writer = False
        self._readers_waiting = 0
        self._writers_waiting = 0
        self._next_ticket = 0  # writers' queue
        self._serving = 0
        self._phase = 0  # incremented whenever a writer leaves

    @override
    def acquire_read(self) -> None:
        with self._cond:
            if not self._writer and self._writers_waiting == 0:
                self._readers += 1
                return
            self._readers_waiting += 1
            phase = self._phase
            self._cond.wait_for(lambda: self._phase != phase)  # the writer counted us in

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    @override
    def acquire_write(self) -> None:
        with self._cond:
            ticket = self._next_ticket
            self._next_ticket += 1
            self._writers_waiting += 1
            self._cond.wait_for(lambda: self._serving == ticket and not self._writer and self._readers == 0)
            self._writers_waiting -= 1
            self._writer = True

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._serving += 1
            self._readers += self._readers_waiting  # start a read phase for everyone waiting
            self._readers_waiting = 0
            self._phase += 1
            self._cond.notify_all()
```

[Brandenburg and Anderson 2009](references.md#brandenburg2009) introduce phase-fair locks and analyze their bounds.

### 11.7

No. `notify_all` wakes *every* waiter, and each one re-checks its predicate under the lock before it can proceed. Admission depends only on the ticket (`_serving == ticket`), not on which thread happens to wake or run first. If a thread that isn't at the head wakes first, its predicate is false and it waits again; the thread at the head proceeds whenever it gets to re-check. The order of wake-ups affects performance, never who goes next. That is also why `wait_for` (with its loop) is essential: a woken thread must never assume that it was woken *for it*.

### 11.8

Courtois, Heymans and Parnas's first solution (readers have priority) uses a counter and two semaphores. `mutex` protects `readcount`; `w` is held by the writer, or on behalf of all readers by the first reader in, until the last reader out releases it. A semaphore, unlike a lock, may be released by a thread other than the one that acquired it, which this solution needs.

```python
# src/minidb/locks.py (append)
class CourtoisLock(RWLockBase):
    """Translate Courtois, Heymans and Parnas's first solution (1971) to semaphores.

    Readers have priority, exactly like :class:`ReaderPreferringLock`: the
    first reader in takes ``w`` for all readers, the last one out releases it.

    >>> lock = CourtoisLock()
    >>> with lock.read(), lock.read():
    ...     pass
    >>> with lock.write():
    ...     pass
    """

    def __init__(self) -> None:
        self._readcount = 0
        self._mutex = threading.Semaphore(1)  # protects readcount
        self._w = threading.Semaphore(1)  # held by the writer, or by the readers as a group

    @override
    def acquire_read(self) -> None:
        with self._mutex:  # P(mutex)
            self._readcount += 1
            if self._readcount == 1:
                self._w.acquire()  # P(w)
        # leaving the block releases the mutex: V(mutex)

    @override
    def release_read(self) -> None:
        with self._mutex:
            self._readcount -= 1
            if self._readcount == 0:
                self._w.release()  # V(w)

    @override
    def acquire_write(self) -> None:
        self._w.acquire()

    @override
    def release_write(self) -> None:
        self._w.release()
```

## Chapter 12 — Isolation

### 12.1

A row's version can only tell you that *that row* changed. A uniqueness check that finds nothing has read no rows, so there is no version to record. Transaction A checks that `email = 'ada@example.org'` is free and finds nothing. B inserts a row with that email and commits. A's read set of row versions is empty, so validation passes, A commits, and the table has two Adas. Recording the lookup's *result set* (∅) catches it: at commit the lookup returns {B's row} ≠ ∅. The row B inserted didn't exist when A looked. It is a phantom, and only a record of the *question* (the key looked up) can notice it.

### 12.2

No. Both serial orders give the same result: if the reader goes first, it reads the original values; if the writer goes first, it writes those same values, and the reader reads them again. Either way the reader sees what it saw, so the history is serializable, and the conflict is a *false positive*. To avoid it, record the row *values* read instead of their versions, and at validation compare the current row with the remembered one. Since rows are never mutated, the read set can just keep a reference to the row it read: `current is seen or current == seen`. That costs one reference per row read, plus an O(columns) comparison at commit whenever the row object has changed. The version check costs only an integer comparison, and false positives this way are rare in practice, which is why most systems accept them.

### 12.3

`conflicts` returns a list, and `_validate` reports everything:

```python
# src/minidb/uow.py (replace TableView.conflicts)
    def conflicts(self) -> list[str]:
        """Describe every recorded read that is no longer true.

        :return: one description per conflict; empty if every read still holds.
        """
        return [*self._scan_conflicts(), *self._row_conflicts(), *self._key_conflicts()]
```

```python
# src/minidb/uow.py (replace TableView._scan_conflict)
    def _scan_conflicts(self) -> list[str]:
        if self.scanned_version is not None and self.base.version != self.scanned_version:
            return [f"{self.name} changed since it was scanned"]
        return []
```

```python
# src/minidb/uow.py (replace TableView._row_conflict)
    def _row_conflicts(self) -> list[str]:
        return [
            f"{self.name} row {rowid} changed since it was read"
            for rowid, version in self.row_reads.items()
            if self.base.row_versions.get(rowid) != version
        ]
```

```python
# src/minidb/uow.py (replace TableView._key_conflict)
    def _key_conflicts(self) -> list[str]:
        problems: list[str] = []
        for (kind, key), seen in self.key_reads.items():
            now = self.base.lookup(dict(key)) if kind == "lookup" else set(self.base.match(dict(key)))
            if frozenset(now) != seen:
                problems.append(f"{self.name} rows matching {dict(key)} changed")
        return problems
```

```python
# src/minidb/uow.py (replace UnitOfWork._validate)
    def _validate(self) -> None:
        problems = [p for view in self._views.values() for p in view.conflicts()]
        if problems:
            raise ConflictError("; ".join(problems))
```

In this version of the write-skew example, Bob also looks at Alice's row before deciding, so his report has two entries:

```python
>>> import threading
>>> from minidb import Boolean, Column, ConflictError, Database, Text
>>> db = Database()
>>> _ = db.create_table("doctors", [Column("name", Text()), Column("on_call", Boolean())], primary_key="name")
>>> alice = db.insert("doctors", {"name": "Alice", "on_call": True})
>>> _ = db.insert("doctors", {"name": "Bob", "on_call": True})
>>> bob_has_read, alice_done, report = threading.Event(), threading.Event(), []
>>> def bob():
...     uow = db.unit_of_work()
...     on_call = uow.query("doctors").where(lambda r: r["on_call"]).all()
...     _ = uow.get("doctors", alice)
...     bob_has_read.set(); alice_done.wait()
...     if len(on_call) >= 2:
...         uow.update("doctors", {"on_call": False}, where={"name": "Bob"})
...     try:
...         uow.commit()
...     except ConflictError as e:
...         uow.rollback(); report.extend(str(e).split("; "))
>>> t = threading.Thread(target=bob); t.start()
>>> _ = bob_has_read.wait()
>>> with db.unit_of_work() as uow:
...     _ = uow.update("doctors", {"on_call": False}, where={"name": "Alice"})
>>> alice_done.set(); t.join()
>>> for line in report: print(line)
doctors changed since it was scanned
doctors row 1 changed since it was read
```

### 12.4

Forward validation checks the committing transaction's *write set* against the *read sets of the transactions still running*, and resolves a conflict by aborting either the committer or the readers (a choice backward validation doesn't have). minidb would need a registry of active transactions, each publishing its read set as it grows. Reads would then have to update shared state under a lock instead of a private dict. It would also need the write set in a form that can be tested against read sets: the changed rowids per table, plus the old and new key values, to test lookups. Read-only transactions then never need validating, and a committer never waits for anyone.

### 12.5

Each table keeps a **commit log**: a list of `(commit number, changed rowids)`, one entry per commit that touched it, plus the global commit counter. A predicate read records `(expression, commit number at read time, rowids it returned)`. At commit, the transaction takes the union of the rowids changed since that commit number, which is usually far fewer than the table, and re-evaluates the expression on each one's current row. The read is still valid if every changed row that matches now was in the result, and every changed row in the result still exists and matches. Entries older than the oldest active transaction's start can be dropped from the log. This is close to how PostgreSQL's serializable snapshot isolation tracks reads ([Ports and Grittner 2012](references.md#ports2012)), though it records predicate locks on index ranges and pages instead of expressions.

### 12.6

To break symmetry. Two transactions that conflict and then sleep for the same fixed time wake up together, read together, and conflict again, as often as there are retries: a *livelock*. Random delays make it likely that one of them retries first and commits before the other reads. Growing the delays exponentially adapts to how much contention there is: the more often a transaction has failed, the longer it waits, so heavy contention spreads out instead of piling up. Ethernet's collision back-off works the same way.

### 12.7

- Each table keeps, per rowid, a list of versions `(created, deleted, row)`: the commit numbers between which the version was the current one, with `deleted = ∞` while it is current.
- `put` at commit *c* sets `deleted = c` on the current version and appends `(c, ∞, new row)`; `remove` only sets `deleted = c`. Nothing is overwritten, so readers never see a change half made.
- A `TableView` of a snapshot taken at commit *s* sees, for each rowid, the version with `created ≤ s < deleted`. Reads need no latch, since versions are only ever appended to, and the snapshot never changes. Indexes must also return rowids whose *old* versions match, and filter by visibility.
- A version can be thrown away once its `deleted` is ≤ the snapshot of the **oldest running transaction**. Nobody can see it any more. That's what PostgreSQL's `VACUUM` does, and why one long-running transaction makes tables bloat.

### 12.8

`latch()` returns a no-op while the latch is already held for the current operation, and each write takes it once, around the flush and the planning:

```python
# src/minidb/uow.py (replace UnitOfWork.latch)
    def latch(self) -> AbstractContextManager[None]:
        """Return the short lock to hold around each read of committed data.

        It does nothing when the unit of work already holds the lock: being
        read-only or exclusive, in the middle of committing, or already
        inside a latched operation.

        :return: a context manager.
        """
        if self.readonly or self.exclusive or self._committing or self._latched:
            return nullcontext()
        return self._operation_latch()

    @contextmanager
    def _operation_latch(self) -> Iterator[None]:
        with self.db.shared_lock():
            self._latched = True
            try:
                yield
            finally:
                self._latched = False
```

```python
# src/minidb/uow.py (replace UnitOfWork.insert)
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
        with self.latch():  # once for every lookup the operation makes
            self.flush()
            changes = ch.plan_insert(self, table, values, check=not self.deferred)
        self._record(changes)
        return changes[0].rowid
```

```python
# src/minidb/uow.py (replace UnitOfWork.update)
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
        with self.latch():
            self.flush()
            planned = ch.plan_update(self, table, changes, where, check=not self.deferred)
        self._record(planned)
        return len(planned)
```

```python
# src/minidb/uow.py (replace UnitOfWork.delete)
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
        with self.latch():
            self.flush()
            planned = ch.plan_delete(self, table, where, check=not self.deferred)
        self._record(planned)
        return sum(1 for c in planned if c.table == table and c.kind == "delete")
```

```python
# src/minidb/uow.py (add to UnitOfWork)
    _latched: bool = False  # inside a latched operation?
```

```python
# src/minidb/uow.py (imports)
from contextlib import contextmanager
```

The measurement, with a primary key and a unique column so that each insert makes two lookups:

```python
# examples/fair_price.py
"""Insert 2,000 rows in one thread while another counts the table, as in §12.6."""

import threading
import time

from minidb import Column
from minidb import Count
from minidb import Database
from minidb import Integer
from minidb import Text

ROWS = 2_000


def main() -> None:
    """Print the writer's time and how many counts the reader ran meanwhile."""
    db = Database()
    db.create_table("t", [Column("id", Integer()), Column("email", Text())], primary_key="id", unique=["email"])
    done = threading.Event()
    reads = 0

    def reader() -> None:
        nonlocal reads
        while not done.is_set():
            db.query("t").group_by(n=Count()).all()
            reads += 1

    thread = threading.Thread(target=reader)
    thread.start()
    t0 = time.perf_counter()
    for i in range(ROWS):
        db.insert("t", {"id": i, "email": f"user{i}@example.org"})
    elapsed = time.perf_counter() - t0
    done.set()
    thread.join()
    print(f"{ROWS} inserts: {elapsed:.2f} s, reader queries meanwhile: {reads}")


if __name__ == "__main__":
    main()
```

```text
                 before (one latch per lookup)           after (one latch per operation)
python3.14       2000 inserts: 8.58 s, 5902 queries      2000 inserts: 6.00 s, 4739 queries
python3.14t      2000 inserts: 3.24 s, 2039 queries      2000 inserts: 3.10 s, 2009 queries
```

With the GIL, the writer is about 30% faster. On the free-threaded build, nothing changes, and that is instructive. The shared latches are compatible with the reader's shared lock, so they only wait when an exclusive request is queued ahead of them, which is rare here. What dominates is the commit: its exclusive request waits for the reader's current scan to finish, and the next scan waits for the commit. One scan per insert remains, however few latches the insert takes. To speed up the writer you must shorten what the *reader* holds, which is MVCC's job ([12.7](#127)).

### 12.9

Yes, once there are many writers. A commit holds the exclusive lock for O(|read set| + |write set|): one version comparison per row read, one index lookup per key read (plus the matches it returns), one comparison per scanned table, then one `put` or `remove` per net change, each updating every index of its table. Nobody else can read committed data meanwhile, so a transaction with a large read set (a report that read a million rows, then wrote one) stops everyone for as long as its validation takes. Real optimistic systems shrink the critical section: validate *before* taking the lock against a commit log and only re-check the commits since, partition the lock per table, or, like PostgreSQL's SSI, track conflicts as they happen instead of validating at the end.

## Chapter 13 — Persistence

### 13.1

```python
# src/minidb/storage.py (append)
class PickleFormat:
    """Store primitives with :mod:`pickle`: fast, but only for files you wrote yourself.

    Unpickling runs code chosen by whoever wrote the file, so never load a
    pickle that could have come from somewhere else.

    >>> PickleFormat().loads(PickleFormat().dumps({"a": [1, None, "x"]}))
    {'a': [1, None, 'x']}
    """

    name = "pickle"
    suffix = ".pickle"

    def dumps(self, obj: object) -> bytes:
        """Encode ``obj`` with the newest pickle protocol.

        :param obj: a structure of primitives.
        :return: the encoded bytes.
        """
        return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    def loads(self, data: bytes) -> object:
        """Decode a pickle; trusted data only.

        :param data: what :meth:`dumps` produced.
        :return: the decoded structure.
        """
        result: object = pickle.loads(data)  # noqa: S301 - only files this program wrote
        return result


class CompactFormat:
    """Store primitives in a tagged binary encoding: one type byte, then the value.

    Integers take 8 bytes (larger ones are stored as decimal text), floats 8,
    strings, lists and dicts a 4-byte length followed by their contents.
    Tuples are stored as lists, as in JSON.

    >>> f = CompactFormat()
    >>> f.loads(f.dumps({"a": [1, None, "x", 2.5, True, 2**70]}))
    {'a': [1, None, 'x', 2.5, True, 1180591620717411303424]}
    """

    name = "compact"
    suffix = ".bin"

    def dumps(self, obj: object) -> bytes:
        """Encode ``obj``.

        :param obj: a structure of primitives.
        :return: the encoded bytes.
        :raises TypeError: if ``obj`` contains something that isn't a primitive.
        """
        out = bytearray()
        _encode(obj, out)
        return bytes(out)

    def loads(self, data: bytes) -> object:
        """Decode what :meth:`dumps` produced.

        :param data: the encoded bytes.
        :return: the decoded structure.
        :raises ValueError: if ``data`` is not a valid encoding.
        """
        value, pos = _decode(data, 0)
        if pos != len(data):
            raise ValueError(f"{len(data) - pos} trailing bytes")
        return value


_LENGTH = struct.Struct(">I")
_INT = struct.Struct(">q")
_FLOAT = struct.Struct(">d")
_SCALARS: dict[object, bytes] = {None: b"N", True: b"T", False: b"F"}


def _encode(obj: object, out: bytearray) -> None:
    """Append the encoding of ``obj`` to ``out``."""
    encoder = _ENCODERS.get(type(obj))
    if encoder is None:
        raise TypeError(f"cannot encode {type(obj).__name__}")
    encoder(obj, out)


def _encode_scalar(obj: object, out: bytearray) -> None:
    out += _SCALARS[obj]


def _encode_int(obj: object, out: bytearray) -> None:
    n = cast("int", obj)
    if -(2**63) <= n < 2**63:
        out += b"i" + _INT.pack(n)
    else:
        _encode_bytes(b"I", str(n).encode(), out)


def _encode_float(obj: object, out: bytearray) -> None:
    out += b"f" + _FLOAT.pack(cast("float", obj))


def _encode_str(obj: object, out: bytearray) -> None:
    _encode_bytes(b"s", cast("str", obj).encode(), out)


def _encode_bytes(tag: bytes, data: bytes, out: bytearray) -> None:
    out += tag + _LENGTH.pack(len(data)) + data


def _encode_list(obj: object, out: bytearray) -> None:
    items = cast("list[object]", obj)
    out += b"l" + _LENGTH.pack(len(items))
    for item in items:
        _encode(item, out)


def _encode_dict(obj: object, out: bytearray) -> None:
    items = cast("dict[str, object]", obj)
    out += b"d" + _LENGTH.pack(len(items))
    for key, value in items.items():
        _encode_str(key, out)
        _encode(value, out)


_ENCODERS: dict[type, Callable[[object, bytearray], None]] = {
    type(None): _encode_scalar,
    bool: _encode_scalar,
    int: _encode_int,
    float: _encode_float,
    str: _encode_str,
    list: _encode_list,
    tuple: _encode_list,
    dict: _encode_dict,
}


def _decode(data: bytes, pos: int) -> tuple[object, int]:
    """Decode the value at ``pos``; return it and the position after it."""
    decoder = _DECODERS.get(data[pos : pos + 1])
    if decoder is None:
        raise ValueError(f"bad type tag at byte {pos}")
    return decoder(data, pos + 1)


def _decode_bytes(data: bytes, pos: int) -> tuple[bytes, int]:
    (length,) = _LENGTH.unpack_from(data, pos)
    start = pos + _LENGTH.size
    if start + length > len(data):
        raise ValueError(f"truncated value at byte {pos}")
    return data[start : start + length], start + length


def _decode_str(data: bytes, pos: int) -> tuple[object, int]:
    raw, pos = _decode_bytes(data, pos)
    return raw.decode(), pos


def _decode_big_int(data: bytes, pos: int) -> tuple[object, int]:
    raw, pos = _decode_bytes(data, pos)
    return int(raw.decode()), pos


def _decode_list(data: bytes, pos: int) -> tuple[object, int]:
    (count,) = _LENGTH.unpack_from(data, pos)
    pos += _LENGTH.size
    items: list[object] = []
    for _ in range(count):
        item, pos = _decode(data, pos)
        items.append(item)
    return items, pos


def _decode_dict(data: bytes, pos: int) -> tuple[object, int]:
    (count,) = _LENGTH.unpack_from(data, pos)
    pos += _LENGTH.size
    items: dict[str, object] = {}
    for _ in range(count):
        key, pos = _decode(data, pos)
        items[cast("str", key)], pos = _decode(data, pos)
    return items, pos


_DECODERS: dict[bytes, Callable[[bytes, int], tuple[object, int]]] = {
    b"N": lambda _, pos: (None, pos),
    b"T": lambda _, pos: (True, pos),
    b"F": lambda _, pos: (False, pos),
    b"i": lambda data, pos: (_INT.unpack_from(data, pos)[0], pos + _INT.size),
    b"f": lambda data, pos: (_FLOAT.unpack_from(data, pos)[0], pos + _FLOAT.size),
    b"s": _decode_str,
    b"I": _decode_big_int,
    b"l": _decode_list,
    b"d": _decode_dict,
}
```

```python
# src/minidb/storage.py (imports)
import pickle
```

```python
# src/minidb/storage.py (typing imports)
from collections.abc import Callable
```

The comparison writes a 100,000-row snapshot in each format, and times encoding, decoding and a complete `attach` (decoding plus validating every value):

```python
# examples/formats.py
"""Compare snapshot size and speed for the JSON, pickle and compact formats."""

import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Real
from minidb import Storage
from minidb import Text
from minidb.storage import CompactFormat
from minidb.storage import JsonFormat
from minidb.storage import PickleFormat

if TYPE_CHECKING:
    from minidb.storage import Format

ROWS = 100_000


def declare() -> Database:
    """Return a database with the test table and no rows.

    :return: the database.
    """
    db = Database()
    db.create_table(
        "people",
        [Column("id", Integer()), Column("name", Text()), Column("score", Real())],
        primary_key="id",
    )
    return db


def measure(fmt: Format, folder: Path) -> str:
    """Write a snapshot of ``ROWS`` rows in ``fmt``, and time reading it back.

    :param fmt: the format.
    :param folder: an empty directory.
    :return: one line of the report.
    """
    db = declare()
    db.attach(Storage(folder, fmt, sync=False))
    for i in range(ROWS):
        db.insert("people", {"id": i, "name": f"person {i}", "score": i / 7})
    t0 = time.perf_counter()
    db.checkpoint()
    write = time.perf_counter() - t0
    db.close()
    data = (folder / f"snapshot{fmt.suffix}").read_bytes()
    t0 = time.perf_counter()
    fmt.loads(data)
    decode = time.perf_counter() - t0
    t0 = time.perf_counter()
    declare().attach(Storage(folder, fmt, sync=False))
    attach = time.perf_counter() - t0
    return f"{fmt.name:>8}{len(data) / 1e6:>8.1f} MB{write:>9.2f} s{decode:>9.2f} s{attach:>9.2f} s"


def main() -> None:
    """Print size, checkpoint time, decode time and attach time for each format."""
    print(f"{'format':>8}{'size':>11}{'write':>11}{'decode':>11}{'attach':>11}")
    for fmt in (JsonFormat(), PickleFormat(), CompactFormat()):
        with tempfile.TemporaryDirectory() as folder:
            print(measure(fmt, Path(folder)))


if __name__ == "__main__":
    main()
```

```text
  format       size      write     decode     attach
    json     4.7 MB     0.26 s     0.08 s     0.64 s
  pickle     3.7 MB     0.28 s     0.05 s     0.59 s
 compact     5.4 MB     0.36 s     0.28 s     0.83 s
```

The hand-written format loses on every count. Its fixed 8-byte integers and 4-byte lengths are bigger than JSON's short decimal digits, and its decoder is a Python loop, while `json` and `pickle` decode in C. Pickle is the smallest and fastest, by a little. All three are dwarfed by `attach`, which spends most of its time validating every value with `from_primitive` and rebuilding the indexes. The format matters less than the work done after decoding. A compact format would only win if written in C, or with variable-length integers, as SQLite's record format does.

### 13.2

Because the log is what survives a crash, and memory is what other transactions see. With memory first, there is a moment when the commit is visible but not durable. If the process crashes in that moment, the commit is gone after recovery although others may already have acted on it. If the `append` fails (disk full, I/O error), the transaction raises and the application believes it failed and may retry, while memory already holds its changes: the retry applies them twice, and a restart then silently drops the first copy. And as soon as other transactions may read before the commit returns (as with group commit in [13.4](#134)), a second transaction can read the change, commit its own record durably and acknowledge its client, after which a crash loses the first record but not the second: the database recovers a state in which T2 acted on data that never existed. Logging first means that whatever anyone has seen is already on disk.

### 13.3

With an `fsync` after every record, no: record *n+1* is only written after record *n* is known to be on disk, so a crash can only damage the last one. Without that ordering (with `sync=False`, with group commit's batches, or on a drive that reorders writes in its cache), the file system may persist a later page and not an earlier one, leaving a torn record followed by intact ones. A *torn write* is a write that reached the disk only partly, in some sectors and not others. A *write barrier* (a cache flush, or FUA) is how a program forces earlier writes to be durable before later ones. Keep scanning when salvaging a damaged database by hand, or to *detect* the situation and refuse to start (keeping a damaged log silently would be worse). For normal recovery, stopping is right: a commit after a lost one may depend on it, so replaying it would recover a state that never existed.

### 13.4

The log gets a ticket counter. `append` writes a record and returns its ticket; with `group_commit=True`, it doesn't sync. A background thread syncs whatever has been written since its last sync, and records the highest ticket that is now durable. A commit applies its changes under the exclusive lock, releases the lock, and *then* waits for its ticket. While one sync is running, other transactions commit and append, and the next sync covers all of them. (The method is called `sync_log`, because `sync` is already the constructor's flag.)

```python
# src/minidb/storage.py (replace Storage docstring)
    """Keep a database in a directory: ``snapshot<suffix>`` plus ``wal.log``.

    :param directory: where the files live; created if missing.
    :param fmt: the format of the snapshot and log payloads;
        ``None`` (the default) means :class:`JsonFormat`.
    :param sync: whether to ``fsync`` before reporting a write as done;
        ``True`` by default. ``False`` is faster but not crash-safe.
    :param group_commit: whether a background thread syncs the log for
        several commits at once; ``False`` by default. Committers then
        wait in :meth:`wait_durable`.
    """
```

```python
# src/minidb/storage.py (replace Storage.__init__)
    def __init__(
        self,
        directory: str | os.PathLike[str],
        fmt: Format | None = None,
        *,
        sync: bool = True,
        group_commit: bool = False,
    ) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.format: Format = fmt if fmt is not None else JsonFormat()
        self.sync = sync
        self.group_commit = group_commit
        self.snapshot_path = self.dir / f"snapshot{self.format.suffix}"
        self.log_path = self.dir / "wal.log"
        self._latch = threading.Lock()  # serializes file operations
        self._durable = threading.Condition(self._latch)  # signalled when tickets advance
        self._appended = 0  # tickets handed out: records written to the file
        self._synced = 0  # tickets known to be on disk
        self._closing = False
        self._log: BufferedWriter | None = None
        self._flusher: threading.Thread | None = None
        if group_commit:
            self._flusher = threading.Thread(target=self._flush_loop, daemon=True)
            self._flusher.start()
```

```python
# src/minidb/storage.py (replace Storage.append)
    def append(self, record: LogRecord) -> int:
        """Append one framed record to the log.

        Without group commit, the record is durable when this returns. With
        it, the record has only been written, and :meth:`wait_durable` waits
        for the flusher to sync it.

        :param record: the commit to log.
        :return: the record's ticket, for :meth:`wait_durable`.
        """
        payload = self.format.dumps(record)
        frame = _FRAME.pack(len(payload), zlib.crc32(payload)) + payload
        with self._durable:
            if self._log is None:
                self._log = self.log_path.open("ab")
            self._log.write(frame)
            self._appended += 1
            if self.group_commit:
                self._durable.notify_all()  # wake the flusher
            else:
                self._fsync(self._log)
                self._synced = self._appended
            return self._appended

    def sync_log(self) -> int:
        """Make every record appended so far durable; appends may go on meanwhile.

        :return: the ticket of the last record that is now on disk.
        """
        with self._latch:
            target = self._appended
            if self._log is None:
                return target
            self._log.flush()
            fd = self._log.fileno()
        if self.sync:
            os.fsync(fd)  # without the latch: other commits keep appending
        return target

    def wait_durable(self, ticket: int) -> None:
        """Wait until the record with ``ticket`` is on disk.

        :param ticket: a value returned by :meth:`append`.
        """
        with self._durable:
            self._durable.wait_for(lambda: self._synced >= ticket)

    def _flush_loop(self) -> None:
        while True:
            with self._durable:
                self._durable.wait_for(lambda: self._appended > self._synced or self._closing)
                if self._appended == self._synced:
                    return  # closing, and everything is on disk
            target = self.sync_log()
            with self._durable:
                self._synced = target
                self._durable.notify_all()
```

```python
# src/minidb/storage.py (replace Storage.truncate_log)
    def truncate_log(self) -> None:
        """Empty the log, after a snapshot has made its records redundant."""
        with self._durable:
            self._durable.wait_for(lambda: self._synced == self._appended)  # no sync in flight
            if self._log is not None:
                self._log.close()
                self._log = None
            with self.log_path.open("wb") as f:
                self._fsync(f)
```

```python
# src/minidb/storage.py (replace Storage.close)
    def close(self) -> None:
        """Stop the flusher after its last sync, and close the log file."""
        with self._durable:
            self._closing = True
            self._durable.notify_all()
        if self._flusher is not None:
            self._flusher.join()
        with self._latch:
            if self._log is not None:
                self._log.close()
                self._log = None
```

```python
# src/minidb/database.py (replace Database.apply)
    def apply(self, changes: Sequence[Change]) -> None:
        """Write validated changes as one commit: log first, then memory.

        The caller holds the exclusive lock. With group commit, the record
        may not be on disk yet: the caller must :meth:`wait_durable` after
        releasing the lock, before reporting success.

        :param changes: the changes to write.
        """
        seq = self.commit_seq + 1
        if self.storage is not None:  # the write-ahead rule
            self._local.ticket = self.storage.append({"seq": seq, "changes": [self._encode(c) for c in changes]})
        self.commit_seq = seq
        for c in changes:
            self._apply_one(c.table, c.rowid, c.after, seq)

    def wait_durable(self) -> None:
        """Wait until the calling thread's last commit is on disk."""
        ticket: int = getattr(self._local, "ticket", 0)
        if self.storage is not None and ticket:
            self.storage.wait_durable(ticket)
```

```python
# src/minidb/uow.py (replace UnitOfWork.commit)
    def commit(self) -> None:
        """Flush, then validate and apply, in the way this unit of work's mode requires.

        Returns only once the commit is durable, but without holding any
        lock while it waits, so that commits can share one sync.

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
        self.db.wait_durable()
```

Other transactions can now read a commit before it is durable, which is the situation [13.2](#132) warns about. It is safe here because the log is written in commit order: a transaction that read T1's data commits *after* T1, so its record follows T1's, and a crash that loses T1 loses it too. But a read-only transaction may *report* data that a crash then loses. Systems that care make readers wait as well, or only expose durable commits.

```python
# examples/group_commit.py
"""Measure commits per second with and without group commit, for 1, 4 and 16 threads."""

import tempfile
import threading
import time
from itertools import count

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Storage

COMMITS = 800  # in total, shared between the threads


def run(threads: int, *, group_commit: bool) -> float:
    """Make ``COMMITS`` single-row commits from ``threads`` threads.

    :param threads: how many threads commit at once.
    :param group_commit: whether the storage uses group commit.
    :return: commits per second.
    """
    with tempfile.TemporaryDirectory() as folder:
        db = Database()
        db.create_table("t", [Column("id", Integer())], primary_key="id")
        db.attach(Storage(folder, group_commit=group_commit))
        ids = count()

        def work() -> None:
            for _ in range(COMMITS // threads):
                db.insert("t", {"id": next(ids)})

        workers = [threading.Thread(target=work) for _ in range(threads)]
        t0 = time.perf_counter()
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        elapsed = time.perf_counter() - t0
        db.close()
    return COMMITS / elapsed


def main() -> None:
    """Print a table of commits per second."""
    print(f"{'threads':>8}{'fsync per commit':>18}{'group commit':>14}")
    for threads in (1, 4, 16):
        print(f"{threads:>8}{run(threads, group_commit=False):>18.0f}{run(threads, group_commit=True):>14.0f}")


if __name__ == "__main__":
    main()
```

```text
threads  fsync per commit  group commit
      1              3018          3649
      4              2978          6162
     16              2019          9080
```

With one fsync per commit, more threads don't help: commits wait for each other's syncs, and contention makes things a little worse. With group commit, throughput grows with the number of committers, 4.5 times at 16 threads, because each sync now makes many commits durable. The book's machine has a fast `fsync` (about 0.3 ms). On a disk where it takes 5–10 ms the effect is far larger, since one sync per commit then limits you to a few hundred commits per second however many threads you have.

### 13.5

```python
# src/minidb/database.py (add to Database)
    def verify(self) -> list[str]:
        """Re-check every constraint over all the data, and describe each violation.

        >>> from minidb.schema import Column
        >>> from minidb.types import Integer
        >>> db = Database()
        >>> _ = db.create_table("t", [Column("id", Integer(min=0))], primary_key="id")
        >>> _ = db.insert("t", {"id": 1})
        >>> db.table("t").rows[7] = {"id": -1}  # corrupt it behind the database's back
        >>> db.table("t").rows[8] = {"id": 1}
        >>> for problem in db.verify():
        ...     print(problem)
        t row 7: t.id: -1 is not a valid Integer(min=0, max=None): below minimum 0
        t: rows 1 and 8 share the key (1,) of ('id',)

        :return: one description per violation; empty if the data is valid.
        """
        with self.shared_lock():
            problems = [p for t in self.tables.values() for p in _row_problems(t)]
            problems += [p for t in self.tables.values() for p in _unique_problems(t)]
            problems += [p for fk in self.foreign_keys for p in self._reference_problems(fk)]
        return problems

    def _reference_problems(self, fk: ForeignKey) -> list[str]:
        parent = self.tables[fk.ref_table]
        return [
            f"{fk.name}: {fk.table} row {rowid} references missing {key}"
            for rowid, row in self.tables[fk.table].rows.items()
            if (key := fk.parent_key(row)) is not None and not parent.lookup(key)
        ]
```

```python
# src/minidb/database.py (append)
def _row_problems(t: Table) -> list[str]:
    """Run every single-row rule (types, NOT NULL, normalization, checks) on every row."""
    problems: list[str] = []
    for rowid, row in t.rows.items():
        try:
            if t.schema.prepare_row(row) != row:
                problems.append(f"{t.name} row {rowid}: stored values are not normalized")
        except DatabaseError as e:
            problems.append(f"{t.name} row {rowid}: {e}")
    return problems


def _unique_problems(t: Table) -> list[str]:
    """Find rows that share a unique key, without trusting the indexes."""
    problems: list[str] = []
    for columns in t.unique_keys():
        first: dict[tuple[Value | None, ...], int] = {}
        for rowid, row in t.rows.items():
            key = tuple(row[c] for c in columns)
            if any(v is None for v in key):
                continue
            if key in first:
                problems.append(f"{t.name}: rows {first[key]} and {rowid} share the key {key} of {columns}")
            first.setdefault(key, rowid)
    return problems
```

```python
# src/minidb/database.py (typing imports)
from minidb.values import Value
```

The checks read the rows, not the indexes, so they also catch an index that disagrees with the data (row 8 is in no index above). Run it automatically after recovering from a crash, after loading a snapshot written by an older version of the program or with different check functions ([13.6](#136)), and in the test suite after every randomized operation ([Appendix B](appendix-b-testing.md)). It costs O(rows × constraints), so not after every commit. SQLite's `PRAGMA integrity_check` is the same idea.

### 13.6

Add a check, or change one, to a table that already has data: `Column("qty", Integer(), check=lambda q: q >= 0)` where some stored rows have `qty = -3`. The fingerprint is the same, the snapshot loads, `decode_row` validates the types (which it does check), and the negative rows are now in a database that claims they can't exist. Changing a default doesn't invalidate data, but a changed normalizer does, in the same way. Real databases make schema changes explicit operations on the stored schema: `ALTER TABLE … ADD CONSTRAINT` checks the existing rows (or is created `NOT VALID` and validated later), and the schema itself is stored in the database, versioned with the data. Applications manage the sequence of changes with migration tools (Alembic, Flyway, Django migrations) that record which migrations have been applied.

### 13.7

Copy one table at a time, each under the shared lock just long enough to encode it, and record with each table the `commit_seq` at which it was copied. Writers run between tables, so the snapshot isn't one consistent state, which is what makes it *fuzzy*. Recovery loads each table, then replays the log from the **smallest** recorded `commit_seq`, applying each record's changes to a table only if the record is newer than that table's copy. That works because log records hold after-images: applying a record twice to the same row gives the same row, so replay is idempotent. Constraints that span tables hold again once the replay reaches the end of the log. The log can be truncated only up to the smallest recorded `commit_seq`, not to the end. ARIES's checkpoints work the same way, with a "redo start point" ([Mohan et al. 1992](references.md#mohan1992)).

### 13.8

minidb resembles **WAL mode**: its log holds after-images, recovery redoes them on top of the last snapshot, and a checkpoint folds the log into the snapshot. A rollback journal is the opposite: the database file is changed in place, and the journal keeps the before-images needed to undo a half-finished transaction. Some things SQLite does that minidb doesn't:

- It works with **pages**, not rows: the log records changed pages, and checkpoints copy pages back into the database file incrementally, without rewriting it.
- **Readers run concurrently with the writer** by remembering where the log ended when they started, a snapshot implemented with a shared-memory index of the log (the "wal-index").
- It **coordinates several processes** with file locks, not just threads.
- It reasons about **sector sizes and torn sector writes**, and checksums its log frames, with salts that change at every checkpoint so that stale frames are never mistaken for new ones.
- With several attached databases, a **super-journal** makes a commit atomic across files.

## Chapter 14 — Query Planning

### 14.1

Tuples compare element by element, so all keys that start with `('Paris',)` are adjacent in a sorted index on `(city, age)`, and within them the keys are sorted by `age`. A *prefix* bound only needs keys to be compared on as many columns as the bound has. Two private helpers of `SortedIndex` change, and full-length bounds behave as before. (`math.inf` is no longer needed.)

```python
# src/minidb/index.py (replace SortedIndex._start)
    def _start(self, lo: Key | None, *, lo_inclusive: bool) -> int:
        """Find the first entry at or after ``lo``, comparing keys on ``len(lo)`` columns only."""
        if lo is None:
            return 0
        width = len(lo)
        if lo_inclusive:
            return bisect.bisect_left(self._sorted, lo, key=lambda e: e[0][:width])
        return bisect.bisect_right(self._sorted, lo, key=lambda e: e[0][:width])
```

```python
# src/minidb/index.py (remove)
import math
```

```python
# src/minidb/index.py (replace _beyond)
def _beyond(key: Key, hi: Key | None, *, hi_inclusive: bool) -> bool:
    """Tell whether ``key`` lies past the upper bound ``hi``, comparing on ``len(hi)`` columns.

    >>> _beyond(("Paris", 40), ("Paris",), hi_inclusive=True)
    False
    """
    if hi is None:
        return False
    head = key[: len(hi)]
    return head > hi or (head == hi and not hi_inclusive)
```

The planner gets a third kind of candidate: equalities on a leading prefix of an ordered index's columns, plus the range conditions on the next column, if any. Its operator reads the committed index directly. A transaction's view would also have to record the prefix in its read set, which `TableView.range` doesn't do, so inside a transaction the planner doesn't offer it, and falls back to the other paths.

```python
# src/minidb/planner.py (append)
class PrefixRange(Operator):
    """Yield the rows between two keys of a composite ordered index; the keys may be prefixes.

    :param table: the committed table.
    :param alias: the qualifier for column names.
    :param index: the ordered index.
    :param bounds: ``(lo, hi, lo_inclusive, hi_inclusive)``, as key tuples.
    """

    def __init__(self, table: Table, alias: str, index: OrderedIndex, bounds: KeyBounds) -> None:
        self.table, self.alias, self.index, self.bounds = table, alias, index, bounds

    @override
    def __iter__(self) -> Iterator[Row]:
        lo, hi, lo_inclusive, hi_inclusive = self.bounds
        for rid in self.index.range(lo, hi, lo_inclusive=lo_inclusive, hi_inclusive=hi_inclusive):
            row = self.table.row(rid)
            yield Row({f"{self.alias}.{c}": row[c] for c in self.table.columns})

    @override
    def columns(self) -> list[str]:
        return [f"{self.alias}.{c}" for c in self.table.columns]

    @property
    @override
    def label(self) -> str:
        lo, hi, lo_inclusive, hi_inclusive = self.bounds
        return (
            f"PrefixRange {self.table.name} AS {self.alias} using {self.index.name}: "
            f"{lo} {'<=' if lo_inclusive else '<'} key {'<=' if hi_inclusive else '<'} {hi}"
        )


type KeyBounds = tuple[Key, Key, bool, bool]


def _prefix_bounds(prefix: Key, bounds: Bounds) -> KeyBounds:
    """Extend an equality prefix with the range bounds on the next column, if there are any."""
    lo, hi, lo_inclusive, hi_inclusive = bounds
    low = (*prefix, lo) if lo is not None else prefix
    high = (*prefix, hi) if hi is not None else prefix
    return low, high, lo_inclusive or lo is None, hi_inclusive or hi is None
```

```python
# src/minidb/planner.py (add to Planner)
    def _prefix_path(
        self,
        rel: Relation,
        index: Index,
        eq: dict[str, tuple[Value, Expr]],
        ranges: dict[str, list[RangeCondition]],
        n: int,
    ) -> Candidate | None:
        """Use equalities on a leading prefix of an ordered index, and a range on the next column."""
        if rel.source is not rel.table or not isinstance(index, OrderedIndex):
            return None  # committed tables only: a view's read set can't record prefixes
        prefix = list(itertools.takewhile(lambda c: c in eq, index.columns))
        if not prefix or len(prefix) == len(index.columns):
            return None  # nothing usable, or a whole key, which IndexLookup does better
        following = ranges.get(index.columns[len(prefix)], [])
        bounds = _prefix_bounds(tuple(eq[c][0] for c in prefix), _bounds(following))
        matches = n * math.prod(1 / (self.distinct(f"{rel.alias}.{c}") or 10) for c in prefix)
        matches *= (1 / 3) ** len(following)
        op = PrefixRange(rel.table, rel.alias, index, bounds)
        op.estimate = matches
        return (1 + matches, op, [eq[c][1] for c in prefix] + [p for _, _, p in following])
```

```python
# src/minidb/planner.py (replace Planner.access_path)
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
            found = (
                self._lookup_path(rel, index, eq, n),
                self._range_path(rel, index, ranges, n),
                self._prefix_path(rel, index, eq, ranges, n),
            )
            candidates.extend(c for c in found if c is not None)
        _, op, consumed = min(candidates, key=lambda c: c[0])
        estimate = n * math.prod(p.selectivity(self) for p in preds)
        residual = [p for p in preds if not any(p is c for c in consumed)]
        if residual:
            op = Filter(op, _conjunction(residual))
            op.estimate = estimate
        return op, estimate
```

```python
# src/minidb/planner.py (imports)
import itertools

from minidb.index import OrderedIndex
```

```python
# src/minidb/planner.py (typing imports)
from minidb.index import Key
from minidb.table import Table
```

```python
>>> from minidb import Column, Database, Integer, Text, col
>>> db = Database()
>>> _ = db.create_table("people", [Column("id", Integer()), Column("city", Text()), Column("age", Integer())],
...                     primary_key="id")
>>> for i in range(1000):
...     _ = db.insert("people", {"id": i, "city": ["Paris", "Rome", "Oslo", "Lima"][i % 4], "age": i % 90})
>>> db.create_index("people", "by_city_age", ["city", "age"], kind="sorted")
>>> db.analyze()
>>> print(db.query("people").where((col("city") == "Paris") & (col("age") > 80)).explain())
PrefixRange people AS people using by_city_age: ('Paris', 80) < key <= ('Paris',)  [~83 rows]
>>> len(db.query("people").where((col("city") == "Paris") & (col("age") > 80)).all())
22
>>> print(db.query("people").where(col("city") == "Rome").explain())
PrefixRange people AS people using by_city_age: ('Rome',) <= key <= ('Rome',)  [~250 rows]
```

### 14.2

```python
# examples/index_maintenance.py
"""Time 100,000 inserts with and without a sorted index."""

import time

from minidb import Column
from minidb import Database
from minidb import Integer

ROWS = 100_000


def time_inserts(kind: str | None) -> float:
    """Insert ``ROWS`` rows in random key order, with one index of ``kind`` (or none).

    :param kind: ``"hash"``, ``"sorted"``, or ``None`` for no index.
    :return: the time taken, in seconds.
    """
    db = Database()
    table = db.create_table("t", [Column("n", Integer())])
    if kind is not None:
        table.create_index("by_n", ["n"], kind=kind)
    t0 = time.perf_counter()
    with db.unit_of_work(exclusive=True):
        for i in range(ROWS):
            table.put(table.new_rowid(), {"n": (i * 7919) % ROWS})  # straight into the table
    return time.perf_counter() - t0


def main() -> None:
    """Print the time for each configuration."""
    for kind in (None, "hash", "sorted"):
        print(f"{kind or 'no index':>9}: {time_inserts(kind):6.2f} s")


if __name__ == "__main__":
    main()
```

The rows go straight into the table with `put`, so that the measurement is the indexes' cost and not the Unit of Work's.

```text
 no index:   0.08 s
     hash:   0.26 s
   sorted:   1.11 s
```

A hash index costs a constant amount per insert. The sorted list must shift every entry after the insertion point, half the list on average, so inserting n rows costs O(n²) in total. The shifting is a single `memmove` in C, which is why 100,000 rows still take only about a second. But the cost grows quadratically: ten times as many rows take about a hundred times as long, while the hash index takes ten times as long. The planner sees only the benefit of a sorted index for reads, never this cost for writes. A B-tree ([Chapter 15](15-b-trees.md)) makes each insert O(log n).

### 14.3

A pattern whose first character is not a wildcard has a literal *prefix*, and every match lies in the range `prefix ≤ s < successor(prefix)`, where the successor increments the prefix's last character: `'Ad%'` matches only strings in `['Ad', 'Ae')`. An ordered index can answer that range, and the `LIKE` itself stays on top as a filter, because the range is only a superset when the pattern has more wildcards (`'Ad%z'`). A pattern that starts with `%` or `_` can't use an ordered index at all. (With a case-insensitive collation, or characters near the top of Unicode, computing the successor is trickier: real systems do it in the collation's order.)

```python
# src/minidb/expr.py (append)
class Like(Expr):
    """Match strings against a SQL pattern: ``%`` is any run of characters, ``_`` any one.

    >>> e = col("name").like("Ad%")
    >>> e({"name": "Ada"}), e({"name": "Grace"}), e({"name": None})
    (True, False, None)
    >>> col("name").like("Ad_z%").prefix()
    'Ad'

    :param item: the string to test.
    :param pattern: the pattern.
    """

    def __init__(self, item: Expr, pattern: str) -> None:
        self.item, self.pattern = item, pattern
        parts = (".*" if ch == "%" else "." if ch == "_" else re.escape(ch) for ch in pattern)
        self._regex = re.compile("".join(parts), re.DOTALL)

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        value = self.item.eval(row)
        if value is None:
            return None
        return isinstance(value, str) and self._regex.fullmatch(value) is not None

    @override
    def columns(self) -> set[str]:
        return self.item.columns()

    def prefix(self) -> str:
        """Return the literal characters before the first wildcard.

        :return: the prefix, possibly empty.
        """
        return re.split(r"[%_]", self.pattern, maxsplit=1)[0]

    @override
    def selectivity(self, stats: Statistics) -> float:
        if self.prefix() == self.pattern:  # no wildcard: an equality
            return _eq_selectivity(stats.distinct(next(iter(self.columns()), "")))
        return RANGE_SELECTIVITY if self.prefix() else OTHER_SELECTIVITY

    def __repr__(self) -> str:
        return f"({self.item!r} LIKE {self.pattern!r})"


def successor(prefix: str) -> str:
    """Return the smallest string greater than every string that starts with ``prefix``.

    >>> successor("Ad")
    'Ae'

    :param prefix: a non-empty string.
    :return: the prefix with its last character incremented.
    """
    return prefix[:-1] + chr(ord(prefix[-1]) + 1)
```

```python
# src/minidb/expr.py (add to Expr)
    def like(self, pattern: str) -> Like:
        """Return the condition ``self LIKE pattern``.

        :param pattern: a SQL pattern, with ``%`` and ``_`` as wildcards.
        :return: the condition.
        """
        return Like(self, pattern)
```

```python
# src/minidb/expr.py (imports)
import re
```

In the planner, `_canonical` hands each condition to a helper, which also files a `LIKE` with a prefix as two range conditions. The conditions it files are new `Compare` objects, not the `LIKE` itself, so a range path "consumes" them and leaves the `LIKE` as a residual filter:

```python
# src/minidb/planner.py (replace Planner._canonical)
    def _canonical(
        self, rel: Relation, preds: list[Expr]
    ) -> tuple[list[Expr], dict[str, tuple[Value, Expr]], dict[str, list[RangeCondition]]]:
        """Normalize the constants in ``column op constant`` conditions, and sort them by use.

        :return: the rewritten conditions; the equalities by column; and the
            range conditions by column.
        """
        eq: dict[str, tuple[Value, Expr]] = {}
        ranges: dict[str, list[RangeCondition]] = {}
        canonical = [self._file(rel, p, eq, ranges) for p in preds]
        return canonical, eq, ranges

    def _file(
        self, rel: Relation, p: Expr, eq: dict[str, tuple[Value, Expr]], ranges: dict[str, list[RangeCondition]]
    ) -> Expr:
        """File ``p`` under ``eq`` or ``ranges`` if an index could use it; return it normalized."""
        if isinstance(p, Like):
            self._file_like(p, ranges)
            return p
        found = self._column_constant(rel, p)
        if found is None:
            return p
        q, column, value = found
        if q.op == "=":
            eq[column] = (value, q)
        elif q.op in ("<", "<=", ">", ">="):
            ranges.setdefault(column, []).append((q.op, value, q))
        return q

    def _file_like(self, p: Like, ranges: dict[str, list[RangeCondition]]) -> None:
        hit = self.resolve(p.item.name) if isinstance(p.item, Col) else None
        prefix = p.prefix()
        if hit is None or not prefix:
            return
        lo, hi = prefix, successor(prefix)
        conditions = ranges.setdefault(hit[1], [])
        conditions.append((">=", lo, Compare(">=", p.item, Const(lo))))
        conditions.append(("<", hi, Compare("<", p.item, Const(hi))))
```

```python
# src/minidb/planner.py (imports)
from minidb.expr import Like
from minidb.expr import successor
```

```python
>>> from minidb import Column, Database, Integer, Text, col
>>> db = Database()
>>> _ = db.create_table("people", [Column("id", Integer()), Column("name", Text())], primary_key="id")
>>> for i, name in enumerate(["Ada", "Adele", "Alan", "Grace", "Adz"]):
...     _ = db.insert("people", {"id": i, "name": name})
>>> db.create_index("people", "by_name", ["name"], kind="sorted")
>>> q = db.query("people").where(col("name").like("Ad%e%")).select("name")
>>> print(q.explain())
Project name
  Filter (name LIKE 'Ad%e%')  [~2 rows]
    IndexRange people AS people using by_name: 'Ad' <= name < 'Ae'  [~1 rows]
>>> q.all()
[{'name': 'Adele'}]
```

### 14.4

It's the same default System R uses for any range comparison, and when nothing is known, a fixed fraction is as good as any. But it can be badly wrong, because two columns of one row are usually *related*. Take `end_date >= start_date`: it is true for practically every row, not a third. Or `discount > price`: it is false for practically every row. Statistics on each column separately can't tell, since they describe the columns independently. What helps is a statistic on the *relationship*: a histogram of `age - min_age` (PostgreSQL's *expression statistics*), a joint histogram of the column pair, or simply a sample of rows on which the condition is evaluated at `analyze()` time, storing the fraction that pass.

### 14.5

System R's dynamic programming keeps, for every subset of relations, the cheapest *left-deep* order that joins exactly that subset. Larger subsets are built by adding one relation to the best plan of a smaller subset. Cost is the sum of the estimated sizes of the intermediate results, as in the greedy planner. A subclass changes only `join`:

```python
# src/minidb/planner.py (append)
type JoinPlans = dict[frozenset[str], tuple[float, tuple[str, ...]]]  # subset -> (cost, join order)


class DPPlanner(Planner):
    """Order joins by dynamic programming over subsets of relations, as System R does.

    For every subset, keep the cheapest left-deep join order: the one whose
    intermediate results add up to the fewest estimated rows. Planning costs
    O(2^n · n) for n relations.
    """

    @override
    def join(self, paths: dict[str, tuple[Operator, float]], multi: list[tuple[Expr, set[str]]]) -> Operator:
        best: JoinPlans = {frozenset([a]): (0.0, (a,)) for a in paths}
        for size in range(2, len(paths) + 1):
            for subset in map(frozenset, itertools.combinations(paths, size)):
                best[subset] = min(self._extend(best, subset, a, paths, multi) for a in subset)
        return self._build(best[frozenset(paths)][1], paths, multi)

    def _extend(
        self,
        best: JoinPlans,
        subset: frozenset[str],
        last: str,
        paths: dict[str, tuple[Operator, float]],
        multi: list[tuple[Expr, set[str]]],
    ) -> tuple[float, tuple[str, ...]]:
        """Cost the best plan for ``subset - {last}`` followed by a join with ``last``."""
        cost, order = best[subset - {last}]
        return cost + self.size(subset, paths, multi), (*order, last)

    def size(
        self, subset: frozenset[str], paths: dict[str, tuple[Operator, float]], multi: list[tuple[Expr, set[str]]]
    ) -> float:
        """Estimate the number of rows of joining ``subset``.

        :param subset: the aliases joined.
        :param paths: the access path and estimate of each relation.
        :param multi: the conditions between relations, with their aliases.
        :return: the estimated size.
        """
        inside = [e for e, aliases in multi if aliases <= subset]
        return math.prod(paths[a][1] for a in subset) * math.prod(e.selectivity(self) for e in inside)

    def _build(
        self, order: tuple[str, ...], paths: dict[str, tuple[Operator, float]], multi: list[tuple[Expr, set[str]]]
    ) -> Operator:
        """Join the access paths in ``order``, with the best join operator at each step."""
        op, est = paths[order[0]]
        joined, pending = {order[0]}, list(multi)
        for alias in order[1:]:
            right, right_est = paths[alias]
            usable = [e for e, al in pending if alias in al and al <= joined | {alias}]
            pending = [(e, al) for e, al in pending if not any(e is u for u in usable)]
            op = self._join_op(
                op, left_est=est, right=right, right_est=right_est, alias=alias, joined=joined, usable=usable
            )
            joined.add(alias)
            est = self.size(frozenset(joined), paths, multi)
            op.estimate = est
        for e, _ in pending:
            op = Filter(op, e)
        return op
```

```python
# src/minidb/planner.py (imports)
import itertools
```

The comparison builds a chain of tables, each joined to the next. The sizes and key distributions are chosen so that the smallest table, where greedy starts, is not where the best plan starts:

```python
# examples/join_order.py
"""Compare greedy and dynamic-programming join orders on chain queries."""

import time

from minidb import Column
from minidb import Count
from minidb import Database
from minidb import Integer
from minidb import Query
from minidb import col
from minidb.planner import DPPlanner
from minidb.planner import Planner

SIZES = [1000, 20, 1000, 300, 100, 100, 100, 100, 100, 100]
KEYS = [20, 10, 300, 100, 100, 100, 100, 100, 100, 100]  # distinct values of each table's "next"


def build(n: int) -> Database:
    """Create ``n`` tables ``t0 … t(n-1)``; ``t(i).next`` joins ``t(i+1).id``.

    :param n: the number of tables.
    :return: the database, analyzed.
    """
    db = Database()
    for i in range(n):
        db.create_table(f"t{i}", [Column("id", Integer()), Column("next", Integer())])
        with db.unit_of_work() as uow:
            for r in range(SIZES[i]):
                uow.insert(f"t{i}", {"id": r % KEYS[i - 1] if i else r, "next": r % KEYS[i]})
    db.analyze()
    return db


def chain(db: Database, n: int) -> Query:
    """Return the query joining the ``n`` tables in a chain.

    :param db: the database.
    :param n: the number of tables.
    :return: the query.
    """
    q = db.query("t0")
    for i in range(1, n):
        q = q.join(f"t{i}", col(f"t{i - 1}.next") == col(f"t{i}.id"))
    return q.group_by(rows=Count())


def report(db: Database, q: Query, planner: type[Planner]) -> str:
    """Plan and run ``q`` with ``planner``.

    :param db: the database.
    :param q: the query.
    :param planner: the planner class.
    :return: a line with planning time, run time, and the result.
    """
    t0 = time.perf_counter()
    plan = planner(q).plan()
    planned = time.perf_counter() - t0
    t0 = time.perf_counter()
    with db.reading():
        rows = list(plan)
    ran = time.perf_counter() - t0
    return f"{planner.__name__:>10}: planned in {planned * 1000:7.1f} ms, ran in {ran:6.2f} s, {rows}"


def main() -> None:
    """Compare the planners on 5 tables, then time planning alone for 10."""
    db = build(5)
    for planner in (Planner, DPPlanner):
        print(report(db, chain(db, 5), planner))
    db = build(10)
    for planner in (Planner, DPPlanner):
        t0 = time.perf_counter()
        planner(chain(db, 10)).plan()
        print(f"{planner.__name__:>10}: 10 tables planned in {(time.perf_counter() - t0) * 1000:.1f} ms")


if __name__ == "__main__":
    main()
```

```text
   Planner: planned in     0.2 ms, ran in   0.35 s, [{'rows': 100000}]
 DPPlanner: planned in     0.5 ms, ran in   0.13 s, [{'rows': 100000}]
   Planner: 10 tables planned in 0.3 ms
 DPPlanner: 10 tables planned in 24.0 ms
```

Greedy starts with the smallest table, `t1` (20 rows), and joins `t0` next, its cheapest neighbour at that moment, which produces 1,000 rows. Each later step then carries those rows along. Dynamic programming finds that starting from the other end (`t3 ⋈ t4`, then `t2`, `t1`, `t0`) keeps the intermediate results small: about 103,000 estimated rows in total instead of 301,000, and the query runs almost three times faster. Planning time grows as 2ⁿ: 24 ms for 10 tables is fine, but 20 tables would take about a thousand times longer, which is why real systems switch to heuristics or genetic search above some number of tables (PostgreSQL's `geqo_threshold` is 12).

### 14.6

```python
>>> from minidb import Column, Database, Integer, Text, col
>>> db = Database()
>>> _ = db.create_table("t", [Column("id", Integer()), Column("city", Text()), Column("country", Text())],
...                     primary_key="id")
>>> places = [("Paris", "France"), ("Lyon", "France"), ("Nice", "France"), ("Rome", "Italy"), ("Milan", "Italy")]
>>> for i in range(1000):
...     city, country = places[i % 5]
...     _ = db.insert("t", {"id": i, "city": city, "country": country})
>>> db.analyze()
>>> q = db.query("t").where((col("city") == "Paris") & (col("country") == "France"))
>>> print(q.explain())
Filter ((city = 'Paris') AND (country = 'France'))  [~100 rows]
  Scan t AS t  [~1,000 rows]
>>> len(q.all())
200
```

The planner multiplies 1/5 by 1/2 as if the columns were independent. But knowing the city *determines* the country, so the second condition removes nothing, and the true answer is twice the estimate. With more cities per country the error grows: with 100 cities in 10 countries, it is 10 times. In a join plan, such errors multiply. The fix is a statistic about the pair. `analyze()` could also count the distinct values of each *pair* of columns that appear together in conditions (or of all pairs, for small tables): 5 for `(city, country)`. The selectivity of `city = ? AND country = ?` is then 1/distinct(pair) = 1/5, not 1/5 × 1/2. PostgreSQL's `CREATE STATISTICS … (ndistinct, dependencies)` does exactly this, for the column groups that the user names.

### 14.7

A `WHERE` condition on the **preserved** side of a `LEFT JOIN` can be applied before the join: removing a left row early removes exactly the output rows it would have produced, matched or padded. A condition on the **null-supplying** (right) side can't, in general: filtering the right input first changes which left rows find *no* match, so it turns removed rows into NULL-padded ones. `WHERE r.x IS NULL` is the classic example, the "anti-join" idiom. But if the condition *rejects NULL* (it isn't true when the right side's columns are NULL, like `r.x > 5`), then the padded rows would be removed anyway, and the outer join gives the same result as an inner join. Three-valued logic makes the test easy: evaluate the condition on a row whose columns are all NULL.

```python
# src/minidb/planner.py (append)
class OuterJoinPlanner(Planner):
    """Also optimize queries with left joins.

    A left join whose right side a WHERE condition rejects when NULL becomes
    an inner join, which the planner can then reorder. In the remaining
    outer-join queries, the joins keep their written order, but conditions
    on the first table (which every left join preserves) are pushed below
    them, into its access path.
    """

    @override
    def plan(self) -> Operator:
        simpler = self._inner_where_possible()
        if simpler is not None:
            return OuterJoinPlanner(simpler).plan()
        if all(kind == "inner" for _, _, _, kind in self.q.joins):
            return super().plan()
        return self._outer_plan()

    def _where(self) -> list[RowPredicate]:
        return [p for f in self.q.filters for p in (conjuncts(f) if isinstance(f, Expr) else [f])]

    def _inner_where_possible(self) -> Query | None:
        """Return the query with null-rejected left joins made inner, or ``None`` if there are none."""
        where = [p for p in self._where() if isinstance(p, Expr)]
        joins = list(self.q.joins)
        changed = False
        for i, (table, alias, on, kind) in enumerate(joins):
            if kind == "left" and any(self.aliases(p) == {alias or table} and _rejects_null(p) for p in where):
                joins[i] = (table, alias, on, "inner")
                changed = True
        return replace(self.q, joins=tuple(joins)) if changed else None

    def _outer_plan(self) -> Operator:
        """Join in the written order, with the first table's own conditions pushed below the joins."""
        first = self.q.alias or self.q.table
        where = self._where()
        preserved = all(kind in ("inner", "left") for _, _, _, kind in self.q.joins)
        pushed = [p for p in where if preserved and isinstance(p, Expr) and self.aliases(p) == {first}]
        op, _ = self.access_path(self.rels[first], pushed)
        for table, alias, on, kind in self.q.joins:
            op = NestedLoopJoin(op, Scan(self.q.state.table(table), alias), on, kind)
        for p in where:
            if not any(p is x for x in pushed):
                op = Filter(op, p)
        return self.q.finish_plan(op)


def _rejects_null(condition: Expr) -> bool:
    """Tell whether ``condition`` fails (is FALSE or UNKNOWN) when all its columns are NULL."""
    return condition.eval(dict.fromkeys(condition.columns())) is not True
```

```python
# src/minidb/planner.py (imports)
from dataclasses import replace
```

```python
>>> from minidb import Column, Database, Integer, col
>>> from minidb.planner import OuterJoinPlanner
>>> db = Database()
>>> _ = db.create_table("u", [Column("id", Integer())], primary_key="id")
>>> _ = db.create_table("o", [Column("id", Integer()), Column("uid", Integer()), Column("n", Integer())],
...                     primary_key="id")
>>> for i in range(3):
...     _ = db.insert("u", {"id": i})
>>> _ = db.insert("o", {"id": 10, "uid": 1, "n": 7})
>>> left = db.query("u").join("o", col("u.id") == col("o.uid"), kind="left")
>>> print(OuterJoinPlanner(left.where(col("u.id") >= 1)).plan().explain())
NestedLoopJoin (left)
  Filter (u.id >= 1)  [~1 rows]
    Scan u AS u  [~3 rows]
  Scan o AS o
>>> print(OuterJoinPlanner(left.where(col("o.n") > 5)).plan().explain())
HashJoin (build left) on o.uid = u.id  [~0 rows]
  Filter (o.n > 5)  [~0 rows]
    Scan o AS o  [~1 rows]
  Scan u AS u  [~3 rows]
>>> [r["u.id"] for r in OuterJoinPlanner(left.where(col("o.n").is_null())).plan()]
[0, 2]
```

The first plan filters the users before joining them. In the second, the join became inner: the planner reordered it, pushed `o.n > 5` down to `o`, and used a hash join. The third keeps the outer join, because `IS NULL` is true for padded rows.

### 14.8

```python
# src/minidb/database.py (replace Database.select)
    def select(self, table: str, where: Where = None) -> list[Row]:
        """Return the rows of ``table`` matching ``where``, through the query planner.

        >>> from minidb.schema import Column
        >>> from minidb.types import Integer
        >>> db = Database()
        >>> _ = db.create_table("t", [Column("id", Integer()), Column("n", Integer())], primary_key="id")
        >>> for i in range(3):
        ...     _ = db.insert("t", {"id": i, "n": i * i})
        >>> db.select("t", {"id": "2"})
        [{'id': 2, 'n': 4}]
        >>> print(db.query("t").where(col("id") == "2").explain())
        IndexLookup t AS t using pk {'id': 2}  [~1 rows]

        :param table: the table's name.
        :param where: a predicate, a dict of equalities, or ``None`` for all rows.
        :return: copies of the matching rows.
        """
        q = self.query(table)
        if isinstance(where, Mapping) and where:
            q = q.where(And(*(col(c) == v for c, v in where.items())))
        elif callable(where):
            q = q.where(where)
        return q.select(*self.table(table).columns).all()
```

```python
# src/minidb/database.py (imports)
from collections.abc import Mapping

from minidb.expr import And
from minidb.expr import col
```

```python
# src/minidb/database.py (replace typing imports)
from collections.abc import Callable
from collections.abc import Iterator
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
```

A dict of equalities becomes a conjunction of `col(c) == value` expressions, which the planner can match against any index, now including sorted and composite ones. Constants are normalized the same way as before (`"2"` becomes `2`). One behaviour changes: a value that isn't valid for its column used to raise `DomainError`, and now simply matches nothing, because the planner compares invalid constants "as written". `Table.match` is still used by `update` and `delete`, which need rowids rather than rows. Moving them to the planner too would need a plan that returns rowids, which is how real systems do it.

## Chapter 15 — B-Trees

### 15.1

An internal entry is a 16-byte key plus an 8-byte child pointer: 24 bytes, so an 8 KB page holds 8192 / 24 ≈ 341 entries, and 70% full means a fanout of about **239**. Assume the leaves hold key plus 8-byte rowid, also 24 bytes, so about 239 entries per leaf too. Then:

- leaves: 10⁸ / 239 ≈ 418,400 pages;
- the level above: 418,400 / 239 ≈ 1,751 pages;
- above that: 1,751 / 239 ≈ 7.3, so 8 pages;
- and the root: 1 page.

The height is **4**. A lookup reads 4 pages. With the top two levels (9 pages, 72 KB) cached, it reads **2**: one of the 1,751 internal pages and one leaf. Caching the third level too would take 14 MB and leave one read per lookup.

### 15.2

Leaves may hold no fewer than `order // 2` keys, and internal nodes no fewer than ⌈order / 2⌉ children (the root is exempt). After a deletion, an underfull node first tries to **borrow** an entry from an adjacent sibling with the same parent, preferring the left one. A leaf borrows a key, and the separator between the two becomes the new first key of the right one. An internal node rotates through the parent: the parent's separator comes down, and the sibling's outermost key goes up. If neither sibling can spare an entry, the node **merges** with one of them, the parent loses a separator and a child, and the parent may underflow in turn. When the root is left with a single child, the tree loses a level.

```python
# src/minidb/btree.py (replace BPlusTree.remove)
    def remove(self, key: K, value: V) -> None:
        """Remove ``value`` from ``key``, dropping the key when its set is empty.

        Underfull nodes borrow from a sibling or merge with it, so every
        node except the root stays at least half full.

        :param key: the key.
        :param value: the value to remove; nothing happens if it is absent.
        """
        leaf, path = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i == len(leaf.keys) or leaf.keys[i] != key:
            return
        leaf.values[i].discard(value)
        if leaf.values[i]:
            return
        del leaf.keys[i], leaf.values[i]
        self._len -= 1
        self._rebalance(leaf, path)

    def _rebalance(self, node: _Node[K, V], path: list[_Internal[K, V]]) -> None:
        """Restore the minimum size of ``node``, whose ancestors are ``path``."""
        if not path:
            if isinstance(node, _Internal) and len(node.children) == 1:
                self.root = node.children[0]  # the tree loses a level
            return
        if _size(node) >= self._minimum(node):
            return
        parent = path[-1]
        i = next(j for j, child in enumerate(parent.children) if child is node)
        if not self._borrow(parent, i):
            _merge(parent, i - 1 if i > 0 else i)
            self._rebalance(parent, path[:-1])

    def _minimum(self, node: _Node[K, V]) -> int:
        return self.order // 2 if isinstance(node, _Leaf) else (self.order + 1) // 2

    def _borrow(self, parent: _Internal[K, V], i: int) -> bool:
        """Move one entry into ``parent.children[i]`` from a sibling that can spare one."""
        for j in (i - 1, i + 1):  # the left sibling first
            if 0 <= j < len(parent.children) and _size(parent.children[j]) > self._minimum(parent.children[j]):
                _move(parent, i, j)
                return True
        return False
```

```python
# src/minidb/btree.py (append)
def _size[K: Ordered, V](node: _Node[K, V]) -> int:
    """Return the number of keys of a leaf, or of children of an internal node."""
    return len(node.keys) if isinstance(node, _Leaf) else len(node.children)


def _move[K: Ordered, V](parent: _Internal[K, V], i: int, j: int) -> None:
    """Move one entry from child ``j`` to its neighbour, child ``i``, updating their separator."""
    node, sibling, sep = parent.children[i], parent.children[j], min(i, j)
    from_left = j < i
    if isinstance(node, _Leaf) and isinstance(sibling, _Leaf):
        _move_key(node, sibling, from_left=from_left)
        parent.keys[sep] = (node if from_left else sibling).keys[0]
    elif isinstance(node, _Internal) and isinstance(sibling, _Internal):
        parent.keys[sep] = _rotate(node, sibling, parent.keys[sep], from_left=from_left)


def _move_key[K: Ordered, V](node: _Leaf[K, V], sibling: _Leaf[K, V], *, from_left: bool) -> None:
    if from_left:
        node.keys.insert(0, sibling.keys.pop())
        node.values.insert(0, sibling.values.pop())
    else:
        node.keys.append(sibling.keys.pop(0))
        node.values.append(sibling.values.pop(0))


def _rotate[K: Ordered, V](node: _Internal[K, V], sibling: _Internal[K, V], separator: K, *, from_left: bool) -> K:
    """Bring the parent's separator down into ``node`` and a sibling's key up; return the new separator."""
    if from_left:
        node.children.insert(0, sibling.children.pop())
        node.keys.insert(0, separator)
        return sibling.keys.pop()
    node.children.append(sibling.children.pop(0))
    node.keys.append(separator)
    return sibling.keys.pop(0)


def _merge[K: Ordered, V](parent: _Internal[K, V], j: int) -> None:
    """Merge child ``j + 1`` of ``parent`` into child ``j``."""
    left, right = parent.children[j], parent.children[j + 1]
    if isinstance(left, _Leaf) and isinstance(right, _Leaf):
        left.keys += right.keys
        left.values += right.values
        left.next = right.next
    elif isinstance(left, _Internal) and isinstance(right, _Internal):
        left.keys += [parent.keys[j], *right.keys]
        left.children += right.children
    del parent.keys[j], parent.children[j + 1]
```

The test runs 20,000 random inserts and removes on a tree of order 4, where splits and merges happen all the time. After every operation it compares the tree with a dict, and checks the structural invariants: every non-root node at least half full, all leaves at the same depth, and keys in order, both inside nodes and along the leaf chain.

```python
>>> import random
>>> from minidb.btree import BPlusTree, _Internal, _Leaf
>>> def check(tree):
...     depths, stack = set(), [(tree.root, 1)]
...     while stack:
...         node, depth = stack.pop()
...         assert node.keys == sorted(node.keys)
...         if isinstance(node, _Internal):
...             assert node is tree.root or len(node.children) >= (tree.order + 1) // 2
...             stack += [(c, depth + 1) for c in node.children]
...         else:
...             assert node is tree.root or len(node.keys) >= tree.order // 2
...             depths.add(depth)
...     assert len(depths) == 1
>>> rnd, tree, model = random.Random(7), BPlusTree[int, int](order=4), {}
>>> for step in range(20_000):
...     k, v = rnd.randrange(200), rnd.randrange(3)
...     if rnd.random() < 0.5:
...         tree.insert(k, v); model.setdefault(k, set()).add(v)
...     else:
...         tree.remove(k, v)
...         if k in model:
...             model[k].discard(v)
...             if not model[k]: del model[k]
...     check(tree)
...     assert [(k, set(vs)) for k, vs in tree.items()] == sorted(model.items())
>>> len(tree) == len(model), tree.height
(True, 5)
```

### 15.3

Bulk loading groups the sorted input into leaves, as full as possible, links them, and then builds each level above by grouping the level below into nodes of up to `order` children. The separators are the smallest keys of the children. Spreading the entries evenly over the minimum number of nodes keeps every node, including the last one, at least half full.

```python
# src/minidb/btree.py (add to BPlusTree)
    @classmethod
    def from_sorted(cls, items: Iterable[tuple[K, V]], order: int = 64) -> BPlusTree[K, V]:
        """Build a tree from ``(key, value)`` pairs sorted by key, filling the nodes.

        >>> tree = BPlusTree[int, str].from_sorted([(k, f"v{k}") for k in range(10)], order=4)
        >>> print(tree.dump())
        [3 6 8]
        [0 1 2]   [3 4 5]   [6 7]   [8 9]

        :param items: the pairs, sorted by key; equal keys may repeat.
        :param order: the maximum number of children per node; 64 by default.
        :return: the new tree.
        :raises ValueError: if the keys are not sorted, or ``order`` is below 3.
        """
        tree = cls(order)
        tree.bulk_load(items)
        return tree

    def bulk_load(self, items: Iterable[tuple[K, V]]) -> None:
        """Fill an empty tree from ``(key, value)`` pairs sorted by key.

        :param items: the pairs, sorted by key; equal keys may repeat.
        :raises ValueError: if the tree isn't empty, or the keys are not sorted.
        """
        if len(self):
            raise ValueError("bulk_load needs an empty tree")
        keys, values = _grouped(items)
        if not keys:
            return
        level: list[tuple[K, _Node[K, V]]] = [(leaf.keys[0], leaf) for leaf in _leaves(keys, values, self.order - 1)]
        while len(level) > 1:
            groups = [level[lo:hi] for lo, hi in _spans(len(level), _chunk_count(len(level), self.order))]
            level = [(g[0][0], _Internal[K, V]([k for k, _ in g[1:]], [n for _, n in g])) for g in groups]
        self.root, self._len = level[0][1], len(keys)
```

```python
# src/minidb/btree.py (append)
def _grouped[K: Ordered, V](items: Iterable[tuple[K, V]]) -> tuple[list[K], list[set[V]]]:
    """Collect sorted pairs into parallel lists of distinct keys and value sets."""
    keys: list[K] = []
    values: list[set[V]] = []
    for key, value in items:
        if keys and key == keys[-1]:
            values[-1].add(value)
            continue
        if keys and key < keys[-1]:
            raise ValueError(f"keys are not sorted: {key!r} after {keys[-1]!r}")
        keys.append(key)
        values.append({value})
    return keys, values


def _leaves[K: Ordered, V](keys: list[K], values: list[set[V]], capacity: int) -> list[_Leaf[K, V]]:
    """Spread the entries evenly over as few linked leaves as ``capacity`` allows."""
    leaves = [_Leaf[K, V]() for _ in range(_chunk_count(len(keys), capacity))]
    for leaf, (lo, hi) in zip(leaves, _spans(len(keys), len(leaves)), strict=True):
        leaf.keys, leaf.values = keys[lo:hi], values[lo:hi]
    for leaf, following in itertools.pairwise(leaves):
        leaf.next = following
    return leaves


def _chunk_count(n: int, capacity: int) -> int:
    return -(-n // capacity)  # ceiling division


def _spans(n: int, chunks: int) -> list[tuple[int, int]]:
    """Split ``range(n)`` into ``chunks`` consecutive spans whose sizes differ by at most one."""
    size, extra = divmod(n, chunks)
    starts = [i * size + min(i, extra) for i in range(chunks + 1)]
    return list(itertools.pairwise(starts))
```

```python
# src/minidb/btree.py (imports)
import itertools
```

```python
# examples/bulk_load.py
"""Compare building a B+ tree by repeated insert with bulk loading."""

import time

from minidb.btree import BPlusTree

N = 200_000


def main() -> None:
    """Print build time, height and number of leaves for both methods."""
    pairs = [(k, k) for k in range(N)]
    t0 = time.perf_counter()
    inserted = BPlusTree[int, int](order=64)
    for k, v in pairs:
        inserted.insert(k, v)
    t_insert = time.perf_counter() - t0
    t0 = time.perf_counter()
    loaded = BPlusTree[int, int].from_sorted(pairs, order=64)
    t_bulk = time.perf_counter() - t0
    for name, tree, t in (("insert", inserted, t_insert), ("bulk load", loaded, t_bulk)):
        leaves = tree.dump().splitlines()[-1].count("[")
        print(f"{name:>10}: {t:5.2f} s, height {tree.height}, {leaves:,} leaves, {N / leaves:.1f} keys per leaf")


if __name__ == "__main__":
    main()
```

```text
    insert:  0.41 s, height 4, 6,250 leaves, 32.0 keys per leaf
 bulk load:  0.16 s, height 3, 3,175 leaves, 63.0 keys per leaf
```

Sorted inserts always land in the last leaf, which splits in half and is never touched again, so every leaf stays exactly half full. Bulk loading fills the leaves (63 keys each with order 64), needs half as many, saves a level, and is about 2.5 times faster, because it never searches the tree or splits a node. It is how databases build an index on existing data: sort, then load bottom-up.

### 15.4

It isn't necessary for correctness: SQL promises no order among rows with equal keys, and the planner doesn't rely on one. It makes results deterministic, which doctests and the differential tests of [Appendix B](appendix-b-testing.md#exercises) need. Sets of small ints iterate in a fairly stable order in CPython, but that is an implementation detail. A disk-based index stores one entry per row, `(key, rowid)` pairs sorted on both ([15.5](#155)), so it returns equal keys in rowid order for free, with no sorting at all.

### 15.5

Making entries unique with `(key, rowid)`:

- **For.** Every entry has the same shape and a bounded size, so a page holds a predictable number. A key with millions of rows is just millions of entries spread over many leaves, instead of one huge set that can't fit in any page and must be rewritten whenever a row changes. Deleting one row's entry is an ordinary O(log n) delete. Splits, merges and concurrency control work entry by entry. And equal keys come out in rowid order.
- **Against.** The key is stored once per row, which wastes space for low-cardinality columns (prefix compression or deduplication wins most of it back, as in PostgreSQL 13's B-tree deduplication). The tree has more entries, and can be taller. An equality lookup becomes a range scan from `(key, -∞)` to `(key, +∞)`. And counting distinct keys is no longer `len(tree)`.

Most disk-based systems choose unique entries. InnoDB's secondary indexes, for example, append the primary key to every entry.

### 15.6

Only the separators produced by *leaf* splits are truncated. That is where almost all separators come from, since there are about `order` times as many leaves as internal nodes. The shortest string `s` with `left < s ≤ right` is `right` cut just after its common prefix with `left`. Lookups still work: `bisect_right` sends every key ≥ `s` to the right, and the left leaf's keys are all < `s`.

```python
# src/minidb/btree.py (replace BPlusTree._split_leaf)
    def _split_leaf(self, leaf: _Leaf[K, V], path: list[_Internal[K, V]]) -> None:
        mid = len(leaf.keys) // 2
        right = _Leaf[K, V]()
        right.keys, leaf.keys = leaf.keys[mid:], leaf.keys[:mid]
        right.values, leaf.values = leaf.values[mid:], leaf.values[:mid]
        right.next, leaf.next = leaf.next, right
        self._insert_in_parent(leaf, _separator(leaf.keys[-1], right.keys[0]), right, path)
```

```python
# src/minidb/btree.py (append)
def _separator[K: Ordered](left: K, right: K) -> K:
    """Return the shortest key ``s`` with ``left < s <= right``: a prefix of ``right``, for strings.

    >>> _separator("Smith, Joan", "Smithers")
    'Smithe'
    """
    if not (isinstance(left, str) and isinstance(right, str)):
        return right
    common = len(os.path.commonprefix([left, right]))
    return cast("K", right[: common + 1])
```

```python
# src/minidb/btree.py (imports)
import os
from typing import cast
```

The measurement inserts 100,000 e-mail addresses in random order, and compares each separator in the tree with the key it replaces, the smallest stored key ≥ the separator:

```python
# examples/separators.py
"""Measure how much suffix truncation shortens the separators of a B+ tree of strings."""

import bisect
import random

from minidb.btree import BPlusTree

N, PAGE, POINTER = 100_000, 8192, 8


def main() -> None:
    """Print the average separator length, and the fanout it allows with 8 KB pages."""
    keys = [f"customer{i:06d}@example.org" for i in range(N)]
    shuffled = random.Random(1).sample(keys, N)  # noqa: S311 - test data
    tree = BPlusTree[str, int](order=64)
    for i, key in enumerate(shuffled):
        tree.insert(key, i)
    separators = [s for line in tree.dump().splitlines()[:-1] for s in line.replace("[", " ").replace("]", " ").split()]
    full = [keys[bisect.bisect_left(keys, s)] for s in separators]
    for name, seps in (("whole keys", full), ("truncated", separators)):
        average = sum(len(s) for s in seps) / len(seps)
        print(f"{name:>10}: {average:5.1f} bytes per separator, fanout {PAGE // (average + POINTER):.0f}")


if __name__ == "__main__":
    main()
```

```text
whole keys:  26.0 bytes per separator, fanout 240
 truncated:  13.7 bytes per separator, fanout 378
```

Neighbouring keys share their first 11 to 14 characters (`customer0123…`), so a truncated separator needs only one more, and the shared `@example.org` suffix disappears completely. Separators shrink to about half their length, and with 8 KB pages and 8-byte child pointers the fanout rises from 240 to 378. In our tree `order` counts children, so nothing changes in memory. On disk, where a node is a page of fixed *bytes*, the higher fanout means a shallower tree.

### 15.7

Comer's survey describes the original **B-tree** (keys and data in every node), the **B⁺-tree** (all keys in the leaves, which are linked; internal nodes hold only separators), the **B\*-tree** (nodes kept at least two-thirds full by redistributing between siblings before splitting, often splitting two nodes into three), and **prefix B-trees** (Bayer and Unterauer's compressed separators, [15.6](#156)). It also covers **virtual B-trees**, where paging the tree into memory is left to virtual memory, and *binary B-trees*, a binary representation of order-3 trees that later became red–black trees. Ours is a **B⁺-tree**: separators in internal nodes, keys and values only in leaves, and a `next` link between leaves for range scans.

### 15.8

**What changes.** `table.py`: rows move from a dict into a B-tree keyed by rowid (a clustered table), whose nodes are fixed-size pages. `btree.py` becomes page-based: nodes are encoded into pages, children are page numbers instead of Python references, and every access goes through a **buffer pool** (a new module) that caches pages, evicts with LRU or clock, and writes dirty pages back. `storage.py`: the snapshot disappears. The data file *is* the database, and the WAL records page changes (or row changes plus a page-level redo) with LSNs on pages, so recovery knows which records a page already contains. Checkpoints flush dirty pages instead of writing a snapshot. `index.py`: secondary indexes become disk B-trees too, storing `(key, rowid)`. `locks.py` gains page *latches*, short locks protecting a page in the buffer pool while a thread reads or splits it.

**What doesn't.** The operators, the expressions, the planner, constraints, the Unit of Work, the SQL parser and the public API all stay as they are, because they only see tables through the `Source`, `PlannedSource`, `TableLike` and `Index` protocols.

**Decisions that help.** Encoding values with `to_primitive`/`from_primitive` gives each type a serialized form already. Changes are planned before being applied, and they flow through the single choke point `Database.apply`, which is exactly where page writes and WAL records go. The protocols decouple the query engine from storage, and rowids are never reused.

**Decisions that hurt.** Rows are Python dicts handed out by reference (`TableView.row` returns the stored row): with pages, every read decodes, so the "never mutate a stored row" rule turns into a real copy. Optimistic validation relies on per-row version dictionaries and whole-table versions in memory, which would have to move onto pages or into a lock manager. Statistics are recomputed by scanning everything. And the read set holds Python objects with no bound on their size.


## Appendix A — A SQL Parser

### A.1

`BETWEEN` is an infix operator with the binding power of a comparison. The trick is in how its operands are parsed. The lower bound is parsed with `min_bp` equal to `AND`'s binding power, so the parser stops in front of the `AND` instead of treating it as a logical operator. That `AND` is then consumed as part of `BETWEEN`, and the upper bound is parsed at comparison strength, so in `x BETWEEN 1 AND 5 AND y = 2` the second `AND` is logical again. Precedence climbing makes this a matter of passing the right number: each operand ends exactly where an operator binds no tighter than the one we give.

```python
# src/minidb/sql.py (replace KEYWORDS)
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
        "BETWEEN",
    }
)
```

```python
# src/minidb/sql.py (replace Parser.INFIX)
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
        "BETWEEN": 40,
        "+": 50,
        "-": 50,
        "*": 60,
        "/": 60,
    }
```

```python
# src/minidb/sql.py (replace Parser._infix)
    def _infix(self, op: str, left: Expr, bp: int) -> Expr:
        """Build the expression for ``left op ...``, parsing the right-hand side."""
        special: dict[str, Callable[[Expr], Expr]] = {
            "IS": self._is,
            "IN": lambda e: self._in(e, negate=False),
            "NOT": lambda e: self._in(e, negate=True),
            "BETWEEN": self._between,
        }
        if op in special:
            return special[op](left)
        if op in ("OR", "AND"):
            right = self.expr(bp)
            return Or(left, right) if op == "OR" else And(left, right)
        if op in ("+", "-", "*", "/"):
            return Arith(_arith_op(op), left, self.expr(bp))
        return Compare(_compare_op(op), left, self.expr(bp))

    def _is(self, left: Expr) -> Expr:
        negate = self.accept("NOT") is not None
        self.expect("NULL")
        return Not(IsNull(left)) if negate else IsNull(left)

    def _between(self, left: Expr) -> Expr:
        """Parse ``lo AND hi`` after ``left BETWEEN``; the ``AND`` belongs to ``BETWEEN``."""
        lo = self.expr(self.INFIX["AND"])  # stop in front of the AND
        self.expect("AND")
        hi = self.expr(self.INFIX["BETWEEN"])
        return And(Compare(">=", left, lo), Compare("<=", left, hi))
```

```python
>>> from minidb.sql import Parser
>>> Parser("SELECT * FROM t WHERE x BETWEEN 1 AND 2 + 3 AND y = 0").statement().where
(((x >= 1) AND (x <= (2 + 3))) AND (y = 0))
```

### A.2

The parser keeps the statement's text, and one method builds every error: the message, the line and column, the line itself, and a caret under the offending token. The end token is described in words.

```python
# src/minidb/sql.py (replace Parser.__init__)
    def __init__(self, sql: str, params: Sequence[Value | None] = ()) -> None:
        self.sql = sql
        self.tokens = tokenize(sql)
        self.i = 0
        self.params = list(params)
        self.used_params = 0
```

```python
# src/minidb/sql.py (add to Parser)
    def error(self, message: str, tok: Token) -> SQLError:
        r"""Build an error that shows where ``tok`` is: the line, with a caret under it.

        >>> Parser("SELECT name\nFROM users WHERE").statement()
        Traceback (most recent call last):
          ...
        minidb.sql.SQLError: unexpected end of input (line 2, column 17)
          FROM users WHERE
                          ^

        :param message: what is wrong.
        :param tok: the token where it went wrong.
        :return: the error, for the caller to raise.
        """
        start = self.sql.rfind("\n", 0, tok.pos) + 1
        end = self.sql.find("\n", tok.pos)
        line = self.sql[start : None if end == -1 else end]
        number = self.sql.count("\n", 0, tok.pos) + 1
        column = tok.pos - start
        return SQLError(f"{message} (line {number}, column {column + 1})\n  {line}\n  {' ' * column}^")
```

```python
# src/minidb/sql.py (replace Parser.expect)
    def expect(self, *values: str) -> Token:
        """Consume the current token, which must be one of these keywords or operators.

        :param values: the acceptable keywords and operators.
        :return: the token.
        :raises SQLError: if it is something else.
        """
        tok = self.accept(*values)
        if tok is None:
            got = self.peek()
            raise self.error(f"expected {' or '.join(values)}, got {_describe(got)}", got)
        return tok
```

```python
# src/minidb/sql.py (replace Parser.name)
    def name(self) -> str:
        """Consume a name.

        :return: the name.
        :raises SQLError: if the current token is not a name.
        """
        tok = self.next()
        if tok.kind != "name" or not isinstance(tok.value, str):
            raise self.error(f"expected a name, got {_describe(tok)}", tok)
        return tok.value
```

```python
# src/minidb/sql.py (replace Parser.primary)
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
        raise self.error(f"unexpected {_describe(tok)}", tok)
```

```python
# src/minidb/sql.py (append)
def _describe(tok: Token) -> str:
    """Name a token for an error message: ``end of input``, ``keyword FROM``, ``'text'``."""
    if tok.kind == "end":
        return "end of input"
    if tok.kind == "keyword":
        return f"keyword {tok.value}"
    return repr(tok.value)
```

```python
>>> from minidb.sql import Parser
>>> Parser("SELECT FROM users").statement()
Traceback (most recent call last):
  ...
minidb.sql.SQLError: unexpected keyword FROM (line 1, column 8)
  SELECT FROM users
         ^
```

The other messages (from `statement` and the tokenizer) can move to `error` the same way.

### A.3

`EXPLAIN` wraps a `SELECT`. The connection builds the same query it would run, and returns its plan instead, one row per line. Building the query moves into its own method, so that both paths share it.

```python
# src/minidb/sql.py (replace KEYWORDS)
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
        "EXPLAIN",
    }
)
```

```python
# src/minidb/sql.py (replace Statement)
type Statement = Select | Insert | Update | Delete | CreateTable | CreateIndex | TransactionControl | Explain


@dataclass
class Explain:
    """Hold a parsed ``EXPLAIN SELECT ...``."""

    select: Select
```

```python
# src/minidb/sql.py (replace Parser.statement)
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
            "EXPLAIN": self.explain,
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

    def explain(self) -> Explain:
        """Parse ``EXPLAIN`` followed by a ``SELECT``."""
        self.expect("EXPLAIN")
        return Explain(self.select())
```

```python
# src/minidb/sql.py (replace Connection._run)
    def _run(self, stmt: Select | Insert | Update | Delete | Explain, uow: UnitOfWork) -> Result:
        if isinstance(stmt, Insert):
            return self._insert(stmt, uow)
        if isinstance(stmt, Update):
            return self._update(stmt, uow)
        if isinstance(stmt, Delete):
            return uow.delete(stmt.table, stmt.where)
        if isinstance(stmt, Explain):
            return [{"plan": line} for line in self._query(stmt.select, uow).explain().splitlines()]
        return self._select(stmt, uow)
```

```python
# src/minidb/sql.py (replace Connection._select)
    def _select(self, s: Select, uow: UnitOfWork) -> list[dict[str, Value | None]]:
        return self._query(s, uow).all()

    @staticmethod
    def _query(s: Select, uow: UnitOfWork) -> Query:
        """Build the query for a ``SELECT``, without running it."""
        q = uow.query(*s.table)
        for name, alias, on, kind in s.joins:
            q = q.join(name, on, alias, kind)
        if s.where is not None:
            q = q.where(s.where)
        q = _with_ordering(_with_grouping(q, s), s)
        if s.items is not None:
            q = q.select(**_outputs(s.items))
        q = q.distinct() if s.distinct else q
        return q.limit(s.limit, s.offset) if s.limit is not None or s.offset else q
```

```python
>>> from minidb import Database
>>> from minidb.sql import connect
>>> conn = connect(Database())
>>> conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, age INTEGER)")
>>> conn.execute("CREATE INDEX by_age ON users (age) USING sorted")
>>> conn.execute("INSERT INTO users VALUES (1, 20), (2, 40), (3, 60)")
3
>>> for row in conn.execute("EXPLAIN SELECT id FROM users WHERE age > 30"):
...     print(row["plan"])
Project id
  IndexRange users AS users using by_age: 30 < age  [~1 rows]
```

### A.4

`Query.order_by` accepts `(key, descending)` pairs next to the string form, and the SQL layer passes a pair for any expression:

```python
# src/minidb/query.py (replace Query.order_by)
    def order_by(self, *keys: str | RowFunction | SortKey) -> Query:
        """Sort the result; ``"name"`` ascends, ``"-name"`` descends.

        >>> from minidb.database import Database
        >>> from minidb.schema import Column
        >>> from minidb.types import Integer
        >>> db = Database()
        >>> _ = db.create_table("t", [Column("a", Integer()), Column("b", Integer())])
        >>> for a, b in [(1, 5), (2, 1), (3, 3)]:
        ...     _ = db.insert("t", {"a": a, "b": b})
        >>> [r["t.a"] for r in db.query("t").order_by((lambda r: r["a"] - r["b"], True)).all()]
        [2, 3, 1]

        :param keys: column names, optionally prefixed with ``-``; functions
            of the row; or ``(name or function, descending)`` pairs. Most
            significant first.
        :return: the extended query.
        """
        parsed = tuple(_sort_key(k) for k in keys)
        return replace(self, ordering=(*self.ordering, *parsed))
```

```python
# src/minidb/query.py (append)
def _sort_key(key: str | RowFunction | SortKey) -> SortKey:
    """Turn one argument of :meth:`Query.order_by` into a ``(key, descending)`` pair."""
    if isinstance(key, tuple):
        return key
    if isinstance(key, str) and key.startswith("-"):
        return (key[1:], True)
    return (key, False)
```

```python
# src/minidb/sql.py (replace _sort_key)
def _sort_key(e: Expr, descending: bool) -> str | SortKey:  # noqa: FBT001 - a pair with e, from the parser
    """Turn an ORDER BY item into a key for :meth:`Query.order_by`."""
    if isinstance(e, Col | AggCall):  # by name: works in either direction
        return ("-" if descending else "") + (e.name if isinstance(e, Col) else e.key)
    return (e, descending)
```

```python
# src/minidb/sql.py (typing imports)
from minidb.operators import SortKey
```

```python
>>> from minidb import Database
>>> from minidb.sql import connect
>>> conn = connect(Database())
>>> conn.execute("CREATE TABLE t (a INTEGER, b INTEGER)")
>>> conn.execute("INSERT INTO t VALUES (1, 5), (2, 1), (3, 3)")
3
>>> conn.execute("SELECT a FROM t ORDER BY a - b DESC")
[{'a': 2}, {'a': 3}, {'a': 1}]
```

### A.5

Parse `CREATE TABLE name AS` followed by a `SELECT`, run the query, then create the table and insert the rows in one transaction. The interesting part is the types:

- An output that is a **plain column** gets that column's type, normalizers and nullability, but not its constraints: a copy of `users.email` isn't unique in a table of query results.
- An **aggregate** gets its result's type: `COUNT` is `Integer`, `SUM` the type of its column, `AVG` `Real` (or `Numeric` for a `Numeric` column, [Exercise 7.6](#76)).
- Any **other expression** has a type only if the system infers types for expressions. Without that, the choices are to infer one from the values produced (`Integer` if they are all ints, and so on), which makes the table's schema depend on its data and fails for an empty result, or to require an explicit list of types, as some systems do.

Every column should be nullable: a left join, or an aggregate of no rows, can produce NULLs where the source column couldn't. PostgreSQL derives types from its expression type system, and SQLite gives each column the "affinity" of its expression, often none at all.

### A.6

Running the subquery first and substituting its result as a constant list is correct for an *uncorrelated* subquery, one that doesn't mention the outer query's rows: it has one result, whichever outer row is being tested. It is wrong for a **correlated** subquery such as `WHERE o.total > (SELECT AVG(total) FROM orders WHERE user_id = u.id)`, whose result is different for every outer row: it must be evaluated per row (or decorrelated into a join or group-by by the planner). Two more traps, even for uncorrelated subqueries: if the subquery returns a NULL, `x NOT IN (…)` is never TRUE, which surprises people, and our `In` already gets right. And the subquery must run in the same transaction as the outer query, so that both see the same data.

### A.7

Tokenizing is pure: the same text always gives the same tokens, so the tokens can be cached by text. A real prepared statement caches the whole parsed (and planned) statement, with placeholders left unbound. Our parser binds `?` values *while parsing*, so its trees can't be shared between executions with different parameters. Caching the tokens is the part that works without changing the syntax tree:

```python
# src/minidb/sql.py (replace Parser.__init__)
    def __init__(self, sql: str, params: Sequence[Value | None] = ()) -> None:
        self.tokens = _cached_tokens(sql)
        self.i = 0
        self.params = list(params)
        self.used_params = 0
```

```python
# src/minidb/sql.py (append)
@functools.lru_cache(maxsize=256)
def _cached_tokens(sql: str) -> tuple[Token, ...]:
    """Tokenize ``sql``, remembering the result for the most recent texts; tokens are immutable."""
    return tuple(tokenize(sql))
```

```python
# src/minidb/sql.py (imports)
import functools
```

```python
# examples/statement_cache.py
"""Time repeated parameterized INSERTs, with the token cache and without it."""

import time

from minidb import Database
from minidb.sql import Parser
from minidb.sql import _cached_tokens
from minidb.sql import connect

N = 5_000
SQL = "INSERT INTO people (id, name, email, age) VALUES (?, ?, ?, ?)"


def run(*, cached: bool) -> tuple[float, float]:
    """Parse and execute ``N`` inserts.

    :param cached: whether to keep the token cache between statements.
    :return: seconds spent parsing, and seconds in total.
    """
    conn = connect(Database())
    conn.execute("CREATE TABLE people (id INTEGER PRIMARY KEY, name TEXT, email TEXT, age INTEGER)")
    parsing = 0.0
    t0 = time.perf_counter()
    for i in range(N):
        if not cached:
            _cached_tokens.cache_clear()
        params = (i, f"person {i}", f"p{i}@example.org", 20 + i % 50)
        p0 = time.perf_counter()
        Parser(SQL, params).statement()
        parsing += time.perf_counter() - p0
        if not cached:
            _cached_tokens.cache_clear()
        conn.execute(SQL, params)
    return parsing, time.perf_counter() - t0 - parsing  # the total is execute's time, which parses too


def main() -> None:
    """Print parse time and total time per insert, with and without the cache."""
    for cached in (False, True):
        parse, total = run(cached=cached)
        label = "cached" if cached else "uncached"
        print(f"{label:>9}: parse {parse / N * 1e6:5.1f} µs, total {total / N * 1e6:6.1f} µs per INSERT")


if __name__ == "__main__":
    main()
```

```text
 uncached: parse  32.4 µs, total   67.8 µs per INSERT
   cached: parse  10.8 µs, total   43.0 µs per INSERT
```

Tokenizing is two-thirds of parsing: the cache cuts parsing from 32 to 11 µs, and a whole `INSERT` from 68 to 43 µs, about 1.6 times faster. The rest of each statement is the parse proper and the transaction. Caching the syntax tree as well, with `?` kept as a placeholder node bound at execution, would remove most of the remaining parse time. Caching the *plan* is what makes prepared statements valuable in real systems, where planning a complex query can cost more than running it.

## Appendix B — Testing a Database

### B.1

Every committed row has a version: `row_versions` has exactly the rowids of `rows`. A row's version is the commit that last wrote it, and the table's `version` is the commit that last changed the table at all (including deletes, which leave no row version behind). And nothing can be newer than the database's last commit. So: `row_versions.keys() == rows.keys()` and `max(row_versions.values()) ≤ version ≤ commit_seq`.

```python
# tests/test_minidb.py (replace check_integrity)
def check_integrity(db: Database) -> None:
    """Raise AssertionError if any index, key, reference or version is inconsistent."""
    for t in db.tables.values():
        for index in t.indexes.values():
            _check_index(t, index)
        for row in t.rows.values():
            t.schema.prepare_row({}, base=row)  # re-runs NOT NULL and CHECKs
        _check_versions(db, t)
    for fk in db.foreign_keys:
        _check_references(db, fk)


def _check_versions(db: Database, t: Table) -> None:
    """Every row has a version, none newer than its table's, which is no newer than the last commit."""
    assert t.row_versions.keys() == t.rows.keys(), f"{t.name}: rows without versions, or versions without rows"
    assert all(v <= t.version for v in t.row_versions.values()), f"{t.name}: a row is newer than its table"
    assert t.version <= db.commit_seq, f"{t.name}: version {t.version} is past commit {db.commit_seq}"
```

```python
>>> import io, unittest
>>> suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_minidb")
>>> unittest.TextTestRunner(stream=io.StringIO()).run(suite).wasSuccessful()
True
```

### B.2

The model now holds users and orders, and implements the cascade itself: dropping a user drops that user's orders. An order for a user who doesn't exist is a `ForeignKeyError`.

```python
# tests/test_minidb.py (append)
class ShopModel:
    """Predict users and orders, with ON DELETE CASCADE from users to orders."""

    def __init__(self) -> None:
        self.users: set[int] = set()
        self.orders: dict[int, int] = {}  # order id -> user id

    def add_user(self, uid: int) -> type[Exception] | None:
        if uid in self.users:
            return UniqueError
        self.users.add(uid)
        return None

    def add_order(self, oid: int, uid: int) -> type[Exception] | None:
        if oid in self.orders:
            return UniqueError
        if uid not in self.users:
            return ForeignKeyError
        self.orders[oid] = uid
        return None

    def drop_user(self, uid: int) -> type[Exception] | None:
        self.users.discard(uid)
        self.orders = {o: u for o, u in self.orders.items() if u != uid}  # the cascade
        return None


def _shop_db() -> Database:
    db = Database()
    db.create_table("users", [Column("id", Integer())], primary_key="id")
    db.create_table(
        "orders",
        [Column("id", Integer()), Column("user_id", Integer())],
        primary_key="id",
        foreign_keys=[ForeignKey(("user_id",), "users", on_delete="cascade")],
    )
    return db


def _shop_step(
    db: Database, model: ShopModel, op: str, uid: int, oid: int
) -> tuple[type[Exception] | None, Callable[[], object]]:
    """Return the model's prediction for one operation, and the operation itself."""
    steps: dict[str, tuple[Callable[[], type[Exception] | None], Callable[[], object]]] = {
        "user": (lambda: model.add_user(uid), lambda: db.insert("users", {"id": uid})),
        "order": (lambda: model.add_order(oid, uid), lambda: db.insert("orders", {"id": oid, "user_id": uid})),
        "drop": (lambda: model.drop_user(uid), lambda: db.delete("users", {"id": uid})),
    }
    predict, action = steps[op]
    return predict(), action


class CascadeModelTest(unittest.TestCase):
    def test_random_operations_with_cascades(self) -> None:
        rnd = random.Random(5)  # noqa: S311 - test data
        db, model = _shop_db(), ShopModel()
        for step in range(1500):
            op = rnd.choice(["user", "user", "order", "order", "order", "drop"])
            expected, action = _shop_step(db, model, op, rnd.randrange(20), rnd.randrange(80))
            if expected is None:
                action()
            else:
                with expect(expected, f"at step {step}: {op}"):
                    action()
        assert {int(r["id"] or 0) for r in db.select("users")} == model.users
        assert {int(r["id"] or 0): int(r["user_id"] or 0) for r in db.select("orders")} == model.orders
        check_integrity(db)
```

```python
# tests/test_minidb.py (imports)
from minidb import ForeignKey
from minidb import ForeignKeyError
```

```python
# tests/test_minidb.py (replace typing imports)
from collections.abc import Callable
from collections.abc import Iterator

from minidb.index import Index
from minidb.table import Table
from minidb.values import Row
```

```python
>>> import io, unittest
>>> from tests.test_minidb import CascadeModelTest
>>> suite = unittest.defaultTestLoader.loadTestsFromTestCase(CascadeModelTest)
>>> unittest.TextTestRunner(stream=io.StringIO()).run(suite).wasSuccessful()
True
```

It is a weakness, but a manageable one. The model must reimplement the cascade, and if the model's author misunderstands the rule the same way as the implementation's author, both agree and the test passes. Here they are often the same person. The defence is to keep the model *obviously* correct, a one-line dict comprehension instead of a stack-based traversal, and to back it with invariants that don't depend on the model at all, such as `check_integrity`'s "no orphans". The model also needs only to be correct, not fast, so it can use the most naive algorithm.

### B.3

The two plans differ in everything that matters to the planner (access paths, join order and algorithm, where filters are applied) and must agree on the result, as a bag of rows. The test builds three joined tables with NULLs, indexes of all three kinds, and statistics, and compares 300 random queries:

```python
# tests/test_minidb.py (append)
_COLUMNS = {"a": ["a.id", "a.x", "a.y"], "b": ["b.id", "b.a_id", "b.z"], "c": ["c.id", "c.b_id", "c.w"]}
_OPS: tuple[CompareOp, ...] = ("=", "!=", "<", "<=", ">", ">=")


def _differential_db(rnd: random.Random) -> Database:
    """Create three chained tables with random data, NULLs, indexes of every kind, and statistics."""
    db = Database()
    for name, columns in _COLUMNS.items():
        db.create_table(name, [Column(c.partition(".")[2], Integer()) for c in columns], primary_key="id")
    with db.unit_of_work() as uow:
        for name, columns in _COLUMNS.items():
            for i in range(40):
                values = [rnd.choice([None, *range(10)]) for _ in columns[1:]]
                uow.insert(name, {"id": i} | dict(zip([c.partition(".")[2] for c in columns[1:]], values, strict=True)))
    db.create_index("a", "a_x", ["x"], kind="sorted")
    db.create_index("b", "b_a_id", ["a_id"])
    db.create_index("c", "c_w", ["w"], kind="btree")
    db.analyze()
    return db


def _random_condition(rnd: random.Random, names: list[str]) -> Expr:
    left = col(rnd.choice(names))
    right = col(rnd.choice(names)) if rnd.random() < 0.2 else lit(rnd.choice([None, *range(10)]))
    condition = Compare(rnd.choice(_OPS), left, right)
    return condition | _random_condition(rnd, names) if rnd.random() < 0.15 else condition


def _random_query(db: Database, rnd: random.Random) -> Query:
    tables = ["a", "b", "c"][: rnd.randint(1, 3)]
    q = db.query("a")
    if "b" in tables:
        q = q.join("b", col("a.id") == col("b.a_id"))
    if "c" in tables:
        q = q.join("c", col("b.id") == col("c.b_id"))
    names = [c for t in tables for c in _COLUMNS[t]]
    for _ in range(rnd.randint(0, 3)):
        q = q.where(_random_condition(rnd, names))
    return q


def _bag(rows: Iterable[Mapping[str, object]]) -> list[str]:
    return sorted(repr(sorted(r.items())) for r in rows)


class PlannerDifferentialTest(unittest.TestCase):
    def test_planned_equals_naive(self) -> None:
        rnd = random.Random(3)  # noqa: S311 - test data
        db = _differential_db(rnd)
        for _ in range(300):
            q = _random_query(db, rnd)
            with db.reading():
                naive = _bag(q.plan_naive())
            assert _bag(q.all()) == naive, q.explain()
```

```python
# tests/test_minidb.py (imports)
from minidb import Query
from minidb import col
from minidb import lit
from minidb.expr import Compare
```

```python
# tests/test_minidb.py (typing imports)
from collections.abc import Iterable
from collections.abc import Mapping

from minidb.expr import CompareOp
from minidb.expr import Expr
```

```python
>>> import io, unittest
>>> from tests.test_minidb import PlannerDifferentialTest
>>> suite = unittest.defaultTestLoader.loadTestsFromTestCase(PlannerDifferentialTest)
>>> unittest.TextTestRunner(stream=io.StringIO()).run(suite).wasSuccessful()
True
```

The assertion message is the plan, so a failure shows at once which access path or join produced the wrong rows. Shrinking a failing case (fewer conditions, fewer tables, fewer rows) is the next step, and what property-testing libraries such as Hypothesis do automatically.

### B.4

Without `- changing`, an update that leaves a row's own unique key unchanged finds the row itself in the index and is refused. `ModelBasedTest` catches it at step 21, the first update of an existing row: `update {'id': 17, 'email': 'u29@x', 'age': 78}` raises `UniqueError`, which the model doesn't expect. The concurrency test fails too, since every transfer updates rows with a primary key.

Three more mutations, applied one at a time to the Appendix B code, with the test suite run against each:

| Mutation | Caught by |
|---|---|
| `check_unique` without `- changing` | `ModelBasedTest` (step 21), `ConcurrencyTests` |
| `_split_leaf` doesn't link the new leaf (`right.next = None`) | `BTreeProperties`: range scans stop at the first split |
| `key_of` indexes keys with NULLs | **nothing** |
| `_frame_at` ignores the CRC | **nothing** |

The two survivors are the useful result: they show where the tests are blind. The model never inserts a NULL email, so NULL handling in unique indexes is never exercised. Adding `None` to the generated emails, and `UNIQUE` semantics for NULLs to the model, kills that mutant. The crash test only *truncates* the log, and a truncated frame is caught by its length before the CRC is ever consulted. The corruption test of [B.5](#b5) kills that mutant. Tools such as `mutmut` and `cosmic-ray` automate this: they generate thousands of mutants and report the ones that survive.

### B.5

```python
# tests/test_minidb.py (add to CrashTests)
    def test_corruption_in_the_middle(self) -> None:
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        states = _write_history(folder)
        path = Path(folder) / "wal.log"
        log = bytearray(path.read_bytes())
        log[len(log) // 2] ^= 0xFF  # flip every bit of one byte
        path.write_bytes(bytes(log))
        recovered = _open(folder)
        assert _ids(recovered) == states[recovered.commit_seq]  # a consistent prefix...
        assert recovered.commit_seq < len(states) - 1  # ...that silently lost the later commits
        assert (Path(folder) / "wal.log").stat().st_size < len(log)  # and the evidence is gone
        recovered.close()
```

```python
>>> import io, unittest
>>> from tests.test_minidb import CrashTests
>>> suite = unittest.defaultTestLoader.loadTestsFromTestCase(CrashTests)
>>> unittest.TextTestRunner(stream=io.StringIO()).run(suite).wasSuccessful()
True
```

What it does: the CRC check rejects the damaged frame, `read_log` treats it like a torn tail, recovers the commits before it, and **truncates the log** there. Every commit after the damaged byte, all acknowledged and durable, is silently thrown away, along with the evidence. What it should do: a torn write can only damage the *last* frame, so a bad frame followed by more data isn't a crash artifact but corruption (a bad disk, a bug, a stray write). Recovery should stop with an error that says where the damage is, and leave the file untouched for a human or a repair tool (or restore from a replica). A simple test distinguishes the two cases: if the bad frame's declared length runs past the end of the file, or it is the last frame, it is a torn tail; otherwise it is corruption. PostgreSQL and SQLite both refuse to start, or report corruption, rather than drop committed data quietly.

### B.6

The talk (Will Wilson, Strange Loop 2014) describes how FoundationDB runs the whole distributed database, network, disks and clocks included, in one single-threaded process. Every source of non-determinism goes through interfaces that a simulator controls with a seeded random number generator. Any failure can then be replayed exactly from its seed, and the simulator injects failures (lost packets, slow disks, crashes) far more often than reality would.

To do the same for minidb's threads:

- **Run threads one at a time.** Each simulated thread holds a private "turn" lock, and a scheduler releases one turn at a time, chosen by the seeded generator.
- **Make every blocking point a scheduling point.** The lock implementations are behind the `RWLock` protocol, so a `SimulatedRWLock` can, instead of blocking, mark the thread as waiting and hand control back to the scheduler. The same goes for the shared latch and for `Condition.wait_for`. Scheduling points can also be added at the places where interleavings matter: between planning and applying, and before validation.
- **Inject time and randomness.** `transaction()`'s back-off calls `time.sleep` and `random`. Passing a clock and a generator in (or patching them in tests) makes them simulated too: the simulated clock advances only when every thread is waiting.
- **Simulate the disk.** A `Storage` whose files live in memory can "crash" at any write, keeping a random prefix of the bytes not yet synced, which generalizes the truncation test.

A failing run then prints its seed, and running it again with that seed reproduces the exact interleaving, which is impossible with real threads. Simpler alternatives give part of the benefit: `sys.setswitchinterval` with tiny values shakes out races on GIL builds, and stress tests on the free-threaded build find more, but neither can replay what they found.

---

[🏠 Contents](index.md) · [Next: References →](references.md)
