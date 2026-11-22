"""Implement query operators in the iterator (Volcano) model.

Every operator is iterable: it yields :class:`Row` objects, which it gets by
iterating over its child operators. A query is a tree of operators, and
iterating over the root makes rows flow up from the leaves.
"""

import itertools
from typing import TYPE_CHECKING
from typing import Literal
from typing import Protocol
from typing import cast
from typing import override

from minidb.values import arithmetic
from minidb.values import ordered

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Mapping

    from minidb.schema import TableSchema
    from minidb.table import Table
    from minidb.values import Ordered
    from minidb.values import Row as StoredRow
    from minidb.values import Value

type JoinKind = Literal["inner", "left"]
type RowFunction = Callable[[Row], Value | None]

type RowPredicate = Callable[[Row], object]
type SortKey = tuple[str | RowFunction, bool]


class Accumulator(Protocol):
    """Fold the values of one group into a single result."""

    def add(self, value: Value) -> None:
        """Fold in one non-NULL value."""
        ...

    def result(self) -> Value | None:
        """Return the aggregate of the values added so far."""
        ...


class Source(Protocol):
    """Describe something a :class:`Scan` can read: a table, or a view of one."""

    name: str
    columns: tuple[str, ...]

    def scan(self) -> Iterator[tuple[int, StoredRow]]:
        """Yield every ``(rowid, row)`` pair."""
        ...


class PlannedSource(Source, Protocol):
    """Describe what the planner needs from a source: rows, indexes, and the committed table."""

    schema: TableSchema

    def committed(self) -> Table:
        """Return the committed table, for its statistics and indexes."""
        ...

    def lookup(self, key: Mapping[str, Value | None]) -> set[int]:
        """Return the rowids whose columns equal ``key``, through an index."""
        ...

    def range(
        self,
        column: str,
        lo: Value | None = None,
        hi: Value | None = None,
        *,
        lo_inclusive: bool = True,
        hi_inclusive: bool = True,
    ) -> list[int]:
        """Return the rowids within the bounds, through an ordered index."""
        ...

    def row(self, rowid: int) -> StoredRow:
        """Return the stored row itself."""
        ...


def _getter(source: str | RowFunction) -> RowFunction:
    """Turn a column name into a function that reads it; leave functions alone."""
    if callable(source):
        return source
    return lambda row: row[source]


def _nulls_first(value: Value | None) -> tuple[bool, Ordered]:
    """Make a sort key under which NULL sorts before every value.

    ``(False, None) < (True, anything)``, so ``None`` is never compared with
    a real value.
    """
    return (value is not None, ordered(value))


class _CountAcc:
    def __init__(self) -> None:
        self.n = 0

    def add(self, value: Value) -> None:  # noqa: ARG002 - only the number of values matters
        self.n += 1

    def result(self) -> Value | None:
        return self.n


class _ExtremeAcc:
    def __init__(self, *, largest: bool) -> None:
        self.largest = largest
        self.best: Value | None = None

    def add(self, value: Value) -> None:
        if self.best is None or (ordered(value) > ordered(self.best)) == self.largest:
            self.best = value

    def result(self) -> Value | None:
        return self.best


class _SumAcc:
    def __init__(self) -> None:
        self.total: Value | None = None

    def add(self, value: Value) -> None:
        self.total = value if self.total is None else cast("Value", arithmetic(self.total) + arithmetic(value))

    def result(self) -> Value | None:
        return self.total


class _AvgAcc(_SumAcc):
    def __init__(self) -> None:
        super().__init__()
        self.n = 0

    @override
    def add(self, value: Value) -> None:
        super().add(value)
        self.n += 1

    @override
    def result(self) -> Value | None:
        if self.total is None:
            return None
        return cast("Value", arithmetic(self.total) / arithmetic(self.n))


class AggregateFunction[A: Accumulator]:
    """Name an aggregate over a column, and make one accumulator per group.

    The type parameter is the kind of accumulator the function makes. It
    appears only as a return type, so ``AggregateFunction`` is covariant: a
    ``Count`` is an ``AggregateFunction[Accumulator]``.

    :param column: the column to aggregate; ``None`` (the default) means
        the whole row, as in ``COUNT(*)``.
    """

    def __init__(self, column: str | None = None) -> None:
        self.column = column

    def __repr__(self) -> str:
        return f"{type(self).__name__.upper()}({self.column or '*'})"

    def accumulator(self) -> A:
        """Return a fresh accumulator for one group; subclasses override this.

        :return: the accumulator.
        """
        raise NotImplementedError


class Avg(AggregateFunction[_AvgAcc]):
    """Average the non-NULL values of a column; the average of none is NULL."""

    @override
    def accumulator(self) -> _AvgAcc:
        return _AvgAcc()


class Count(AggregateFunction[_CountAcc]):
    """Count the non-NULL values of a column, or the rows (``COUNT(*)``)."""

    @override
    def accumulator(self) -> _CountAcc:
        return _CountAcc()


