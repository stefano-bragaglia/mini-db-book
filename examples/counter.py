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
