"""Time the same join with Chapter 7's naive plan and with the planner's plan."""

import time

from minidb import Column
from minidb import Database
from minidb import ForeignKey
from minidb import Integer
from minidb import Text
from minidb import col

CITIES = ["Paris", "London", "Rome", "Oslo", "Lima", "Pune", "Kyiv", "Cairo", "Quito", "Perth"]


def build() -> Database:
    """Create 1,000 users and 10,000 orders, with an age index and statistics.

    :return: the filled database.
    """
    db = Database()
    db.create_table(
        "users", [Column("id", Integer()), Column("city", Text()), Column("age", Integer())], primary_key="id"
    )
    db.create_table(
        "orders",
        [Column("id", Integer()), Column("user_id", Integer())],
        primary_key="id",
        foreign_keys=[ForeignKey(("user_id",), "users")],
    )
    with db.unit_of_work() as uow:
        for i in range(1000):
            uow.insert("users", {"id": i, "city": CITIES[i % 10], "age": 18 + (i * 7) % 60})
        for i in range(10_000):
            uow.insert("orders", {"id": i, "user_id": (i * 13) % 1000})
    db.create_index("users", "by_age", ["age"], kind="sorted")
    db.analyze()
    return db


def main() -> None:
    """Run both plans, check they agree, and print the times."""
    db = build()
    q = (
        db.query("users", "u")
        .join("orders", on=col("u.id") == col("o.user_id"), alias="o")
        .where((col("u.city") == "Paris") & (col("u.age") >= 30))
    )
    with db.reading():
        t0 = time.perf_counter()
        naive = list(q.plan_naive())
        t1 = time.perf_counter()
        planned = list(q.plan())
        t2 = time.perf_counter()
    assert len(naive) == len(planned)
    print(
        f"{len(planned)} rows | naive: {t1 - t0:.2f} s | planned: {(t2 - t1) * 1000:.1f} ms | {(t1 - t0) / (t2 - t1):,.0f}x faster"
    )


if __name__ == "__main__":
    main()
