"""Compare a lookup by scan with a lookup through the primary-key index."""

import timeit

from minidb import Column
from minidb import Database
from minidb import Integer
from minidb import Text


def main() -> None:
    """Fill a table with 100,000 rows and time both kinds of lookup."""
    db = Database()
    db.create_table("t", [Column("id", Integer()), Column("name", Text())], primary_key="id")
    for i in range(100_000):
        db.insert("t", {"id": i, "name": f"n{i}"})
    scan = timeit.timeit(lambda: db.select("t", lambda r: r["id"] == 77_777), number=20) / 20
    index = timeit.timeit(lambda: db.select("t", {"id": 77_777}), number=20) / 20
    print(f"scan:  {scan * 1e3:8.3f} ms")
    print(f"index: {index * 1e3:8.3f} ms   ({scan / index:,.0f}x faster)")


if __name__ == "__main__":
    main()
