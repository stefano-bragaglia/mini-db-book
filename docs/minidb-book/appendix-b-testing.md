[🏠 Contents](index.md) · [← Previous: Appendix A — A SQL Front End](appendix-a-sql-parser.md)

# Appendix B — Testing a Database

Databases are hard to test. The bugs that matter only show up after a particular sequence of operations, under a particular thread interleaving, or after a crash at a particular byte. Example-based tests ("insert Ada, select Ada") are necessary but nowhere near sufficient. This appendix shows five kinds of test that work much better for systems like minidb, all written with the standard library's `unittest`:

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

Run it from the project directory with `python3.14 -m unittest tests.test_minidb -v`, and again with `python3.14t`:

```python
# run
import sys, unittest
suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_minidb")
result = unittest.TextTestRunner(verbosity=1).run(suite)
assert result.wasSuccessful()
```

```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.565s

OK
```

The free-threaded build gives the same result (0.7 s).

## Exercises

1. Make the integrity checker also verify `Table.row_versions` and `Table.version` ([Chapter 12](12-isolation.md)). What invariant should hold between them and `Database.commit_seq`?
2. Extend the model-based test to foreign keys with `ON DELETE CASCADE`. Your model must implement the cascade too. Is that a weakness of model-based testing?
3. Write a model-based test for the *query planner*: generate random queries over random data, and compare `q.all()` with `q.plan_naive()`. This is called *differential testing*. It's how SQLite and other databases find optimizer bugs.
4. Break something on purpose: remove the `- changing` in `check_unique` ([§8.2](08-unit-of-work-i.md#82-the-planning-module)). Which test catches it? How many steps does it take? Try the same with three other deliberate bugs. This is *mutation testing*.
5. The crash test truncates the log, but never corrupts bytes *inside* it. Add a test that flips one random byte in the middle. What should recovery do? What does it do?
6. *(Research)* Read about deterministic simulation testing (FoundationDB's talk "Testing Distributed Systems w/ Deterministic Simulation" is a good start). How would you make minidb's thread scheduling deterministic for tests?

---

[🏠 Contents](index.md) · [Next: Appendix C — The Complete Code →](appendix-c-complete-code.md)
