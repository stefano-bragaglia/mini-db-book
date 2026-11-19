# examples/transfers.py
"""Move money between accounts from many threads, and check none is lost.

An auditor thread keeps summing all balances while the transfers run; it
must always see the same total.
"""

import random
import sys
import threading

from minidb import Column
from minidb import Database
from minidb import DomainError
from minidb import Integer
from minidb import Sum

ACCOUNTS, START = 10, 1000


def gil_enabled() -> bool:
    """Return whether this interpreter runs with the GIL."""
    check = getattr(sys, "_is_gil_enabled", None)
    return bool(check()) if callable(check) else True


def transfer(db: Database, seed: int) -> None:
    """Make 500 random transfers, skipping those that would overdraw.

    :param db: the database.
    :param seed: the seed for this thread's random choices.
    """
    rnd = random.Random(seed)  # noqa: S311 - test data, not cryptography
    for _ in range(500):
        a, b = rnd.sample(range(ACCOUNTS), 2)
        amount = rnd.randint(1, 100)
        try:
            with db.unit_of_work() as uow:
                src, dst = uow.find("accounts", {"id": a})[0], uow.find("accounts", {"id": b})[0]
                src["balance"] = int(src["balance"] or 0) - amount  # DomainError below zero
                dst["balance"] = int(dst["balance"] or 0) + amount
        except DomainError:
            pass


def audit(db: Database, stop: threading.Event, problems: list[object]) -> None:
    """Sum the balances until ``stop`` is set, recording any wrong total.

    :param db: the database.
    :param stop: set when the transfers have finished.
    :param problems: where to record wrong totals.
    """
    while not stop.is_set():
        result = db.query("accounts").group_by(total=Sum("balance")).first()
        if result is None or result["total"] != ACCOUNTS * START:
            problems.append(result)


def main() -> None:
    """Run eight transfer threads and one auditor, then check the final total."""
    db = Database()
    db.create_table("accounts", [Column("id", Integer()), Column("balance", Integer(min=0))], primary_key="id")
    for i in range(ACCOUNTS):
        db.insert("accounts", {"id": i, "balance": START})
    stop, problems = threading.Event(), list[object]()
    workers = [threading.Thread(target=transfer, args=(db, s)) for s in range(8)]
    auditor = threading.Thread(target=audit, args=(db, stop, problems))
    auditor.start()
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    stop.set()
    auditor.join()
    final = sum(int(r["balance"] or 0) for r in db.select("accounts"))
    print(f"GIL={gil_enabled()} final total={final} audit problems={len(problems)}")
    assert final == ACCOUNTS * START
    assert not problems


if __name__ == "__main__":
    main()
