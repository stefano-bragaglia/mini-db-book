from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import Integer
from minidb import TransactionError

if TYPE_CHECKING:
    from collections.abc import Callable


def execute(operation: Callable) -> object | None:
    try:
        value = operation()
    except (ConstraintError, TransactionError) as e:
        print(e)
    else:
        print(value)
        return value
    finally:
        print()


def main() -> None:
    db = Database()
    _ = db.create_table("t", [Column("id", Integer())], primary_key="id")
    _ = db.insert("t", {"id": 1})

    try:
        with db.unit_of_work(readonly=True) as uow:
            execute(lambda: uow.select("t"))
            execute(lambda: uow.insert("t", {"id": 2}))
    except  TransactionError as e:
        print(e)
    finally:
        print()

    try:
        with db.unit_of_work(readonly=True) as uow:
            uow.get("t", 1)["id"] = 99
    except  TransactionError as e:
        print(e)
    finally:
        print()

    execute(lambda: db.select("t"))


if __name__ == "__main__":
    main()
    print("Done.")
