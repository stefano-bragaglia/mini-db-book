import threading
from typing import TYPE_CHECKING

from minidb import Boolean
from minidb import Column
from minidb import ConflictError
from minidb import ConstraintError
from minidb import Database
from minidb import Integer
from minidb import Text
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
    db.create_table("stock", [Column("sku", Text()), Column("qty", Integer(min=0))], primary_key="sku")
    db.insert("stock", {"sku": "TEA", "qty": 10})

    a_has_read, b_done, log = threading.Event(), threading.Event(), []

    def sale_a():
        uow = db.unit_of_work()
        item = uow.find("stock", {"sku": "TEA"})[0]  # reads qty = 10
        a_has_read.set()
        b_done.wait()
        item["qty"] -= 1
        try:
            uow.commit()
        except ConflictError as e:
            log.append(f"A: {e}")
            uow.rollback()

    def sale_b():
        a_has_read.wait()
        with db.unit_of_work() as uow:
            uow.find("stock", {"sku": "TEA"})[0]["qty"] -= 1
        log.append("B committed")
        b_done.set()

    threads = [threading.Thread(target=sale_a), threading.Thread(target=sale_b)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(log)
    execute(lambda: db.select("stock"))

    # -------------------------------------------------------------------------------------------------------------------
    db.create_table("doctors", [Column("name", Text()), Column("on_call", Boolean())], primary_key="name")
    db.insert("doctors", {"name": "Alice", "on_call": True})
    db.insert("doctors", {"name": "Bob", "on_call": True})

    def go_off_call(me, ready, go, log):
        uow = db.unit_of_work()
        on_call = uow.query("doctors").where(lambda r: r["on_call"]).all()
        ready.set()
        go.wait()
        if len(on_call) >= 2:
            uow.update("doctors", {"on_call": False}, where={"name": me})
        try:
            uow.commit()
            log.append(f"{me} went off call")
        except ConflictError:
            uow.rollback()
            log.append(f"{me}: conflict")

    ready_a, ready_b = threading.Event(), threading.Event()
    go_a, go_b, log = threading.Event(), threading.Event(), []
    t1 = threading.Thread(target=go_off_call, args=("Alice", ready_a, go_a, log))
    t2 = threading.Thread(target=go_off_call, args=("Bob", ready_b, go_b, log))
    t1.start()
    t2.start()
    ready_a.wait()
    ready_b.wait()  # both have counted 2 doctors on call
    go_a.set()
    t1.join()  # Alice commits first...
    go_b.set()
    t2.join()  # ...then Bob tries
    print(log)
    execute(lambda: [d["name"] for d in db.select("doctors", lambda r: r["on_call"])])

    # -------------------------------------------------------------------------------------------------------------------
    db.create_table("users", [Column("email", Text())], primary_key="email")
    u_ready, v_done, log = threading.Event(), threading.Event(), []

    def first():
        uow = db.unit_of_work()
        uow.insert("users", {"email": "ada@example.org"})  # lookup: no such key
        u_ready.set()
        v_done.wait()
        try:
            uow.commit()
        except ConflictError as e:
            log.append(str(e))
            uow.rollback()

    def second():
        u_ready.wait()
        db.insert("users", {"email": "ada@example.org"})
        v_done.set()

    threads = [threading.Thread(target=first), threading.Thread(target=second)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(log)
    execute(lambda: db.select("users"))


if __name__ == "__main__":
    main()
    print("Done.")
