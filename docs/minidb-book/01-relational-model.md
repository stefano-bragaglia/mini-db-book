[🏠 Contents](index.md)

# Chapter 1 — What a Relational Database Is

> *"Future users of large data banks must be protected from having to know how the data is organized in the machine."*
> — E. F. Codd, 1970

This book builds a small but real relational database, **minidb**, in pure Python 3.14 using only the standard library. By the last chapter it will have typed columns, constraints, indexes, foreign keys, composable query operators, transactions built on the *Unit of Work* pattern, a fair readers–writer lock, crash-safe persistence and a cost-based query planner. Appendix A adds a small SQL front end on top.

We build it the way real systems grow. We write the simplest thing that could work, run into its limits, then rewrite it. Several subsystems are rewritten twice. That is intentional: the *reasons* for each rewrite are most of what there is to learn.

## 1.1 The relational model in one page

In 1970 Edgar F. Codd proposed storing data as **relations** ([Codd 1970](references.md#codd1970)). Before that, programs navigated pointers between records. The idea was simple and radical: describe *what* data you want, not *how* to walk to it.

![Anatomy of a relation](images/01-relation-anatomy.svg)

The vocabulary, with the everyday SQL words in brackets:

| Term | Everyday name | Meaning |
|---|---|---|
| **Relation** | table | A named set of tuples that share a heading. |
| **Attribute** | column | A name paired with a domain. |
| **Domain** | type | The set of legal values for an attribute (e.g. "integers 0–150"). |
| **Tuple** | row | One value per attribute. |
| **Heading** | schema | The set of attributes. |
| **Key** | primary key / unique | A set of attributes whose values identify exactly one tuple. |
| **Foreign key** | reference | Attributes whose values must match a key in another relation. |

Two properties of the pure model surprise programmers:

1. **A relation is a *set*.** Its tuples have no order and no duplicates. SQL relaxes this (tables are *bags*, and `ORDER BY` exists), and so will we. But we will keep the idea that order is something you *ask for*, never something you can rely on.
2. **Tuples are values, not objects.** A tuple has no identity beyond its contents; you find it by its key. Internally we *will* give every row a hidden `rowid`, as SQLite does ([SQLite rowid tables](references.md#sqlite-rowid)), because it makes the machinery simpler. The user-visible identity is still the primary key.

### Relational algebra

Codd also defined a small algebra of operators that take relations and return relations. Every query is a composition of them:

| Operator | Symbol | SQL | Meaning |
|---|---|---|---|
| Selection | σ | `WHERE` | Keep the tuples satisfying a predicate. |
| Projection | π | `SELECT a, b` | Keep some attributes. |
| Join | ⋈ | `JOIN … ON` | Combine tuples from two relations that match. |
| Union, difference | ∪, − | `UNION`, `EXCEPT` | Set operations. |
| Rename | ρ | `AS` | Rename attributes or relations. |

Because each operator returns a relation, they **compose**. "Names of users older than 40" is π<sub>name</sub>(σ<sub>age>40</sub>(users)). That composability is the backbone of [Chapter 7](07-query-primitives.md), and the freedom to *reorder* those compositions is the whole of [Chapter 14](14-query-planning.md).

### Integrity

A database is more than storage. It **refuses bad data**. Codd's model comes with integrity rules: entity integrity (keys are never NULL), referential integrity (foreign keys point at something real) and domain integrity (values belong to their type). Chapters [3](03-types-and-normalization.md) to [6](06-referential-integrity.md) implement all three.

### Transactions and ACID

Finally, changes happen in **transactions** with four guarantees, named ACID by Härder and Reuter ([Härder & Reuter 1983](references.md#harder1983)):

- **Atomicity** — all of a transaction's changes happen, or none do.
- **Consistency** — every committed state satisfies all constraints.
- **Isolation** — concurrent transactions don't see each other's half-finished work.
- **Durability** — once committed, changes survive a crash.

Atomicity and consistency arrive with the Unit of Work ([Chapters 8](08-unit-of-work-i.md)–[9](09-unit-of-work-ii.md)). Isolation needs locks and validation ([Chapters 10](10-concurrency-i.md)–[12](12-isolation.md)). Durability needs a log on disk ([Chapter 13](13-persistence.md)).

## 1.2 A database in forty lines

Before any architecture, let's see how far a list of dicts gets us. This toy isn't part of minidb. We write it once to feel the problems. It lives in `examples/toy.py`. Even a toy follows the house style of this book: type hints everywhere, and a reStructuredText docstring with a runnable example for every function. §1.4 explains the conventions.

```python
# examples/toy.py
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

It works:

```python
>>> from examples.toy import ORDERS, USERS, join, project, select
>>> project(select(USERS, lambda u: u["age"] is not None and u["age"] > 40), "name")
[{'name': 'Alan'}]
>>> for row in join(USERS, ORDERS, lambda u, o: u["id"] == o["user_id"]):
...     print(row["name"], row["total"])
Ada 25
Ada 15
Alan 40
```

The output order follows the nested loops (all of Ada's orders come first), not the order of `ORDERS`. That is one more reason never to rely on row order you didn't ask for.

…and it is wrong in at least eight ways. Each one is a chapter:

| Problem with the toy | Where we fix it |
|---|---|
| Nothing stops `{"id": "one", "age": -5}` | [Ch. 3](03-types-and-normalization.md) types, [Ch. 4](04-constraints.md) constraints |
| Two users can share `id` 1 | [Ch. 5](05-keys-and-indexes.md) keys |
| Finding user 1 scans the whole list | [Ch. 5](05-keys-and-indexes.md) indexes |
| An order can point at user 99, who doesn't exist | [Ch. 6](06-referential-integrity.md) foreign keys |
| `join` compares every pair: O(n·m) | [Ch. 7](07-query-primitives.md), [Ch. 14](14-query-planning.md) |
| A failed batch of changes leaves half of them applied | [Ch. 8](08-unit-of-work-i.md)–[9](09-unit-of-work-ii.md) Unit of Work |
| Two threads appending at once corrupt the list | [Ch. 10](10-concurrency-i.md)–[12](12-isolation.md) concurrency |
| Everything vanishes when the process exits | [Ch. 13](13-persistence.md) persistence |

Notice also the `u["age"] is not None` guard in the first query. Without it, `None > 40` raises `TypeError`. Missing values (SQL's `NULL`) will need careful, consistent rules. We meet them in [Chapter 4](04-constraints.md#42-three-valued-logic).

## 1.3 The architecture we are heading for

Here is minidb as it will look by the end of the book. Each box is a module; arrows mean "calls".

```mermaid
flowchart TD
    SQL["sql.py<br/>(Appendix A)"] --> Q
    APP[Your application] --> DB
    APP --> Q
    DB["database.py<br/>Database: CRUD façade"] --> UOW
    Q["query.py / planner.py<br/>Query builder, planner"] --> OPS["operators<br/>scan, filter, join, sort…"]
    UOW["uow.py<br/>Unit of Work"] --> CH["changes.py<br/>plan & validate changes"]
    UOW --> LOCK["locks.py<br/>fair RW lock"]
    UOW --> ST["storage.py<br/>snapshot + log, pluggable format"]
    CH --> T["table.py<br/>rows + indexes"]
    CH --> S["schema.py / types.py<br/>columns, types, checks"]
    OPS --> T
    T --> IDX["index.py / btree.py"]
```

> **Rendering diagrams.** Diagrams written as `mermaid` blocks render on GitHub, GitLab, in VS Code's Markdown preview and in most modern Markdown tools. Static pictures are SVG files in `images/`.

## 1.4 How to read the code in this book

All code targets **Python 3.14** and uses only the standard library. It uses 3.14 features such as deferred evaluation of annotations, so it won't run on older versions.

### Project layout

The project uses the standard `src` layout: the package lives in `src/minidb/`, small runnable programs in `examples/`, and the test suite in `tests/`.

```text
minidb-project/
├── pyproject.toml
├── examples/
│   ├── __init__.py
│   └── toy.py
├── src/
│   └── minidb/
│       └── __init__.py
└── tests/
    └── __init__.py
```

Run things from the project directory with `src` on the import path, for example `PYTHONPATH=src python3.14 -m examples.toy`.

### Where each snippet goes

Every snippet that belongs to a file starts with a comment saying **where it goes**:

| First line of the snippet | Meaning |
|---|---|
| `# src/minidb/table.py` | This is the *whole* file. Create it or overwrite it. |
| `# src/minidb/table.py (replace Table.insert)` | Replace just that method, or a top-level function, class or type alias. |
| `# src/minidb/table.py (add to Table)` | Add these methods to the class. |
| `# src/minidb/table.py (append)` | Add this code at the end of the file. |
| `# src/minidb/table.py (imports)` | Add these imports to the file's imports. |
| `# src/minidb/table.py (typing imports)` | Add these imports inside the file's `if TYPE_CHECKING:` block, creating it if needed. |
| `# src/minidb/table.py (replace typing imports)` | Replace the whole `if TYPE_CHECKING:` block with these imports. |

Snippets that start with `>>>` are interactive sessions. Start Python in the project directory with `PYTHONPATH=src` and type them in. Snippets with no header are illustrations, not part of any file.

### Code style and checks

The code is held to a strict standard, the kind you'd want in a real project, and the same configuration works for your own copy. `pyproject.toml` configures two tools:

- **[ruff](https://docs.astral.sh/ruff/)**, a linter and formatter, with *every* rule enabled (`select = ["ALL"]`) apart from a short list of exceptions. Two of its rules shape the code more than any other: functions must keep a cyclomatic complexity of at most 5, so the code is split into many small, named steps, and imports used only in annotations go in an `if TYPE_CHECKING:` block.
- **[pyrefly](https://pyrefly.org/)**, a type checker, in its `strict` preset. Everything is typed, including every `__dunder__` method's parameters and return value.

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

**Docstrings** are reStructuredText. Each opens with a one-line summary in the imperative ("Return the row…", not "Returns the row…"). A further paragraph explains anything unusual. Where it helps, a doctest shows how to use the code, and fields list the parameters (including whether they may be `None` and their defaults), the return value and the exceptions raised:

```text
:param where: rows to match; ``None`` (the default) matches every row.
:return: the matching rowids.
:raises SchemaError: if ``where`` names an unknown column.
```

There are no `:type:` or `:rtype:` fields, since the signature already carries the types. Dunder methods have no docstrings, and small private helpers whose code explains itself don't either.

**Every listing has been checked.** The listings were assembled into a package chapter by chapter. At the end of every chapter, that package passed `ruff format`, `ruff check` and `pyrefly check`, all its docstring doctests, and every `>>>` session in the chapter. [Appendix C](appendix-c-complete-code.md) has the complete final code in one place, and [Appendix D](appendix-d-answers.md) answers every question and exercise.

## 1.5 Further reading

- Codd's original paper ([Codd 1970](references.md#codd1970)) is short and readable. Section 1 alone explains why the relational model won.
- *Architecture of a Database System* ([Hellerstein, Stonebraker & Hamilton 2007](references.md#hellerstein2007)) is a free tour of how real systems are organized. Skim it now and reread it at the end of the book.
- For a full textbook treatment, see [Ramakrishnan & Gehrke](references.md#ramakrishnan2003) or [Silberschatz, Korth & Sudarshan](references.md#silberschatz2019).

## Questions and exercises

1. **Sets vs bags.** `project` removes duplicates. Give a query where keeping duplicates changes the *meaning* of the answer, not just its length. (Hint: think of `SUM`.)
2. Why does the toy `join` merge dicts with `lrow | rrow`? What goes wrong if both relations have an attribute called `id`? Propose a fix. ([Chapter 7](07-query-primitives.md) has ours.)
3. Write `union(r, s)` and `difference(r, s)` for the toy. What must be true of `r` and `s` for them to make sense? (Codd calls this *union compatibility*.)
4. The toy uses Python lambdas as predicates. List one advantage and one disadvantage of that choice. Keep your answer; we revisit it in [Chapter 14](14-query-planning.md).
5. Which ACID property does each of these violate?
   a) A power cut after a bank transfer was confirmed loses the transfer.
   b) A report shows money that has left one account but not yet arrived in the other.
   c) An order is saved with `quantity = -3`.
6. *(Research)* Read the first two pages of [Codd 1970](references.md#codd1970). What are the three kinds of "data dependence" he wants to remove?

*Answers: [Appendix D, Chapter 1](appendix-d-answers.md#chapter-1--what-a-relational-database-is).*

---

[🏠 Contents](index.md) · [Next: Chapter 2 — Tables and CRUD →](02-tables-and-crud.md)
