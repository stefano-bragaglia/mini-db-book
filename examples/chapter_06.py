from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import ForeignKey
from minidb import Integer
from minidb import Numeric
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
    _ = db.create_table(
        "users",
        [
            Column("id", Integer()),
            Column("name", Text()),
            Column("referred_by", Integer()),
        ],
        primary_key="id",
        foreign_keys=[ForeignKey("referred_by", "users", on_delete="set null")],
    )
    _ = db.create_table("products", [Column("sku", Text()), Column("price", Numeric(8, 2))], primary_key="sku")
    _ = db.create_table(
        "orders",
        [Column("id", Integer()), Column("user_id", Integer())],
        primary_key="id",
        foreign_keys=[ForeignKey("user_id", "users", on_delete="cascade")],
    )
    _ = db.create_table(
        "order_items",
        [
            Column("order_id", Integer()),
            Column("sku", Text()),
            Column("qty", Integer(min=1)),
        ],
        primary_key=("order_id", "sku"),
        foreign_keys=[
            ForeignKey("order_id", "orders", on_delete="cascade"),
            ForeignKey("sku", "products"),  # restrict
        ],
    )

    execute(lambda: db.insert("users", {"id": 1, "name": "Ada"}))
    execute(lambda: db.insert("users", {"id": 2, "name": "Alan", "referred_by": 1}))
    execute(lambda: db.insert("products", {"sku": "TEA", "price": "3.50"}))
    execute(lambda: db.insert("orders", {"id": 100, "user_id": 1}))
    execute(lambda: db.insert("order_items", {"order_id": 100, "sku": "TEA", "qty": 2}))
    execute(lambda: db.insert("orders", {"id": 101, "user_id": 99}))
    execute(lambda: db.delete("products", {"sku": "TEA"}))
    execute(lambda: db.update("users", {"id": 10}, where={"id": 1}))

    execute(lambda: db.delete("users", {"id": 1}))
    execute(lambda: db.select("orders"))
    execute(lambda: db.select("order_items"))
    execute(lambda: db.select("users"))

    execute(lambda: db.insert("orders", {"id": 200, "user_id": 2}))
    execute(lambda: db.insert("order_items", {"order_id": 200, "sku": "TEA", "qty": 1}))
    execute(lambda: db.delete("products", {"sku": "TEA"}))
    execute(lambda: len(db.select("orders")))
    execute(lambda: len(db.select("order_items")))


if __name__ == "__main__":
    main()
    print("Done.")
