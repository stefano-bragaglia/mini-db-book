"""Plan queries: choose access paths, push filters down, and order joins by cost.

The planner turns a :class:`~minidb.query.Query` into a tree of physical
operators. Conditions written as :class:`~minidb.expr.Expr` objects can be
analysed; plain Python callables are opaque, and are applied last, exactly
where the query put them.
"""

import math
from typing import TYPE_CHECKING
from typing import Literal
from typing import override

from minidb.errors import DatabaseError
from minidb.expr import And
from minidb.expr import Col
from minidb.expr import Compare
from minidb.expr import Const
from minidb.expr import Expr
from minidb.expr import conjuncts
from minidb.operators import Filter
from minidb.operators import NestedLoopJoin
from minidb.operators import Operator
from minidb.operators import Row
from minidb.operators import Scan
from minidb.values import ordered

if TYPE_CHECKING:
    from collections.abc import Iterator

    from minidb.expr import CompareOp
    from minidb.index import Index
    from minidb.operators import PlannedSource
    from minidb.operators import RowPredicate
    from minidb.query import Query
    from minidb.values import Value

type Bounds = tuple[Value | None, Value | None, bool, bool]  # lo, hi, lo_inclusive, hi_inclusive

type Candidate = tuple[float, Operator, list[Expr]]  # (cost, access path, conditions it consumes)
type RangeCondition = tuple[CompareOp, Value, Expr]


# -- physical operators that need indexes or hashing ----------------------------------------
def _buckets(rows: Operator, keys: list[Expr]) -> dict[tuple[Value | None, ...], list[Row]]:
    """Group ``rows`` by their join key, leaving out keys with NULL: NULL never joins."""
    buckets: dict[tuple[Value | None, ...], list[Row]] = {}
    for row in rows:
        key = tuple(k.eval(row) for k in keys)
        if not any(v is None for v in key):
            buckets.setdefault(key, []).append(row)
    return buckets


def _conjunction(exprs: list[Expr]) -> Expr:
    return exprs[0] if len(exprs) == 1 else And(*exprs)


class HashJoin(Operator):
    """Join on equalities in O(|left| + |right|): hash one side, probe with the other.

    :param left: the left input.
    :param right: the right input.
    :param left_keys: the join columns of the left input.
    :param right_keys: the matching columns of the right input.
    :param build: which side to hash, ideally the smaller; ``"right"`` by default.
    """

    def __init__(
        self,
        left: Operator,
        right: Operator,
        left_keys: list[Expr],
        right_keys: list[Expr],
        build: Literal["left", "right"] = "right",
    ) -> None:
        self.children = (left, right)
        self.left_keys, self.right_keys, self.build = left_keys, right_keys, build

    @override
    def __iter__(self) -> Iterator[Row]:
        left, right = self.children
        if self.build == "right":
            build, build_keys, probe, probe_keys = right, self.right_keys, left, self.left_keys
        else:
            build, build_keys, probe, probe_keys = left, self.left_keys, right, self.right_keys
        buckets = _buckets(build, build_keys)  # blocking on the build side
        for row in probe:
            key = tuple(k.eval(row) for k in probe_keys)
            for match in buckets.get(key, ()):
                yield Row(row | match)

    @property
    @override
    def label(self) -> str:
        on = " AND ".join(f"{lk!r} = {rk!r}" for lk, rk in zip(self.left_keys, self.right_keys, strict=True))
        return f"HashJoin (build {self.build}) on {on}"

    @override
    def columns(self) -> list[str]:
        return self.children[0].columns() + self.children[1].columns()


class IndexLookup(Operator):
    """Yield the rows whose indexed columns equal ``key``, without a scan.

    :param source: the table or view.
    :param alias: the qualifier for column names.
    :param index_name: the index used, for :meth:`explain`.
    :param key: ``{column: value}`` to look up.
    """

    def __init__(self, source: PlannedSource, alias: str, index_name: str, key: dict[str, Value | None]) -> None:
        self.source, self.alias, self.index_name, self.key = source, alias, index_name, key

    @override
    def __iter__(self) -> Iterator[Row]:
        for rid in self.source.lookup(self.key):
            row = self.source.row(rid)
            yield Row({f"{self.alias}.{c}": row[c] for c in self.source.columns})

    @property
    @override
    def label(self) -> str:
        return f"IndexLookup {self.source.name} AS {self.alias} using {self.index_name} {self.key}"

    @override
    def columns(self) -> list[str]:
        return [f"{self.alias}.{c}" for c in self.source.columns]


