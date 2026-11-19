from typing import Callable

from minidb import Check
from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Numeric
from minidb import Text


def execute(operation: Callable) -> None:
    try:
        value = operation()
    except Exception as e:
        print(e)
    else:
        print(value)
    finally:
        print()


def main() -> None:
    db = Database()
    _ = db.create_table("products", [
        Column("sku", Text(), nullable=False),
        Column("price", Numeric(8, 2), nullable=False, check=lambda p: p > 0),
        Column("discount", Numeric(8, 2)),
        Column("qty", Integer(min=0), nullable=False, default=0),
    ], checks=[
        Check("discount_le_price",
              lambda r: None if r["discount"] is None else r["discount"] <= r["price"]),
    ])

    execute(lambda: db.insert("products", {"sku": "A-1", "price": "9.99"}))
    execute(lambda: db.get("products", 1))
    execute(lambda: db.insert("products", {"sku": "A-2", "price": 0}))
    execute(lambda: db.insert("products", {"sku": "A-3", "price": 5, "qty": None}))
    execute(lambda: db.update("products", {"discount": 20}))
    execute(lambda: db.update("products", {"discount": "1.50"}))
    execute(lambda: db.update("products", {"price": 1}))  # now the *price* change violates the row check


if __name__ == '__main__':
    main()
    print("Done.")
