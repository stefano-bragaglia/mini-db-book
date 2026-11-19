from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import ForeignKey
from minidb import Integer
from minidb import Text

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
    db.create_table(
        "users", [Column("id", Integer()), Column("name", Text()), Column("age", Integer(min=0))], primary_key="id"
    )

    execute(lambda: db.insert("users", {"id": 1, "name": "Ada", "age": 36}))
    uow = db.unit_of_work()
    execute(lambda: uow.insert("users", {"id": 2, "name": "Alan", "age": 41}))
    execute(lambda: [r["name"] for r in uow.query("users").order_by("name")])
    execute(lambda: [r["name"] for r in db.query("users")])
    execute(lambda: uow.insert("users", {"id": 1, "name": "Ada again"}))
    try:
        uow.commit()
    except ConstraintError as e:
        print(e)
    finally:
        print()
    execute(lambda: [r["name"] for r in db.query("users")])

    with db.unit_of_work() as uow:
        ada = execute(lambda: uow.find("users", {"name": "Ada"})[0])
        execute(lambda: ada is uow.get("users", ada.rowid))  # one object per row
        ada["age"] += 1  # just mutate it
        execute(lambda: uow.select("users", {"age": 37}))
    execute(lambda: db.select("users", {"id": 1}))

    try:
        with db.unit_of_work() as uow:
            alan = execute(lambda: uow.get("users", 2))
            alan["age"] = -5
            uow.commit()
    except ConstraintError as e:
        print(e)
    finally:
        print()
    execute(lambda: db.get("users", 2)["age"])

    with db.unit_of_work(deferred=True) as uow:
        execute(lambda: uow.update("users", {"id": 2}, where={"name": "Ada"}))  # temporarily two id=2!
        execute(lambda: uow.update("users", {"id": 1}, where={"name": "Alan"}))
    execute(lambda: sorted((r["name"], r["id"]) for r in db.select("users")))

    db.create_table(
        "employees",
        [Column("id", Integer()), Column("buddy", Integer())],
        primary_key="id",
        foreign_keys=[ForeignKey("buddy", "employees")],
    )
    execute(lambda: db.insert("employees", {"id": 1, "buddy": 2}))
    with db.unit_of_work(deferred=True) as uow:
        execute(lambda: uow.insert("employees", {"id": 1, "buddy": 2}))
        execute(lambda: uow.insert("employees", {"id": 2, "buddy": 1}))
    execute(lambda: len(db.select("employees")))

    try:
        with db.unit_of_work(deferred=True) as uow:
            execute(lambda: uow.delete("employees", {"id": 1}))  # 2 still names 1 as buddy
    except ConstraintError as e:
        print(e)
    finally:
        print()
    execute(lambda: len(db.select("employees")))


if __name__ == "__main__":
    main()
    print("Done.")
