from typing import Callable

from minidb import Column
from minidb import Database
from minidb import DomainError
from minidb import Integer
from minidb import Numeric
from minidb import Text
from minidb.normalizers import collapse_spaces
from minidb.normalizers import lower
from minidb.normalizers import nfc
from minidb.normalizers import strip


def execute(operation: Callable) -> None:
    try:
        value = operation()
    except DomainError as e:
        print(e)
    else:
        print(value)
    finally:
        print()


def main() -> None:
    db = Database()
    _ = db.create_table("users", [
        Column("id", Integer(min=1)),
        Column("email", Text(max_length=254), normalizers=(strip, lower)),
        Column("name", Text(), normalizers=(nfc, collapse_spaces)),
        Column("age", Integer(min=0, max=150)),
        Column("balance", Numeric(10, 2)),
    ])

    execute(lambda: db.insert("users", {
        "id": "1",
        "email": "  Ada@Example.ORG ",
        "name": " Ada   Lovelace",
        "age": 36.0,
        "balance": "12.5",
    }))
    execute(lambda: db.get("users", 1))
    execute(lambda: db.insert("users", {"id": 2, "age": -1}))
    execute(lambda: db.update("users", {"age": "thirty"}))
    execute(lambda: db.get("users", 1)["age"])  # the failed update changed nothing


if __name__ == '__main__':
    main()
    print("Done.")
