import threading
from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import Integer
from minidb import TransactionError
from minidb import UniqueError

if TYPE_CHECKING:
    from collections.abc import Callable


def execute(operation: Callable) -> object | None:
    try:
        value = operation()
    except ConstraintError as e:
        print(e)
    else:
        print(value)
        return value
    finally:
        print()


def main() -> None:
    db = Database()
    _ = db.create_table("users", [Column("id", Integer())], primary_key="id")
    try:
        u1 = db.unit_of_work()
        u2 = db.unit_of_work()
    except TransactionError as e:
        print(e)
    else:
        execute(lambda: db.insert("users", {"id": 1}))  # also a nested unit of work
        execute(u1.rollback)
    finally:
        print()

    inside = threading.Event()

    results = []

    def first():
        with db.unit_of_work() as uow:
            uow.insert("users", {"id": 5})
            inside.set()  # let the second thread try
            threading.Event().wait(0.2)  # ...while we still hold the lock

    def second():
        inside.wait()
        try:
            db.insert("users", {"id": 5})
        except UniqueError as e:
            results.append("second: " + str(e))

    threads = [threading.Thread(target=first), threading.Thread(target=second)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(results)


if __name__ == "__main__":
    main()
    print("Done.")
