from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import Integer
from minidb import SchemaError
from minidb import TransactionError
from minidb import col
from minidb.btree import BPlusTree

if TYPE_CHECKING:
    from collections.abc import Callable


def execute(operation: Callable) -> object | None:
    try:
        value = operation()
    except (ConstraintError, TransactionError, SchemaError) as e:
        print(e)
    else:
        print(value)
        return value
    finally:
        print()


def main() -> None:
    t = BPlusTree(order=4)
    for k in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        t.insert(k, k)
    print(t.dump())
    print(t.height, len(t))
    print([k for k, _ in t.items(35, 80, hi_inclusive=False)])
    t.insert(35, 35)
    print(t.dump())

    # -------------------------------------------------------------------------------------------------------------------
    db = Database()
    db.create_table("events", [Column("id", Integer()), Column("at", Integer())], primary_key="id")
    with db.unit_of_work() as uow:
        for i in range(5000):
            uow.insert("events", {"id": i, "at": (i * 7919) % 100_000})
    db.create_index("events", "by_time", ["at"], kind="btree")
    q = db.query("events").where((col("at") >= 1000) & (col("at") < 1500))
    print(q.explain())
    print(len(q.all()))


if __name__ == "__main__":
    main()
    print("Done.")
