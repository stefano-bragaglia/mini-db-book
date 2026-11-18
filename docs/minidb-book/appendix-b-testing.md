[🏠 Contents](index.md) · [← Previous: Appendix A — A SQL Front End](appendix-a-sql-parser.md)

# Appendix B — Testing a Database

Databases are hard to test. The bugs that matter only show up after a particular sequence of operations, under a particular thread interleaving, or after a crash at a particular byte. Example-based tests ("insert Ada, select Ada") are necessary but nowhere near sufficient. This appendix shows five kinds of test that work much better for systems like minidb, all written with the standard library's `unittest`. The tests use plain `assert` statements and a three-line `expect()` context manager rather than `self.assertEqual` and `self.assertRaises`: ruff's pytest-style rules prefer bare asserts, and they read better anyway.

| Kind | Idea | Finds |
|---|---|---|
| **Unit** | one function, known inputs and outputs | edge cases you thought of |
| **Invariant checking** | after anything, assert the structure is self-consistent | corruption, wherever it came from |
| **Property-based** | random operations on the real thing *and* a trivially correct model; compare | edge cases you didn't think of |
| **Concurrency** | many threads, then check invariants that must survive any interleaving | races, starvation |
| **Crash** | simulate a crash at *every* point, recover, check | durability and atomicity bugs |

The `>>>` sessions throughout the book are tests too. Every one was run against the code as it stood at the end of its chapter.

## B.1 An integrity checker

The most valuable test helper for a database is a function that checks **every invariant** the engine is supposed to maintain:

- each index contains exactly the rows it should, with no missing and no stale entries;
- unique indexes have at most one row per key;
- every row passes its schema's NOT NULL and CHECK constraints;
- every foreign key points at an existing parent.

Call it after every test, or every N steps of a randomized test. It doesn't care *how* the database got into a bad state, which is exactly why it catches bugs nobody anticipated.

## B.2 Property-based and model-based tests

Hypothesis is the best-known library for property-based testing in Python, but the core idea needs only `random`:

1. Generate a random sequence of operations, using a seeded `random.Random` so failures are reproducible.
2. Apply each operation to the system under test **and** to a *model*: the simplest thing that could possibly be correct (a `dict`, a sorted list).
3. Compare them, both on results and on errors.

Small key spaces matter. With ids drawn from 0–59, collisions, re-inserts after deletes and duplicate e-mails happen constantly. With ids from 0–10⁹ they would never happen, and the test would prove nothing.

The B-tree test is the classic shape: insert and remove random keys in both a `BPlusTree` and a `dict` of sets, then compare full contents and a range scan. Running it at order 3 (the smallest legal tree, which splits constantly) exercises every code path within a few thousand operations.

The model-based test of `Database` goes further. The model also predicts *which error* each operation should raise. That forces you to write down the semantics precisely: which comes first, a CHECK failure or a uniqueness failure? (In minidb the single-row pipeline runs first, as in [§5.4](05-keys-and-indexes.md#54-table-rewritten-around-put-and-remove).)

## B.3 Concurrency tests

Concurrency bugs depend on timing, so a single run proves little. The strategy is to make bugs *likely* and their effects *visible*:

- **Many threads, tight loops, contended data.** Five accounts and six threads conflict far more often than a thousand accounts would.
- **Check invariants that hold under any correct interleaving**: money is conserved, the integrity checker passes. Don't check exact outcomes, which depend on scheduling.
- **Run them on the free-threaded build** (`python3.14t`), where races that the GIL hides appear immediately ([§10.2](10-concurrency-i.md#102-breaking-minidb)).
- **Test liveness, not just safety.** The fairness test asserts an upper bound on how long a writer waits while readers stream. Against `ReaderPreferringLock` it fails, as it should.

For more systematic approaches, look at stress-testing tools like Jepsen for distributed databases, and at deterministic simulation testing, which runs everything in one thread under a scheduler you control.

## B.4 Crash tests

To test durability, crash at **every possible point**. Our log is the only file that changes between checkpoints, so "crashing after byte *k* of the log reached disk" is simulated by truncating a copy of the log to *k* bytes. For every cut point, recovery must produce exactly the state after some *prefix* of the commits: never a partial commit, never a commit that wasn't in the log.

The test records the database state after each commit, then checks that the recovered state equals the state at the recovered `commit_seq`. It covers torn frame headers, torn payloads and frames cut exactly at a boundary in one loop. The `SIGKILL` test in [§13.6](13-persistence.md#136-trying-it-out) complements it with real process death.

## B.5 The test module

```python
# tests/test_minidb.py
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

Run it from the project directory with `PYTHONPATH=src python3.14 -m unittest tests.test_minidb -v`, and again with `python3.14t`, or through `examples/run_tests.py`:

```python
# examples/run_tests.py
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

```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.340s

OK
```

The free-threaded build gives the same result (0.9 s).

## Exercises

1. Make the integrity checker also verify `Table.row_versions` and `Table.version` ([Chapter 12](12-isolation.md)). What invariant should hold between them and `Database.commit_seq`?
2. Extend the model-based test to foreign keys with `ON DELETE CASCADE`. Your model must implement the cascade too. Is that a weakness of model-based testing?
3. Write a model-based test for the *query planner*: generate random queries over random data, and compare `q.all()` with `q.plan_naive()`. This is called *differential testing*. It's how SQLite and other databases find optimizer bugs.
4. Break something on purpose: remove the `- changing` in `check_unique` ([§8.2](08-unit-of-work-i.md#82-the-planning-module)). Which test catches it? How many steps does it take? Try the same with three other deliberate bugs. This is *mutation testing*.
5. The crash test truncates the log, but never corrupts bytes *inside* it. Add a test that flips one random byte in the middle. What should recovery do? What does it do?
6. *(Research)* Read about deterministic simulation testing (FoundationDB's talk "Testing Distributed Systems w/ Deterministic Simulation" is a good start). How would you make minidb's thread scheduling deterministic for tests?

*Answers: [Appendix D, Appendix B](appendix-d-answers.md#appendix-b--testing-a-database).*

---

[🏠 Contents](index.md) · [Next: Appendix C — The Complete Code →](appendix-c-complete-code.md)
