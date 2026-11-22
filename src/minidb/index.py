"""Define indexes: secondary structures that map column values to rowids."""

import bisect
import itertools
import math
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Protocol
from typing import runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping

    from minidb.values import Value

type Key = tuple[Value | None, ...]


class Index(Protocol):
    """Describe what every kind of index offers.

    An index maps the *key* of a row, the tuple of its values in the
    indexed columns, to the set of rowids having that key. Rows whose key
    contains NULL are not indexed, because NULL never equals anything.
    """

    kind: ClassVar[str]
    name: str
    columns: tuple[str, ...]
    unique: bool

    def key_of(self, row: Mapping[str, Value | None]) -> Key | None:
        """Return the row's key, or ``None`` if any of its values is NULL."""
        ...

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``."""
        ...

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``."""
        ...

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``, as a new set."""
        ...

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        ...


class KeyedIndex:
    """Provide the attributes and the :meth:`key_of` that all indexes share.

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    """

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool) -> None:
        self.name: str = name
        self.columns: tuple[str, ...] = tuple(columns)
        self.unique: bool = unique

    def key_of(self, row: Mapping[str, Value | None]) -> Key | None:
        """Return the row's values in the indexed columns, or ``None`` if one is NULL.

        >>> KeyedIndex("i", ["a", "b"], unique=False).key_of({"a": 1, "b": 2, "c": 3})
        (1, 2)
        >>> KeyedIndex("i", ["a", "b"], unique=False).key_of({"a": 1, "b": None, "c": 3}) is None
        True

        :param row: a row with (at least) the indexed columns.
        :return: the key tuple, or ``None``.
        """
        key = tuple(row[c] for c in self.columns)
        return None if any(v is None for v in key) else key


class HashIndex(KeyedIndex):
    """Answer equality lookups in O(1) with a dict from key to rowids.

    >>> index = HashIndex("by_city", ["city"])
    >>> index.add(1, {"city": "London"})
    >>> index.add(4, {"city": "London"})
    >>> index.lookup(("London",))
    {1, 4}

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    """

    kind: ClassVar[str] = "hash"

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool = False) -> None:
        super().__init__(name, columns, unique=unique)
        self._entries: dict[Key, set[int]] = {}

    def __repr__(self) -> str:
        return f"<{'unique ' if self.unique else ''}{self.kind} index {self.name} on {self.columns}>"

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the row's values.
        """
        key = self.key_of(row)
        if key is not None:
            self._entries.setdefault(key, set()).add(rowid)

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``, dropping keys left with no rows.

        :param rowid: the row's rowid.
        :param row: the values the row had when it was added.
        """
        key = self.key_of(row)
        ids = self._entries.get(key) if key is not None else None
        if key is not None and ids is not None:
            ids.discard(rowid)
            if not ids:
                del self._entries[key]  # don't keep empty buckets around

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``.

        :param key: the key to look up.
        :return: a new set, which the caller may modify.
        """
        return set(self._entries.get(tuple(key), ()))

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        return len(self._entries)


@runtime_checkable
class OrderedIndex(Index, Protocol):
    """Describe an index that also answers range queries, in key order."""

    def range(
        self, lo: Key | None, hi: Key | None, *, lo_inclusive: bool = True, hi_inclusive: bool = True
    ) -> list[int]:
        """Return the rowids with ``lo <= key <= hi``, in key order; ``None`` bounds are open."""
        ...


class IndexFactory(Protocol):
    """Describe what makes an index: any index class's constructor fits."""

    def __call__(self, name: str, columns: Iterable[str], *, unique: bool = False) -> Index:
        """Create an empty index."""
        ...


class SortedIndex(KeyedIndex):
    """Keep ``(key, rowid)`` pairs in a sorted list: lookups and ranges by binary search.

    Inserting shifts the list, so it costs O(n); Chapter 15 fixes that.

    >>> index = SortedIndex("by_age", ["age"])
    >>> for rowid, age in [(1, 41), (2, 36), (3, 85)]:
    ...     index.add(rowid, {"age": age})
    >>> index.range((40,), None)
    [1, 3]

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    """

    kind: ClassVar[str] = "sorted"

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool = False) -> None:
        super().__init__(name, columns, unique=unique)
        self._sorted: list[tuple[Key, int]] = []

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the row's values.
        """
        key = self.key_of(row)
        if key is not None:
            bisect.insort(self._sorted, (key, rowid))  # O(n): the list shifts

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the values the row had when it was added.
        """
        key = self.key_of(row)
        if key is None:
            return
        i = bisect.bisect_left(self._sorted, (key, rowid))
        if i < len(self._sorted) and self._sorted[i] == (key, rowid):
            del self._sorted[i]

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``.

        :param key: the key to look up.
        :return: a new set.
        """
        key = tuple(key)
        i = bisect.bisect_left(self._sorted, (key,))  # (key,) sorts before (key, any rowid)
        found: set[int] = set()
        while i < len(self._sorted) and self._sorted[i][0] == key:
            found.add(self._sorted[i][1])
            i += 1
        return found

    def range(
        self, lo: Key | None, hi: Key | None, *, lo_inclusive: bool = True, hi_inclusive: bool = True
    ) -> list[int]:
        """Return the rowids with ``lo <= key <= hi``, in key order.

        :param lo: the lower bound, or ``None`` for none.
        :param hi: the upper bound, or ``None`` for none.
        :param lo_inclusive: whether ``lo`` itself matches; ``True`` by default.
        :param hi_inclusive: whether ``hi`` itself matches; ``True`` by default.
        :return: the matching rowids.
        """
        i = self._start(lo, lo_inclusive=lo_inclusive)
        found: list[int] = []
        while i < len(self._sorted) and not _beyond(self._sorted[i][0], hi, hi_inclusive=hi_inclusive):
            found.append(self._sorted[i][1])
            i += 1
        return found

    def _start(self, lo: Key | None, *, lo_inclusive: bool) -> int:
        if lo is None:
            return 0
        if lo_inclusive:
            return bisect.bisect_left(self._sorted, (lo,))
        return bisect.bisect_right(self._sorted, (lo, math.inf))  # after every (lo, rowid)

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        return sum(1 for _ in itertools.groupby(self._sorted, key=lambda e: e[0]))


def _beyond(key: Key, hi: Key | None, *, hi_inclusive: bool) -> bool:
    """Tell whether ``key`` lies past the upper bound ``hi``."""
    return hi is not None and (key > hi or (key == hi and not hi_inclusive))
