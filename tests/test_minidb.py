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