class IndexRange(Operator):
    """Yield the rows whose ``column`` lies between ``lo`` and ``hi``, through an ordered index.

    :param source: the table or view.
    :param alias: the qualifier for column names.
    :param index_name: the index used, for :meth:`explain`.
    :param column: the indexed column.
    :param bounds: ``(lo, hi, lo_inclusive, hi_inclusive)``; a ``None``
        bound is open.
    """

    def __init__(self, source: PlannedSource, alias: str, index_name: str, column: str, bounds: Bounds) -> None:
        self.source, self.alias, self.index_name, self.column = source, alias, index_name, column
        self.bounds = bounds

    @override
    def __iter__(self) -> Iterator[Row]:
        lo, hi, lo_inclusive, hi_inclusive = self.bounds
        for rid in self.source.range(self.column, lo, hi, lo_inclusive=lo_inclusive, hi_inclusive=hi_inclusive):
            row = self.source.row(rid)
            yield Row({f"{self.alias}.{c}": row[c] for c in self.source.columns})

    @property
    @override
    def label(self) -> str:
        lo, hi, lo_inclusive, hi_inclusive = self.bounds
        left = "" if lo is None else f"{lo!r} {'<=' if lo_inclusive else '<'} "
        right = "" if hi is None else f" {'<=' if hi_inclusive else '<'} {hi!r}"
        return f"IndexRange {self.source.name} AS {self.alias} using {self.index_name}: {left}{self.column}{right}"

    @override
    def columns(self) -> list[str]:
        return [f"{self.alias}.{c}" for c in self.source.columns]


# -- the planner -------------------------------------------------------------------------
def _bounds(conditions: list[RangeCondition]) -> Bounds:
    """Combine range conditions on one column into the tightest lower and upper bounds."""
    lo: Value | None = None
    hi: Value | None = None
    lo_inclusive = hi_inclusive = True
    for op, value, _ in conditions:
        if op in (">", ">=") and (lo is None or ordered(value) > ordered(lo) or (value == lo and op == ">")):
            lo, lo_inclusive = value, op == ">="
        elif op in ("<", "<=") and (hi is None or ordered(value) < ordered(hi) or (value == hi and op == "<")):
            hi, hi_inclusive = value, op == "<="
    return lo, hi, lo_inclusive, hi_inclusive


