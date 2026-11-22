"""Insert 200,000 random keys into each kind of index, then run 1,000 range scans."""

import random
import time

from minidb.btree import BTreeIndex
from minidb.index import HashIndex
from minidb.index import KeyedIndex
from minidb.index import SortedIndex


def fill(index: KeyedIndex, rows: list[dict[str, int]]) -> float:
    """Add every row to ``index``.

    :param index: an empty index on column ``k``.
    :param rows: the rows to add.
    :return: the time taken, in seconds.
    """
    t0 = time.perf_counter()
    for rowid, row in enumerate(rows):
        index.add(rowid, dict(row))
    return time.perf_counter() - t0


def scan(index: SortedIndex | BTreeIndex, rnd: random.Random) -> float:
    """Run 1,000 range queries, each over one thousandth of the key space.

    :param index: a filled ordered index.
    :param rnd: the source of random bounds.
    :return: the time taken, in seconds.
    """
    t0 = time.perf_counter()
    for _ in range(1000):
        lo = rnd.randrange(10**9)
        index.range((lo,), (lo + 10**6,))
    return time.perf_counter() - t0


def main() -> None:
    """Print insert and range times for the three kinds of index."""
    rnd = random.Random(1)  # noqa: S311 - test data, not cryptography
    rows = [{"k": rnd.randrange(10**9)} for _ in range(200_000)]
    print(f"{'index':<12}{'200k inserts':>14}{'1k range scans':>16}")
    print(f"{'HashIndex':<12}{fill(HashIndex('i', ['k']), rows):>12.2f} s{'(no ranges)':>16}")
    for index in (SortedIndex("i", ["k"]), BTreeIndex("i", ["k"])):
        inserts = fill(index, rows)
        print(f"{type(index).__name__:<12}{inserts:>12.2f} s{scan(index, rnd):>14.2f} s")


if __name__ == "__main__":
    main()
