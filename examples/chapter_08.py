from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import ForeignKey
from minidb import Integer
from minidb import Text

if TYPE_CHECKING:
    from collections.abc import Callable


def execute(operation: Callable) -> None:
    try:
        value = operation()
    except ConstraintError as e:
        print(e)
    else:
        print(value)
    finally:
        print()


def main() -> None:
    db = Database()
    db.create_table("products", [Column("sku", Text()), Column("stock", Integer(min=0))], primary_key="sku")
    db.create_table("orders", [Column("id", Integer())], primary_key="id")
    db.create_table(
        "items",
        [Column("order_id", Integer()), Column("sku", Text()), Column("qty", Integer(min=1))],
        primary_key=("order_id", "sku"),
        foreign_keys=[ForeignKey("order_id", "orders", on_delete="cascade"), ForeignKey("sku", "products")],
    )

    execute(lambda: db.insert("products", {"sku": "TEA", "stock": 10}))
    with db.unit_of_work() as uow:
        execute(lambda: uow.insert("orders", {"id": 1}))
        execute(lambda: uow.insert("items", {"order_id": 1, "sku": "TEA", "qty": 3}))
        execute(lambda: uow.update("products", {"stock": 7}, where={"sku": "TEA"}))
    execute(lambda: db.select("products"))
    execute(lambda: len(db.select("items")))

    try:
        with db.unit_of_work() as uow:
            execute(lambda: uow.insert("orders", {"id": 2}))
            execute(lambda: uow.insert("items", {"order_id": 2, "sku": "TEA", "qty": 1}))
            execute(lambda: uow.insert("items", {"order_id": 2, "sku": "COFFEE", "qty": 1}))  # no such product
    except ConstraintError as e:
        print(e)
    finally:
        print(uow.state)
        print()
    execute(lambda: [r["id"] for r in db.select("orders")])  # order 2 was undone

    uow = db.unit_of_work()
    execute(lambda: uow.delete("orders", {"id": 1}))  # cascades to its item
    execute(lambda: uow.update("products", {"stock": -1}))  # violates min=0
    execute(uow.commit)
    execute(lambda: len(db.select("orders")))
    execute(lambda: len(db.select("items")))


if __name__ == "__main__":
    main()
    print("Done.")