class Planner:
    """Turn one query into a physical plan; also the query's :class:`~minidb.expr.Statistics`.

    :param query: the query to plan.
    """

    def __init__(self, query: Query) -> None:
        self.q = query
        rels = [Relation(query.state.table(query.table), query.alias or query.table)]
        rels += [Relation(query.state.table(t), a or t) for t, a, _, _ in query.joins]
        self.rels = {r.alias: r for r in rels}

    # -- column resolution and statistics ----------------------------------------------------

    def aliases(self, expr: Expr) -> set[str] | None:
        """Return the relations an expression reads from.

        :param expr: the expression.
        :return: their aliases, or ``None`` if a column can't be resolved.
        """
        out: set[str] = set()
        for name in expr.columns():
            hit = self.resolve(name)
            if hit is None:
                return None
            out.add(hit[0])
        return out

    def distinct(self, column: str) -> int | None:
        """Return the number of distinct values of a column, from statistics or an index.

        :param column: the column, qualified or not.
        :return: the count, or ``None`` if unknown.
        """
        hit = self.resolve(column)
        if hit is None:
            return None
        table = self.rels[hit[0]].table
        if hit[1] in table.stats:
            return table.stats[hit[1]]
        index = table.index_on([hit[1]])
        return max(index.distinct_keys(), 1) if index is not None else None

    def resolve(self, name: str) -> tuple[str, str] | None:
        """Find which relation a column belongs to.

        :param name: ``"u.age"`` or ``"age"``.
        :return: ``(alias, column)``, or ``None`` if the name is unknown or
            ambiguous.
        """
        if "." in name:
            alias, _, column = name.partition(".")
            rel = self.rels.get(alias)
            return (alias, column) if rel and column in rel.columns else None
        found = [(a, name) for a, r in self.rels.items() if name in r.columns]
        return found[0] if len(found) == 1 else None

    # -- access paths: how to read one table ---------------------------------------------------

    @staticmethod
    def _lookup_path(rel: Relation, index: Index, eq: dict[str, tuple[Value, Expr]], n: int) -> Candidate | None:
        if not set(index.columns) <= eq.keys():
            return None
        matches = n / max(index.distinct_keys(), 1)
        op = IndexLookup(rel.source, rel.alias, index.name, {c: eq[c][0] for c in index.columns})
        op.estimate = matches
        return (1 + matches, op, [eq[c][1] for c in index.columns])

    @staticmethod
    def _prepared(rel: Relation, column: str, value: Value) -> Value | None:
        """Normalize ``value`` for ``column``, or return ``None`` if it isn't valid there."""
        try:
            return rel.source.schema.column(column).prepare(value)
        except DatabaseError:
            return None  # not a valid value: compare it as written

    @staticmethod
    def _range_path(rel: Relation, index: Index, ranges: dict[str, list[RangeCondition]], n: int) -> Candidate | None:
        if index.kind == "hash" or len(index.columns) != 1 or index.columns[0] not in ranges:
            return None
        column = index.columns[0]
        bounds = _bounds(ranges[column])
        matches = n * (1 / 3) ** ((bounds[0] is not None) + (bounds[1] is not None))
        op = IndexRange(rel.source, rel.alias, index.name, column, bounds)
        op.estimate = matches
        return (1 + matches, op, [p for _, _, p in ranges[column]])

    def _canonical(
        self, rel: Relation, preds: list[Expr]
    ) -> tuple[list[Expr], dict[str, tuple[Value, Expr]], dict[str, list[RangeCondition]]]:
        """Normalize the constants in ``column op constant`` conditions, and sort them by use.

        :return: the rewritten conditions; the equalities by column; and the
            range conditions by column.
        """
        canonical: list[Expr] = []
        eq: dict[str, tuple[Value, Expr]] = {}
        ranges: dict[str, list[RangeCondition]] = {}
        for p in preds:
            found = self._column_constant(rel, p)
            canonical.append(found[0] if found else p)
            if found is None:
                continue
            q, column, value = found
            if q.op == "=":
                eq[column] = (value, q)
            elif q.op in ("<", "<=", ">", ">="):
                ranges.setdefault(column, []).append((q.op, value, q))
        return canonical, eq, ranges

    def _column_constant(self, rel: Relation, p: Expr) -> tuple[Compare, str, Value] | None:
        """Return ``p`` as ``column op constant``, the constant prepared like a stored value."""
        if not isinstance(p, Compare):
            return None
        c = p.column_first()
        if not isinstance(c.left, Col) or not isinstance(c.right, Const) or c.right.value is None:
            return None
        hit = self.resolve(c.left.name)
        value = self._prepared(rel, hit[1], c.right.value) if hit else None
        if hit is None or value is None:
            return None
        return Compare(c.op, c.left, Const(value)), hit[1], value

    def access_path(self, rel: Relation, preds: list[Expr]) -> tuple[Operator, float]:
        """Choose the cheapest way to read ``rel`` given its own conditions.

        :param rel: the relation.
        :param preds: the conditions that mention only ``rel``.
        :return: the access path, with remaining conditions on top, and the
            estimated number of rows it produces.
        """
        preds, eq, ranges = self._canonical(rel, preds)
        n = len(rel.table)
        scan = Scan(rel.source, rel.alias)
        scan.estimate = n
        candidates: list[Candidate] = [(float(n), scan, [])]
        for index in rel.table.indexes.values():
            found = (self._lookup_path(rel, index, eq, n), self._range_path(rel, index, ranges, n))
            candidates.extend(c for c in found if c is not None)
        _, op, consumed = min(candidates, key=lambda c: c[0])
        estimate = n * math.prod(p.selectivity(self) for p in preds)
        residual = [p for p in preds if not any(p is c for c in consumed)]
        if residual:
            op = Filter(op, _conjunction(residual))
            op.estimate = estimate
        return op, estimate

    # -- join ordering: greedy, smallest intermediate result first ------------------------------

    def _equi_sides(self, e: Expr, alias: str, joined: set[str]) -> tuple[Col, Col] | None:
        """Return ``(joined side, new side)`` if ``e`` equates a column of each."""
        if not (isinstance(e, Compare) and e.op == "=" and isinstance(e.left, Col) and isinstance(e.right, Col)):
            return None
        lhs, rhs = self.resolve(e.left.name), self.resolve(e.right.name)
        if lhs is None or rhs is None:
            return None
        if rhs[0] == alias and lhs[0] in joined:
            return e.left, e.right
        return (e.right, e.left) if lhs[0] == alias and rhs[0] in joined else None

    def _join_op(
        self,
        left: Operator,
        *,
        left_est: float,
        right: Operator,
        right_est: float,
        alias: str,
        joined: set[str],
        usable: list[Expr],
    ) -> Operator:
        """Join with a hash join when there are equalities between the sides, else nested loops."""
        left_keys: list[Expr] = []
        right_keys: list[Expr] = []
        others: list[Expr] = []
        for e in usable:
            sides = self._equi_sides(e, alias, joined)
            if sides is None:
                others.append(e)
            else:
                left_keys.append(sides[0])
                right_keys.append(sides[1])
        if not left_keys:
            return NestedLoopJoin(left, right, _conjunction(others) if others else None)
        op: Operator = HashJoin(left, right, left_keys, right_keys, "right" if right_est <= left_est else "left")
        return Filter(op, _conjunction(others)) if others else op

    def _score(
        self, alias: str, joined: set[str], est: float, right_est: float, pending: list[tuple[Expr, set[str]]]
    ) -> tuple[bool, float]:
        """Rate joining ``alias`` next: connected joins first, then the smallest estimate."""
        usable = [e for e, al in pending if alias in al and al <= joined | {alias}]
        size = est * right_est * math.prod(e.selectivity(self) for e in usable)
        return (not usable, size)

    def join(self, paths: dict[str, tuple[Operator, float]], multi: list[tuple[Expr, set[str]]]) -> Operator:
        """Join the access paths, always adding the relation that gives the smallest result.

        :param paths: the access path and estimate of each relation.
        :param multi: conditions that mention several relations, with their aliases.
        :return: the joined plan.
        """
        remaining = dict(paths)
        start = min(remaining, key=lambda a: remaining[a][1])
        op, est = remaining.pop(start)
        joined, pending = {start}, list(multi)
        while remaining:
            scores = {a: self._score(a, joined, est, remaining[a][1], pending) for a in remaining}
            alias = min(scores, key=scores.__getitem__)
            right, right_est = remaining.pop(alias)
            usable = [e for e, al in pending if alias in al and al <= joined | {alias}]
            pending = [(e, al) for e, al in pending if not any(e is u for u in usable)]
            op = self._join_op(
                op, left_est=est, right=right, right_est=right_est, alias=alias, joined=joined, usable=usable
            )
            est = scores[alias][1]
            op.estimate = est
            joined.add(alias)
        for e, _ in pending:
            op = Filter(op, e)
        return op

    # -- putting it together -----------------------------------------------------------------

    def _classify(self) -> tuple[dict[str, list[Expr]], list[tuple[Expr, set[str]]], list[RowPredicate]]:
        """Split every condition into conjuncts, and sort them by the relations they mention."""
        local: dict[str, list[Expr]] = {a: [] for a in self.rels}
        multi: list[tuple[Expr, set[str]]] = []
        opaque: list[RowPredicate] = []
        for predicate in [*self.q.filters, *(on for _, _, on, _ in self.q.joins)]:
            parts = conjuncts(predicate) if isinstance(predicate, Expr) else [predicate]
            for part in parts:
                self._place(part, local, multi, opaque)
        return local, multi, opaque

    def _place(
        self,
        part: RowPredicate,
        local: dict[str, list[Expr]],
        multi: list[tuple[Expr, set[str]]],
        opaque: list[RowPredicate],
    ) -> None:
        aliases = self.aliases(part) if isinstance(part, Expr) else None
        if not aliases or not isinstance(part, Expr):
            opaque.append(part)  # callables, unresolvable or constant
        elif len(aliases) == 1:
            local[next(iter(aliases))].append(part)
        else:
            multi.append((part, aliases))

    def plan(self) -> Operator:
        """Build the physical plan for the query.

        :return: the root operator.
        """
        if any(kind != "inner" for _, _, _, kind in self.q.joins):
            return self.q.plan_naive()  # outer joins: keep the written order
        local, multi, opaque = self._classify()
        paths = {a: self.access_path(self.rels[a], local[a]) for a in self.rels}
        op = self.join(paths, multi)
        for predicate in opaque:
            op = Filter(op, predicate)
        return self.q.finish_plan(op)


class Relation:
    """Describe one FROM or JOIN item: a source, its alias, and its committed table.

    :param source: the table, or a transaction's view of it.
    :param alias: the name the query uses for it.
    """

    def __init__(self, source: PlannedSource, alias: str) -> None:
        self.source, self.alias = source, alias
        self.table = source.committed()  # for statistics and indexes
        self.columns = set(source.columns)
