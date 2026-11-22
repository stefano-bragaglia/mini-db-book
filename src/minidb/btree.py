"""Implement an in-memory B+ tree, and an ordered index built on it.

Internal nodes hold separator keys and children. Leaves hold the keys, each
with its set of values, and a link to the next leaf, so a range scan walks
the leaf level without climbing back up the tree.
"""

import bisect
from typing import TYPE_CHECKING
from typing import ClassVar

from minidb.index import KeyedIndex

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Iterator
    from collections.abc import Mapping

    from minidb.index import Key
    from minidb.values import Ordered
    from minidb.values import Value


class _Leaf[K: Ordered, V]:
    __slots__ = ("keys", "next", "values")

    def __init__(self) -> None:
        self.keys: list[K] = []
        self.values: list[set[V]] = []
        self.next: _Leaf[K, V] | None = None


class _Internal[K: Ordered, V]:
    __slots__ = ("children", "keys")

    def __init__(self, keys: list[K], children: list[_Node[K, V]]) -> None:
        self.keys = keys  # keys[i] is the smallest key under children[i + 1]
        self.children = children  # always len(keys) + 1 of them


type _Node[K: Ordered, V] = _Leaf[K, V] | _Internal[K, V]


class BPlusTree[K: Ordered, V]:
    """Map ordered keys to sets of values, with O(log n) inserts, lookups and range starts.

    ``K`` is the key type, which must be orderable; ``V`` the type of the
    values stored under each key.

    >>> tree = BPlusTree[int, str](order=4)
    >>> for k in [30, 10, 20]:
    ...     tree.insert(k, f"v{k}")
    >>> tree.get(20), [k for k, _ in tree.items(lo=15)]
    ({'v20'}, [20, 30])

    :param order: the maximum number of children per node; 64 by default.
    :raises ValueError: if ``order`` is below 3.
    """

    def __init__(self, order: int = 64) -> None:
        if order < 3:
            raise ValueError("order must be at least 3")
        self.order = order
        self.root: _Node[K, V] = _Leaf[K, V]()
        self._len = 0

    def __len__(self) -> int:
        return self._len

    @property
    def height(self) -> int:
        """Return the number of levels, counting the leaves."""
        node, h = self.root, 1
        while isinstance(node, _Internal):
            node, h = node.children[0], h + 1
        return h

    # -- search ---------------------------------------------------------------------------
    def _descend(self, key: K) -> tuple[_Leaf[K, V], list[_Internal[K, V]]]:
        """Return the leaf where ``key`` belongs, and the internal nodes on the way."""
        node, path = self.root, list[_Internal[K, V]]()
        while isinstance(node, _Internal):
            path.append(node)
            node = node.children[bisect.bisect_right(node.keys, key)]
        return node, path

    def _first_leaf(self) -> _Leaf[K, V]:
        node = self.root
        while isinstance(node, _Internal):
            node = node.children[0]
        return node

    def get(self, key: K) -> set[V]:
        """Return the values stored under ``key``.

        :param key: the key.
        :return: a new set; empty if the key is absent.
        """
        leaf, _ = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            return set(leaf.values[i])
        return set()

    def items(
        self, lo: K | None = None, hi: K | None = None, *, lo_inclusive: bool = True, hi_inclusive: bool = True
    ) -> Iterator[tuple[K, set[V]]]:
        """Yield ``(key, values)`` for the keys between ``lo`` and ``hi``, in order.

        :param lo: the lower bound; ``None`` (the default) for none.
        :param hi: the upper bound; ``None`` (the default) for none.
        :param lo_inclusive: whether ``lo`` itself is included; ``True`` by default.
        :param hi_inclusive: whether ``hi`` itself is included; ``True`` by default.
        :return: an iterator walking the leaves.
        """
        leaf: _Leaf[K, V] | None
        if lo is None:
            leaf, i = self._first_leaf(), 0
        else:
            leaf, _ = self._descend(lo)
            i = (bisect.bisect_left if lo_inclusive else bisect.bisect_right)(leaf.keys, lo)
        while leaf is not None:
            for key, values in zip(leaf.keys[i:], leaf.values[i:], strict=True):
                if hi is not None and (key > hi or (key == hi and not hi_inclusive)):
                    return
                yield key, values
            leaf, i = leaf.next, 0

    # -- insert ---------------------------------------------------------------------------
    def insert(self, key: K, value: V) -> None:
        """Store ``value`` under ``key``, splitting nodes that overflow.

        :param key: the key.
        :param value: the value to add to the key's set.
        """
        leaf, path = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            leaf.values[i].add(value)
            return
        leaf.keys.insert(i, key)
        leaf.values.insert(i, {value})
        self._len += 1
        if len(leaf.keys) >= self.order:
            self._split_leaf(leaf, path)

    def _split_leaf(self, leaf: _Leaf[K, V], path: list[_Internal[K, V]]) -> None:
        mid = len(leaf.keys) // 2
        right = _Leaf[K, V]()
        right.keys, leaf.keys = leaf.keys[mid:], leaf.keys[:mid]
        right.values, leaf.values = leaf.values[mid:], leaf.values[:mid]
        right.next, leaf.next = leaf.next, right
        self._insert_in_parent(leaf, right.keys[0], right, path)

    def _insert_in_parent(
        self, left: _Node[K, V], separator: K, right: _Node[K, V], path: list[_Internal[K, V]]
    ) -> None:
        if not path:  # the root split: the tree grows a level
            self.root = _Internal[K, V]([separator], [left, right])
            return
        parent = path.pop()
        i = next(j for j, child in enumerate(parent.children) if child is left)
        parent.keys.insert(i, separator)
        parent.children.insert(i + 1, right)
        if len(parent.children) > self.order:
            mid = len(parent.keys) // 2
            up = parent.keys[mid]
            sibling = _Internal[K, V](parent.keys[mid + 1 :], parent.children[mid + 1 :])
            parent.keys, parent.children = parent.keys[:mid], parent.children[: mid + 1]
            self._insert_in_parent(parent, up, sibling, path)

    # -- delete ---------------------------------------------------------------------------
    def remove(self, key: K, value: V) -> None:
        """Remove ``value`` from ``key``, dropping the key when its set is empty.

        Nodes are never merged ("lazy deletion"): simple, and fine for
        workloads that insert more than they delete.

        :param key: the key.
        :param value: the value to remove; nothing happens if it is absent.
        """
        leaf, _ = self._descend(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            leaf.values[i].discard(value)
            if not leaf.values[i]:
                del leaf.keys[i], leaf.values[i]
                self._len -= 1

    # -- for teaching ----------------------------------------------------------------------
    def dump(self) -> str:
        """Draw the tree's keys, one line per level.

        :return: the drawing.
        """
        lines: list[str] = []
        level: list[_Node[K, V]] = [self.root]
        while level:
            lines.append("   ".join("[" + " ".join(map(str, n.keys)) + "]" for n in level))
            level = [c for n in level if isinstance(n, _Internal) for c in n.children]
        return "\n".join(lines)


class BTreeIndex(KeyedIndex):
    """Answer lookups and ranges with a B+ tree: O(log n) for inserts too.

    :param name: the index's name.
    :param columns: the indexed columns, in key order.
    :param unique: whether two rows may share a key; ``False`` by default.
    :param order: the tree's maximum fan-out; 64 by default.
    """

    kind: ClassVar[str] = "btree"

    def __init__(self, name: str, columns: Iterable[str], *, unique: bool = False, order: int = 64) -> None:
        super().__init__(name, columns, unique=unique)
        self.tree: BPlusTree[Key, int] = BPlusTree(order)

    def add(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Record that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the row's values.
        """
        key = self.key_of(row)
        if key is not None:
            self.tree.insert(key, rowid)

    def remove(self, rowid: int, row: Mapping[str, Value | None]) -> None:
        """Forget that ``rowid`` holds ``row``.

        :param rowid: the row's rowid.
        :param row: the values the row had when it was added.
        """
        key = self.key_of(row)
        if key is not None:
            self.tree.remove(key, rowid)

    def lookup(self, key: Key) -> set[int]:
        """Return the rowids whose key equals ``key``.

        :param key: the key to look up.
        :return: a new set.
        """
        return self.tree.get(tuple(key))

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
        items = self.tree.items(lo, hi, lo_inclusive=lo_inclusive, hi_inclusive=hi_inclusive)
        return [rowid for _, rowids in items for rowid in sorted(rowids)]

    def distinct_keys(self) -> int:
        """Return the number of different keys in the index."""
        return len(self.tree)
