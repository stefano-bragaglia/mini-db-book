"""Define indexes: secondary structures that map column values to rowids."""
from collections.abc import Mapping
from typing import ClassVar
from typing import Iterable
from typing import Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
    column: tuple[str, ...]
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
