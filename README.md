<p align="center">
  <img src="https://raw.githubusercontent.com/stefano-bragaglia/mini-db-book/main/docs/minidb-book/mini-db.gif" alt="mini-db" width="480" height="270">
</p>

<h1 align="center">mini-db</h1>

<p align="center"><em>A little speaker making a very loud noise: small in size, big in decibels (dB), hence the name.</em></p>

<p align="center">
  <a href="https://pypi.org/project/mini-db/"><img src="https://img.shields.io/pypi/v/mini-db" alt="PyPI version"></a>
  <a href="https://pypi.org/project/mini-db/"><img src="https://img.shields.io/pypi/pyversions/mini-db" alt="Python versions"></a>
  <a href="https://github.com/stefano-bragaglia/mini-db-book/actions/workflows/ci.yml"><img src="https://github.com/stefano-bragaglia/mini-db-book/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/stefano-bragaglia/mini-db-book/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/mini-db" alt="License: MIT"></a>
  <a href="https://pypi.org/project/mini-db/"><img src="https://img.shields.io/pypi/dm/mini-db" alt="Downloads"></a>
  <a href="https://docs.astral.sh/ruff/"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://docs.astral.sh/uv/"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv"></a>
  <img src="https://img.shields.io/badge/typing-strict-blue" alt="Typed">
  <img src="https://img.shields.io/badge/dependencies-none-brightgreen" alt="No dependencies">
</p>

A small but real relational database in pure Python 3.14, with no dependencies beyond the standard library. It is
built one subsystem at a time in the accompanying book, [*Build Your Own Relational Database in
Python*](https://github.com/stefano-bragaglia/mini-db-book/blob/main/docs/minidb-book/index.md).

The code is meant to be read: each chapter adds a feature (or tears down a simplified version and rebuilds it
properly) and explains why the simple version wasn't enough.

## Status

The book is complete and the code follows it chapter by chapter, through all fifteen chapters and the appendices.

| Chapter | Topic                          |
|--------:|--------------------------------|
|       1 | The relational model           |
|       2 | Tables and CRUD                |
|       3 | Types and normalization        |
|       4 | Constraints                    |
|       5 | Keys and indexes               |
|       6 | Referential integrity          |
|       7 | Query primitives               |
|    8–9 | Unit of Work (transactions)    |
|  10–12 | Concurrency and isolation      |
|      13 | Persistence                    |
|      14 | Query planning                 |
|      15 | B-trees                        |
|       A | SQL front end                  |

## Installation

Requires Python 3.14 or later. The distribution is called `mini-db`; the package you import is `minidb`.

```sh
pip install mini-db
# or
uv add mini-db
```

To work on the code or follow the book, clone the repository and use [uv](https://docs.astral.sh/uv/):

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

[`examples/`](https://github.com/stefano-bragaglia/mini-db-book/tree/main/examples) holds runnable scripts that reproduce the book's sessions, for example:

```sh
uv run python examples/transfers.py
uv run python examples/index_speed.py
```

`examples/toy.py` is the list-of-dicts relational algebra toy from Chapter 1 (it is not part of minidb).

## Project layout

```
src/minidb/
  database.py    Database façade: tables, constraints, foreign keys
  table.py       Tables, rows and rowids
  schema.py      Columns, table schemas, CHECK and foreign-key definitions
  types.py       Column types: Integer, Text, Numeric, Date, ...
  normalizers.py Value normalizers applied on write
  values.py      Value and row type aliases
  changes.py     Planning of writes into validated changes
  index.py       Secondary indexes
  btree.py       B+ tree and the index built on it
  query.py       Fluent query builder
  expr.py        Expressions
  operators.py   Query operators (scan, filter, join, sort, aggregate)
  planner.py     Query planner
  uow.py         Unit of Work (transactions)
  locks.py       Readers-writer locks
  storage.py     Write-ahead log, snapshots, recovery
  sql.py         SQL front end
  errors.py      Error hierarchy
docs/minidb-book/  The book, one Markdown file per chapter
examples/          Runnable scripts
tests/             Tests
```

## The book

Start at the [index](https://github.com/stefano-bragaglia/mini-db-book/blob/main/docs/minidb-book/index.md) and read the chapters in order, since each builds on the previous
one's code. Every chapter ends with exercises, and [Appendix D](https://github.com/stefano-bragaglia/mini-db-book/blob/main/docs/minidb-book/appendix-d-answers.md) answers them.

## Development

The code is linted and formatted with [ruff](https://docs.astral.sh/ruff/) (all rules enabled) and uses PEP 695 generics
and protocols throughout.

```sh
uv run ruff check
uv run ruff format
uv run python -m examples.run_tests
```

## License

- **Code** (`src/`, `examples/`, `tests/`): [MIT License](https://github.com/stefano-bragaglia/mini-db-book/blob/main/LICENSE).
- **Book** (`docs/minidb-book/`): [Creative Commons Attribution 4.0](https://github.com/stefano-bragaglia/mini-db-book/blob/main/docs/minidb-book/LICENSE) (CC BY 4.0).

Copyright (c) 2026 Stefano Bragaglia.