class Max(AggregateFunction[_ExtremeAcc]):
    """Find the largest non-NULL value of a column."""

    @override
    def accumulator(self) -> _ExtremeAcc:
        return _ExtremeAcc(largest=True)


class Min(AggregateFunction[_ExtremeAcc]):
    """Find the smallest non-NULL value of a column."""

    @override
    def accumulator(self) -> _ExtremeAcc:
        return _ExtremeAcc(largest=False)


class Operator:
    """Produce rows when iterated; the base class of every operator.

    Subclasses implement :meth:`__iter__`, :meth:`columns` and :attr:`label`.
    The planner sets :attr:`estimate`, the number of rows it expects.
    """

    children: tuple[Operator, ...] = ()
    estimate: float | None = None

    def __iter__(self) -> Iterator[Row]:
        raise NotImplementedError

    @property
    def label(self) -> str:
        """Return a one-line description, used by :meth:`explain`."""
        return type(self).__name__

    def columns(self) -> list[str]:
        """Return the names of the columns this operator produces.

        :return: the names, by default those of the first child.
        """
        return self.children[0].columns()

    def explain(self, indent: int = 0) -> str:
        """Describe the operator tree rooted here, one operator per line, with estimates.

        :param indent: the nesting depth of this operator; 0 by default.
        :return: the indented description.
        """
        line = "  " * indent + self.label
        if self.estimate is not None:
            line += f"  [~{self.estimate:,.0f} rows]"
        return "\n".join([line] + [child.explain(indent + 1) for child in self.children])


class NestedLoopJoin(Operator):
    """Join every pair of rows for which ``on`` is true.

    The right input is read once into a list: an operator may not be safely
    iterable twice, or may be expensive to re-run.

    :param left: the outer input.
    :param right: the inner input.
    :param on: the join condition; ``None`` (the default) joins every pair.
    :param kind: ``"inner"`` (the default), or ``"left"`` to keep unmatched
        left rows, padded with NULLs.
    :raises ValueError: for any other ``kind``.
    """

    def __init__(
        self, left: Operator, right: Operator, on: RowPredicate | None = None, kind: JoinKind = "inner"
    ) -> None:
        if kind not in ("inner", "left"):
            raise ValueError("kind must be 'inner' or 'left'")
        self.children = (left, right)
        self.on, self.kind = on, kind

    @override
    def __iter__(self) -> Iterator[Row]:
        left, right = self.children
        inner = list(right)  # materialize once: blocking
        nulls = dict.fromkeys(right.columns())
        for lrow in left:
            matches = [row for r in inner if self._matches(row := Row(lrow | r))]
            yield from matches
            if not matches and self.kind == "left":
                yield Row(lrow | nulls)

    @property
    @override
    def label(self) -> str:
        return f"NestedLoopJoin ({self.kind})"

    def _matches(self, row: Row) -> bool:
        return self.on is None or self.on(row) is True

    @override
    def columns(self) -> list[str]:
        return self.children[0].columns() + self.children[1].columns()


class Limit(Operator):
    """Skip ``offset`` rows, then yield at most ``count``.

    :param child: the input.
    :param count: the maximum number of rows; ``None`` for no maximum.
    :param offset: how many rows to skip first; 0 by default.
    """

    def __init__(self, child: Operator, count: int | None, offset: int = 0) -> None:
        self.children = (child,)
        self.count, self.offset = count, offset

    @override
    def __iter__(self) -> Iterator[Row]:
        stop = None if self.count is None else self.offset + self.count
        return itertools.islice(self.children[0], self.offset, stop)

    @property
    @override
    def label(self) -> str:
        return f"Limit {self.count} offset {self.offset}"


class Filter(Operator):
    """Keep the rows for which ``predicate`` is exactly ``True`` (WHERE semantics).

    :param child: the input.
    :param predicate: a function of the row; ``False`` and ``None``
        (UNKNOWN) both drop the row.
    """

    def __init__(self, child: Operator, predicate: RowPredicate) -> None:
        self.children = (child,)
        self.predicate = predicate

    @override
    def __iter__(self) -> Iterator[Row]:
        return (row for row in self.children[0] if self.predicate(row) is True)

    @property
    @override
    def label(self) -> str:
        return f"Filter {getattr(self.predicate, '__name__', self.predicate)}"


class Distinct(Operator):
    """Drop rows equal to an earlier row, keeping the first of each.

    :param child: the input.
    """

    def __init__(self, child: Operator) -> None:
        self.children = (child,)

    @override
    def __iter__(self) -> Iterator[Row]:
        seen: set[tuple[tuple[str, Value | None], ...]] = set()
        for row in self.children[0]:
            key = tuple(row.items())
            if key not in seen:
                seen.add(key)
                yield row


