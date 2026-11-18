"""
>>> from minidb import *
>>> from decimal import Decimal
>>>
>>>
>>>
1
>>>
{'sku': 'A-1', 'price': Decimal('9.99'), 'discount': None, 'qty': 0}
>>>
Traceback (most recent call last):
  ...
minidb.errors.CheckViolation: products.price: check failed for Decimal('0.00')
>>>
Traceback (most recent call last):
  ...
minidb.errors.NotNullViolation: products.qty may not be NULL
>>>
Traceback (most recent call last):
  ...
minidb.errors.CheckViolation: products: check 'discount_le_price' failed
>>>
1
>>>
Traceback (most recent call last):
  ...
minidb.errors.CheckViolation: products: check 'discount_le_price' failed
"""
from minidb import Check
from minidb import CheckViolation
from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import NotNullViolation
from minidb import Numeric
from minidb import Text


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

    print(db.insert("products", {"sku": "A-1", "price": "9.99"}))

    print(db.get("products", 1))

    try:
        value = db.insert("products", {"sku": "A-2", "price": 0})
    except CheckViolation as e:
        print(e)
    else:
        print(value)

    try:
        value = db.insert("products", {"sku": "A-3", "price": 5, "qty": None})
    except NotNullViolation as e:
        print(e)
    else:
        print(value)

    try:
        value = db.update("products", {"discount": 20})
    except CheckViolation as e:
        print(e)
    else:
        print(value)

    print(db.update("products", {"discount": "1.50"}))

    try:
        value = db.update("products", {"price": 1})  # now the *price* change violates the row check
    except CheckViolation as e:
        print(e)
    else:
        print(value)


if __name__ == '__main__':
    main()
    print("Done.")
