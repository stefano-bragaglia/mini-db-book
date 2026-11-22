# minidb

A small but real relational database in pure Python 3.14, with no dependencies beyond the standard library. It is
built one subsystem at a time in the accompanying book, [*Build Your Own Relational Database in
Python*](docs/minidb-book/index.md).

The code is meant to be read: each chapter adds a feature (or tears down a simplified version and rebuilds it
properly) and explains why the simple version wasn't enough.

## Status

The book is complete; the code in this repository follows it chapter by chapter and is currently at **Chapter 7**.

| Chapter | Topic                          | Code |
|--------:|--------------------------------|:----:|
|       1 | The relational model           |  ✅  |
|       2 | Tables and CRUD                |  ✅  |
|       3 | Types and normalization        |  ✅  |
|       4 | Constraints                    |  ✅  |
|       5 | Keys and indexes               |  ✅  |
|       6 | Referential integrity          |  ✅  |
|       7 | Query primitives               |  ✅  |
|    8–9 | Unit of Work (transactions)    |  ✅  |
|  10–12 | Concurrency and isolation      |  ✅  |
|      13 | Persistence                    |  ✅  |
|      14 | Query planning                 |  ✅  |
|      15 | B-trees                        |  ✅  |
|       A | SQL front end                  |  ✅  |

## Requirements

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)

```sh
git clone git@github.com:stefano-bragaglia/mini-db-book.git
cd mini-db-book
uv sync
```

## A taste

```python
from minidb import Column, Database, ForeignKey, Integer, Numeric, Text
from minidb.operators import Count, Sum

db = Database()
db.create_table("users", [Column("id", Integer()), Column("name", Text()), Column("city", Text())], primary_key="id")
db.create_table(
    "orders",
    [Column("id", Integer()), Column("user_id", Integer()), Column("total", Numeric(8, 2))],
    primary_key="id",
    foreign_keys=[ForeignKey("user_id", "users")],
)
db.insert("users", {"id": 1, "name": "Ada", "city": "London"})
db.insert("orders", {"id": 10, "user_id": 1, "total": "25.00"})
db.insert("orders", {"id": 11, "user_id": 1, "total": "15.50"})

report = (
    db.query("users", "u")
    .join("orders", on=lambda r: r["u.id"] == r["o.user_id"], alias="o")
    .where(lambda r: r["u.city"] == "London")
    .group_by("u.name", total=Sum("o.total"), n=Count())
)
print(report.all())  # [{'u.name': 'Ada', 'total': Decimal('40.50'), 'n': 2}]

db.insert("orders", {"id": 12, "user_id": 99, "total": "1.00"})  # raises ForeignKeyError
```

## Examples

Each chapter has a runnable script in [`examples/`](examples/) that reproduces its interactive sessions:

```sh
uv run python examples/chapter_07.py
```

`examples/index_speed.py` compares indexed and unindexed lookups, and `examples/toy.py` is the list-of-dicts
relational algebra toy from Chapter 1 (it is not part of minidb).

## Project layout

```
src/minidb/
  database.py    Database façade: tables, constraints, foreign keys
  table.py       Tables, rows and rowids
  schema.py      Columns, table schemas, CHECK and foreign-key definitions
  types.py       Column types: Integer, Text, Numeric, Date, ...
  normalizers.py Value normalizers applied on write
  values.py      Value and row type aliases
  index.py       Secondary indexes
  query.py       Fluent query builder
  operators.py   Query operators (scan, filter, join, sort, aggregate)
  errors.py      Error hierarchy
docs/minidb-book/  The book, one Markdown file per chapter
examples/          Runnable scripts, one per chapter
tests/             Tests
```

## The book

Start at the [index](docs/minidb-book/index.md) and read the chapters in order, since each builds on the previous
one's code. Every chapter ends with exercises, and [Appendix D](docs/minidb-book/appendix-d-answers.md) answers them.

## Development

The code is linted and formatted with [ruff](https://docs.astral.sh/ruff/) (all rules enabled) and uses PEP 695 generics
and protocols throughout.

```sh
uv run ruff check
uv run ruff format
```

## License

- **Code** (`src/`, `examples/`, `tests/`): [MIT License](LICENSE).
- **Book** (`docs/minidb-book/`): [Creative Commons Attribution 4.0](docs/minidb-book/LICENSE) (CC BY 4.0).

Copyright (c) 2026 Stefano Bragaglia.