class Aggregate(Operator):
    """Group rows by ``group_by`` and compute ``aggregates`` for each group.

    This is hash aggregation: one dict entry per group. With no
    ``group_by`` the whole input is one group, so an empty input still
    produces one row.

    :param child: the input.
    :param group_by: the grouping columns.
    :param aggregates: ``{output name: aggregate function}``.
    """

    def __init__(
        self, child: Operator, group_by: list[str], aggregates: dict[str, AggregateFunction[Accumulator]]
    ) -> None:
        self.children = (child,)
        self.group_by, self.aggregates = list(group_by), aggregates

    @override
    def __iter__(self) -> Iterator[Row]:
        groups: dict[tuple[Value | None, ...], list[Accumulator]] = {}
        for row in self.children[0]:  # blocking
            key = tuple(row[c] for c in self.group_by)
            if key not in groups:
                groups[key] = self._fresh()
            self._accumulate(groups[key], row)
        if not groups and not self.group_by:  # aggregate of no rows
            groups[()] = self._fresh()
        for key, accs in groups.items():
            out = Row(zip(self.group_by, key, strict=True))
            out.update((name, acc.result()) for name, acc in zip(self.aggregates, accs, strict=True))
            yield out

    @property
    @override
    def label(self) -> str:
        aggs = ", ".join(f"{n}={f!r}" for n, f in self.aggregates.items())
        return f"Aggregate by {self.group_by or '()'}: {aggs}"

    def _accumulate(self, accs: list[Accumulator], row: Row) -> None:
        """Fold one row into a group's accumulators; aggregates skip NULLs."""
        for f, acc in zip(self.aggregates.values(), accs, strict=True):
            value = True if f.column is None else row[f.column]  # COUNT(*) counts rows
            if value is not None:
                acc.add(value)

    def _fresh(self) -> list[Accumulator]:
        return [f.accumulator() for f in self.aggregates.values()]

    @override
    def columns(self) -> list[str]:
        return self.group_by + list(self.aggregates)


class Project(Operator):
    """Compute output columns, each from a column name or a function of the row.

    :param child: the input.
    :param outputs: ``{output name: source column or function}``.
    """

    def __init__(self, child: Operator, outputs: dict[str, str | RowFunction]) -> None:
        self.children = (child,)
        self.outputs = outputs

    @override
    def __iter__(self) -> Iterator[Row]:
        getters = [(name, _getter(src)) for name, src in self.outputs.items()]
        for row in self.children[0]:
            yield Row({name: get(row) for name, get in getters})

    @property
    @override
    def label(self) -> str:
        return f"Project {', '.join(self.outputs)}"

    @override
    def columns(self) -> list[str]:
        return list(self.outputs)


class Row(dict[str, "Value | None"]):
    """Hold a result row, keyed by qualified names such as ``"u.age"``.

    An unqualified name such as ``"age"`` also works when exactly one
    column has it.

    >>> row = Row({"u.id": 1, "o.id": 10, "o.total": 25})
    >>> row["total"]
    25
    >>> row["id"]
    Traceback (most recent call last):
      ...
    KeyError: "ambiguous column 'id': one of ['o.id', 'u.id']"
    """

    def __missing__(self, key: str) -> Value | None:
        if "." not in key:
            found = [k for k in self if k.rpartition(".")[2] == key]
            if len(found) == 1:
                return self[found[0]]
            if found:
                raise KeyError(f"ambiguous column {key!r}: one of {sorted(found)}")
        raise KeyError(key)


class Scan(Operator):
    """Yield every row of a source, with names qualified by ``alias``.

    :param source: the table (or view) to read.
    :param alias: the qualifier for column names; ``None`` (the default)
        uses the source's name.
    """

    def __init__(self, source: Source, alias: str | None = None) -> None:
        self.source = source
        self.alias = alias or source.name

    @override
    def __iter__(self) -> Iterator[Row]:
        names = [(c, f"{self.alias}.{c}") for c in self.source.columns]
        for _, row in self.source.scan():
            yield Row({q: row[c] for c, q in names})

    @property
    @override
    def label(self) -> str:
        return f"Scan {self.source.name} AS {self.alias}"

    @override
    def columns(self) -> list[str]:
        return [f"{self.alias}.{c}" for c in self.source.columns]


class Sort(Operator):
    """Order rows by several keys, each ascending or descending; NULLs sort first.

    :param child: the input.
    :param keys: ``(column name or function, descending)`` pairs, most
        significant first.
    """

    def __init__(self, child: Operator, keys: list[SortKey]) -> None:
        self.children = (child,)
        self.keys = keys

    @override
    def __iter__(self) -> Iterator[Row]:
        rows = list(self.children[0])  # blocking
        for key, descending in reversed(self.keys):  # stable sorts, last key first
            get = _getter(key)
            rows.sort(key=lambda r: _nulls_first(get(r)), reverse=descending)
        return iter(rows)

    @property
    @override
    def label(self) -> str:
        return "Sort " + ", ".join(f"{k}{' DESC' if d else ''}" for k, d in self.keys)


class Sum(AggregateFunction[_SumAcc]):
    """Add up the non-NULL values of a column; the sum of no values is NULL."""

    @override
    def accumulator(self) -> _SumAcc:
        return _SumAcc()
