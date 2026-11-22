from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import ForeignKey
from minidb import Integer
from minidb import SchemaError
from minidb import Text
from minidb import TransactionError
from minidb import col

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
    db = Database()
    db.create_table(
        "users",
        [Column("id", Integer()), Column("name", Text()), Column("city", Text()), Column("age", Integer())],
        primary_key="id",
    )
    db.create_table(
        "orders",
        [Column("id", Integer()), Column("user_id", Integer()), Column("total", Integer())],
        primary_key="id",
        foreign_keys=[ForeignKey("user_id", "users")],
    )
    cities = ["Paris", "London", "Rome", "Oslo", "Lima", "Pune", "Kyiv", "Cairo", "Quito", "Perth"]
    with db.unit_of_work() as uow:
        for i in range(1000):
            uow.insert("users", {"id": i, "name": f"user{i}", "city": cities[i % 10], "age": 18 + (i * 7) % 60})
        for i in range(10_000):
            uow.insert("orders", {"id": i, "user_id": (i * 13) % 1000, "total": i % 100})
    db.create_index("users", "by_age", ["age"], kind="sorted")
    db.analyze()

    # ------------------------------------------------------------------------------------------------------------------
    print(db.query("users").where(col("id") == 42).explain())
    print(db.query("users").where(lambda r: r["id"] == 42).explain())

    # ------------------------------------------------------------------------------------------------------------------
    q = db.query("users").where((col("age") >= 60) & (col("city") == "Paris"))
    print(q.explain())
    print(len(q.all()))

    # ------------------------------------------------------------------------------------------------------------------
    q = (
        db.query("users", "u")
        .join("orders", on=col("u.id") == col("o.user_id"), alias="o")
        .where((col("u.city") == "Paris") & (col("u.age") >= 30))
    )
    print(q.plan_naive().explain())
    print(q.explain())
    print(len(q.all()) == len([r for r in q.plan_naive()]))


if __name__ == "__main__":
    main()
    print("Done.")
