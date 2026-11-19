from typing import Callable

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import Integer
from minidb import Text
from minidb.normalizers import lower
from minidb.normalizers import strip


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

    _ = db.create_table("users", [
        Column("id", Integer()),
        Column("email", Text(), normalizers=(strip, lower)),
        Column("city", Text()),
    ], primary_key="id", unique=["email"])

    execute(lambda: db.insert("users", {"id": 1, "email": "ada@example.org", "city": "London"}))
    execute(lambda: db.insert("users", {"id": 2, "email": " ADA@example.org"}))
    execute(lambda: db.insert("users", {"email": "x@example.org"}))
    execute(lambda: db.insert("users", {"id": 2, "email": None}))  # NULLs never collide...
    execute(lambda: db.insert("users", {"id": 3, "email": None}))  # ...not even with each other
    execute(lambda: db.select("users", {"email": "  Ada@Example.org"}))

    users = db.table("users")
    execute(lambda: users.update_rows({2: {"id": 3}, 3: {"id": 2}}))  # swap ids of two rows
    execute(lambda: db.select("users"))
    execute(lambda: db.update("users", {"id": 1}, where={"id": 3}))  # one at a time collides

    _ = db.create_table("enrolments", [
        Column("student_id", Integer()), Column("course_id", Integer()),
        Column("grade", Text()),
    ], primary_key=("student_id", "course_id"))

    for s, c in [(1, 10), (1, 11), (2, 10)]:
        execute(lambda : db.insert("enrolments", {"student_id": s, "course_id": c}))
    execute(lambda: db.insert("enrolments", {"student_id": 1, "course_id": 10}))
    execute(lambda: db.create_index("enrolments", "by_course", ["course_id"]))
    execute(lambda: len(db.select("enrolments", {"course_id": 10})))

if __name__ == '__main__':
    main()
    print("Done.")
