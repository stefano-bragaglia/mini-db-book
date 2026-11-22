import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from minidb import Column
from minidb import ConstraintError
from minidb import Database
from minidb import Date
from minidb import Integer
from minidb import JsonFormat
from minidb import Numeric
from minidb import SchemaError
from minidb import Storage
from minidb import Text
from minidb import TransactionError

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


def main(folder: Path | None = None) -> None:
    if folder is None:
        folder = tempfile.mkdtemp()

    def open_db():
        db = Database()
        db.create_table(
            "accounts",
            [
                Column("id", Integer()),
                Column("owner", Text()),
                Column("balance", Numeric(10, 2)),
                Column("opened", Date()),
            ],
            primary_key="id",
        )
        db.attach(Storage(folder, JsonFormat(), sync=False))
        return db

    db = open_db()
    db.insert("accounts", {"id": 1, "owner": "Ada", "balance": "100.00", "opened": "2026-01-05"})
    db.insert("accounts", {"id": 2, "owner": "Alan", "balance": "50.00", "opened": "2026-02-01"})
    db.checkpoint()
    db.update("accounts", {"balance": "75.25"}, where={"id": 2})
    db.close()

    execute(lambda: sorted(os.listdir(folder)))

    snap = json.loads(open(os.path.join(folder, "snapshot.json"), "rb").read())
    execute(lambda: json.dumps(snap["commit_seq"]))
    execute(lambda: json.dumps(snap["tables"]["accounts"]["rows"]))

    # ------------------------------------------------------------------------------------------------------------------
    db.insert("accounts", {"id": 3, "owner": "Grace", "balance": "1.00", "opened": "2026-03-03"})
    db.close()
    with open(os.path.join(folder, "wal.log"), "ab") as f:
        f.write(b"\x00\x00\x01\x00garbage")  # a torn frame
    db = open_db()
    execute(lambda: [r["owner"] for r in db.query("accounts").order_by("id")])
    db.close()

    # ------------------------------------------------------------------------------------------------------------------
    other = Database()
    other.create_table("accounts", [Column("id", Integer())], primary_key="id")
    execute(lambda: other.attach(Storage(folder, sync=False)))


if __name__ == "__main__":
    main()
    print("Done.")
