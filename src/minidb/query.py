"""Provide a fluent, immutable query builder on top of the operators."""

from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from typing import TYPE_CHECKING
from typing import Protocol

from minidb.operators import Aggregate
from minidb.operators import Distinct
from minidb.operators import Filter
from minidb.operators import Limit
from minidb.operators import NestedLoopJoin
from minidb.operators import PlannedSource
from minidb.operators import Project
from minidb.operators import Scan
from minidb.operators import Sort
from minidb.planner import Planner

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import AbstractContextManager

    from minidb.operators import Accumulator
    from minidb.operators import AggregateFunction
    from minidb.operators import JoinKind
    from minidb.operators import Operator
    from minidb.operators import Row
    from minidb.operators import RowFunction
    from minidb.operators import RowPredicate
    from minidb.operators import SortKey
    from minidb.values import Value


class QueryState(Protocol):
    """Describe where a query finds its tables, and how it protects its reads."""

    def table(self, name: str) -> PlannedSource:
        """Return the table (or view) called ``name``."""
        ...

    def reading(self) -> AbstractContextManager[object]:
        """Return a context manager to hold while the query reads."""
        ...


@dataclass(frozen=True)
class Query:
    """Build a query step by step; each method returns a new, extended query.

    Nothing runs until the query is iterated, or :meth:`all`, :meth:`first`
    or :meth:`explain` is called. The parts are assembled in the order SQL
    evaluates them: FROM and JOIN, WHERE, GROUP BY, HAVING, ORDER BY,
    SELECT, DISTINCT, LIMIT.

    :param state: where the tables come from.
    :param table: the first table, as in ``FROM table``.
    :param alias: its alias; ``None`` (the default) uses the table's name.
    """

    state: QueryState
    table: str
    alias: str | None = None
    joins: tuple[tuple[str, str | None, RowPredicate, JoinKind], ...] = ()
    filters: tuple[RowPredicate, ...] = ()
    grouping: tuple[str, ...] | None = None
    aggregates: dict[str, AggregateFunction[Accumulator]] = field(default_factory=dict)
    having_filters: tuple[RowPredicate, ...] = ()
    ordering: tuple[SortKey, ...] = ()
    outputs: dict[str, str | RowFunction] | None = None
    is_distinct: bool = False
    bounds: tuple[int | None, int] | None = None

    # -- building ---------------------------------------------------------------
    def join(self, table: str, on: RowPredicate, alias: str | None = None, kind: JoinKind = "inner") -> Query:
        """Join another table.

        :param table: the table to join.
        :param on: the join condition.
        :param alias: its alias; ``None`` (the default) uses its name.
        :param kind: ``"inner"`` (the default) or ``"left"``.
        :return: the extended query.
        """
        return replace(self, joins=(*self.joins, (table, alias, on, kind)))

    def where(self, predicate: RowPredicate) -> Query:
        """Keep only rows for which ``predicate`` is true; calls combine with AND.

        :param predicate: a function of the row.
        :return: the extended query.
        """
        return replace(self, filters=(*self.filters, predicate))

    def group_by(self, *columns: str, **aggregates: AggregateFunction[Accumulator]) -> Query:
        """Group rows by ``columns`` and compute ``aggregates`` for each group.

        :param columns: the grouping columns; none for a single group.
        :param aggregates: ``name=function`` for each output aggregate.
        :return: the extended query.
        """
        return replace(self, grouping=columns, aggregates=aggregates)

    def having(self, predicate: RowPredicate) -> Query:
        """Keep only groups for which ``predicate`` is true.

        :param predicate: a function of the aggregated row.
        :return: the extended query.
        """
        return replace(self, having_filters=(*self.having_filters, predicate))

    def order_by(self, *keys: str | RowFunction) -> Query:
        """Sort the result; ``"name"`` ascends, ``"-name"`` descends.

        :param keys: column names, optionally prefixed with ``-``, or
            functions of the row, most significant first.
        :return: the extended query.
        """
        parsed = tuple((k[1:], True) if isinstance(k, str) and k.startswith("-") else (k, False) for k in keys)
        return replace(self, ordering=(*self.ordering, *parsed))

    def select(self, *columns: str, **computed: str | RowFunction) -> Query:
        """Choose the output columns.

        ``select("u.name", total="o.total", double=lambda r: 2 * r["x"])``

        :param columns: columns to output, under their unqualified names.
        :param computed: ``name=column`` or ``name=function`` pairs.
        :return: the extended query.
        :raises ValueError: if two outputs would have the same name.
        """
        outputs: dict[str, str | RowFunction] = {c.rpartition(".")[2]: c for c in columns}
        if len(outputs) != len(columns):
            raise ValueError("duplicate output names; use keyword aliases")
        return replace(self, outputs=outputs | computed)

    def distinct(self) -> Query:
        """Drop duplicate result rows.

        :return: the extended query.
        """
        return replace(self, is_distinct=True)

    def limit(self, count: int | None, offset: int = 0) -> Query:
        """Return at most ``count`` rows, after skipping ``offset``.

        :param count: the maximum number of rows, or ``None`` for no limit.
        :param offset: the rows to skip first; 0 by default.
        :return: the extended query.
        """
        return replace(self, bounds=(count, offset))

    # -- planning ---------------------------------------------------------------
    def plan(self) -> Operator:
        """Return the physical plan chosen by the cost-based planner.

        :return: the root operator.
        """
        return Planner(self).plan()

    def plan_naive(self) -> Operator:
        """Return Chapter 7's plan: joins in the written order, every filter on top.

        :return: the root operator.
        """
        op: Operator = Scan(self.state.table(self.table), self.alias)
        for jtable, jalias, on, kind in self.joins:
            op = NestedLoopJoin(op, Scan(self.state.table(jtable), jalias), on, kind)
        for predicate in self.filters:
            op = Filter(op, predicate)
        return self.finish_plan(op)

    def finish_plan(self, op: Operator) -> Operator:
        """Add GROUP BY, HAVING, ORDER BY, SELECT, DISTINCT and LIMIT on top of ``op``.

        :param op: the plan for FROM, JOIN and WHERE.
        :return: the complete plan.
        """
        return self._shape(self._group(op))

    def _group(self, op: Operator) -> Operator:
        if self.grouping is not None:
            op = Aggregate(op, list(self.grouping), self.aggregates)
        for predicate in self.having_filters:
            op = Filter(op, predicate)
        return op

    def _shape(self, op: Operator) -> Operator:
        if self.ordering:
            op = Sort(op, list(self.ordering))
        if self.outputs is not None:
            op = Project(op, self.outputs)
        if self.is_distinct:
            op = Distinct(op)
        if self.bounds is not None:
            op = Limit(op, *self.bounds)
        return op

    # -- running ----------------------------------------------------------------
    def __iter__(self) -> Iterator[Row]:
        with self.state.reading():
            rows = list(self.plan())  # materialize while protected
        return iter(rows)

    def all(self) -> list[dict[str, Value | None]]:
        """Run the query and return every row, as a plain dict.

        :return: the result rows.
        """
        with self.state.reading():
            return [dict(row) for row in self.plan()]

    def first(self) -> dict[str, Value | None] | None:
        """Run the query and return its first row.

        :return: the first row, or ``None`` if there are no rows.
        """
        rows = self.limit(1).all()
        return rows[0] if rows else None

    def explain(self) -> str:
        """Describe the plan, one operator per line.

        :return: the description.
        """
        return self.plan().explain()
