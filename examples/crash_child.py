# examples/crash_child.py
"""Make money transfers against a database on disk as fast as possible, forever.

``examples.crash_test`` starts this program and kills it at a random moment.
"""

import random
import sys

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Storage
from minidb import UnitOfWork

ACCOUNTS, START = 10, 1000


def open_db(folder: str) -> Database:
    """Declare the schema and attach the storage in ``folder``.

    :param folder: the database directory.
    :return: the database, with its saved data loaded.
    """
    db = Database()
    db.create_table("acct", [Column("id", Integer()), Column("bal", Integer(min=0))], primary_key="id")
    db.attach(Storage(folder))
    return db


def move(uow: UnitOfWork, a: int, b: int, amount: int) -> None:
    """Move ``amount`` from account ``a`` to account ``b``, if ``a`` has enough.

    :param uow: the transaction.
    :param a: the paying account.
    :param b: the receiving account.
    :param amount: the sum to move.
    """
    src, dst = uow.find("acct", {"id": a})[0], uow.find("acct", {"id": b})[0]
    if int(src["bal"] or 0) >= amount:
        src["bal"] = int(src["bal"] or 0) - amount
        dst["bal"] = int(dst["bal"] or 0) + amount


def main() -> None:
    """Fill the accounts if needed, say "ready", then transfer until killed."""
    if len(sys.argv) != 2:
        print("usage: python -m examples.crash_child FOLDER")
        return
    db = open_db(sys.argv[1])
    if not db.select("acct"):
        with db.unit_of_work() as uow:
            for i in range(ACCOUNTS):
                uow.insert("acct", {"id": i, "bal": START})
    print("ready", flush=True)
    rnd = random.Random()  # noqa: S311 - test data, not cryptography
    while True:
        a, b = rnd.sample(range(ACCOUNTS), 2)
        n = rnd.randint(1, 50)
        db.transaction(lambda uow, a=a, b=b, n=n: move(uow, a, b, n))


if __name__ == "__main__":
    main()
