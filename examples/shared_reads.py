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


class MutexAsRWLock(RWLockBase):
    """Behave like Chapter 10's lock: every acquisition is exclusive."""

    def __init__(self) -> None:
        self._mutex = threading.Lock()

    def acquire_read(self) -> None:
        """Take the mutex."""
        self._mutex.acquire()

    def acquire_write(self) -> None:
        """Take the mutex."""
        self._mutex.acquire()

    def release_read(self) -> None:
        """Release the mutex."""
        self._mutex.release()

    def release_write(self) -> None:
        """Release the mutex."""
        self._mutex.release()


def main() -> None:
    """Time both locks and print the speed-up."""
    shared = run(filled(Database()))
    exclusive = run(filled(Database(lock=MutexAsRWLock())))
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"GIL={gil}  exclusive: {exclusive:.2f}s   shared: {shared:.2f}s   speed-up: {exclusive / shared:.1f}x")


if __name__ == "__main__":
    main()
