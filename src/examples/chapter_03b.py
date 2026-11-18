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


def main() -> None:
    db = Database()
    _ = db.create_table("users", [
        Column("id", Integer(min=1)),
        Column("email", Text(max_length=254), normalizers=(strip, lower)),
        Column("name", Text(), normalizers=(nfc, collapse_spaces)),
        Column("age", Integer(min=0, max=150)),
        Column("balance", Numeric(10, 2)),
    ])

    print(db.insert("users", {
        "id": "1",
        "email": "  Ada@Example.ORG ",
        "name": " Ada   Lovelace",
        "age": 36.0,
        "balance": "12.5",
    }))

    print(db.get("users", 1))

    try:
        value = db.insert("users", {"id": 2, "age": -1})
    except DomainError as e:
        print(e)
    else:
        print(value)

    try:
        value = db.update("users", {"age": "thirty"})
    except DomainError as e:
        print(e)
    else:
        print(value)

    print(db.get("users", 1)["age"])  # the failed update changed nothing


if __name__ == '__main__':
    main()
    print("Done.")
