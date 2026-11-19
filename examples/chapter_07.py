from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import ForeignKey
from minidb import Integer
from minidb import Numeric
from minidb import Text
from minidb.operators import Count
from minidb.operators import Sum

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
        "users", [Column("id", Integer()), Column("name", Text()), Column("city", Text())], primary_key="id"
    )
    _ = db.create_table(
        "orders",
        [Column("id", Integer()), Column("user_id", Integer()), Column("total", Numeric(8, 2))],
        primary_key="id",
        foreign_keys=[ForeignKey("user_id", "users")],
    )
    for row in [(1, "Ada", "London"), (2, "Alan", "London"), (3, "Grace", "New York"), (4, "Edgar", None)]:
        execute(lambda: db.insert("users", dict(zip(("id", "name", "city"), row))))
    for row in [(10, 1, "25.00"), (11, 2, "40.00"), (12, 1, "15.50"), (13, 3, "9.99")]:
        execute(lambda: db.insert("orders", dict(zip(("id", "user_id", "total"), row))))

    execute(lambda: db.query("users").where(lambda r: r["city"] == "London").select("name").all())
    execute(lambda: [r["name"] for r in db.query("users").order_by("city", "-name")])

    q = (
        db.query("users", "u")
        .join("orders", on=lambda r: r["u.id"] == r["o.user_id"], alias="o")
        .where(lambda r: r["u.city"] == "London")
        .group_by("u.name", total=Sum("o.total"), n=Count())
        .order_by("-total")
    )
    execute(q.all)
    execute(q.explain)

    execute(
        db.query("users", "u")
        .join("orders", on=lambda r: r["u.id"] == r["o.user_id"], alias="o", kind="left")
        .group_by("u.name", orders=Count("o.id"), spent=Sum("o.total"))
        .order_by("u.name")
        .select(name="u.name", orders="orders", spent="spent")
        .all
    )
    execute(db.query("orders").where(lambda r: False).group_by(n=Count(), s=Sum("total")).all)

    pulled = []

    def spy(r):
        pulled.append(r["id"])
        return True

    execute(db.query("orders").where(spy).limit(2).all)
    print(pulled)


if __name__ == "__main__":
    main()
    print("Done.")
