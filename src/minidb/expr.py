"""Build predicates the planner can look inside: expression trees.

``col("age") > 30`` is not ``True`` or ``False`` but a :class:`Compare`
object. Expressions are callable, so they work anywhere a predicate does,
and they follow SQL's three-valued logic: ``None`` means UNKNOWN.
"""

from typing import TYPE_CHECKING
from typing import Literal
from typing import NoReturn
from typing import Protocol
from typing import cast
from typing import override

from minidb.values import arithmetic
from minidb.values import ordered

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

    from minidb.values import Ordered
    from minidb.values import Value

type CompareOp = Literal["=", "!=", "<", "<=", ">", ">="]
type ArithOp = Literal["+", "-", "*", "/"]

# System R's default selectivities, used when nothing better is known
EQ_SELECTIVITY = 1 / 10
RANGE_SELECTIVITY = 1 / 3
OTHER_SELECTIVITY = 1 / 2


class Statistics(Protocol):
    """Describe what selectivity estimates need to know about columns."""

    def distinct(self, column: str) -> int | None:
        """Return the number of distinct values in ``column``, or ``None`` if unknown."""
        ...


def _eq_selectivity(distinct: int | None) -> float:
    return 1 / distinct if distinct else EQ_SELECTIVITY


class Expr:
    """Represent an expression over a row; the base of every expression node.

    The comparison and arithmetic operators build new expressions instead of
    computing answers, and ``&``, ``|``, ``~`` combine conditions.

    >>> e = (col("age") >= 30) & ~col("city").is_null()
    >>> e
    ((age >= 30) AND NOT city IS NULL)
    >>> e({"age": 41, "city": "Paris"}), e({"age": None, "city": "Paris"})
    (True, None)
    """

    __hash__ = object.__hash__  # we override ==, but keep identity hashing

    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        """Evaluate the expression against ``row``; subclasses override this.

        :param row: the row, by column name.
        :return: the value, ``None`` meaning NULL or UNKNOWN.
        """
        raise NotImplementedError

    def __call__(self, row: Mapping[str, Value | None]) -> Value | None:  # noqa: D102 - a dunder
        return self.eval(row)

    def columns(self) -> set[str]:
        """Return the names of the columns the expression reads.

        :return: the column names, as written.
        """
        return set()

    def selectivity(self, stats: Statistics) -> float:
        """Estimate the fraction of rows for which this condition is true.

        :param stats: what is known about the columns.
        :return: a number between 0 and 1; 1/2 unless a subclass knows better.
        """
        del stats
        return OTHER_SELECTIVITY

    # -- building expressions with operators -----------------------------------------
    # Returning an expression from == and != is the point of this class, so
    # the incompatibility with object.__eq__ is deliberate.
    @override
    def __eq__(self, other: object) -> Compare:  # pyrefly: ignore[bad-override]
        return Compare("=", self, _wrap(other))

    @override
    def __ne__(self, other: object) -> Compare:  # pyrefly: ignore[bad-override]
        return Compare("!=", self, _wrap(other))

    def __lt__(self, other: object) -> Compare:
        return Compare("<", self, _wrap(other))

    def __le__(self, other: object) -> Compare:
        return Compare("<=", self, _wrap(other))

    def __gt__(self, other: object) -> Compare:
        return Compare(">", self, _wrap(other))

    def __ge__(self, other: object) -> Compare:
        return Compare(">=", self, _wrap(other))

    def __and__(self, other: object) -> And:
        return And(self, _wrap(other))

    def __or__(self, other: object) -> Or:
        return Or(self, _wrap(other))

    def __invert__(self) -> Not:
        return Not(self)

    def __add__(self, other: object) -> Arith:
        return Arith("+", self, _wrap(other))

    def __sub__(self, other: object) -> Arith:
        return Arith("-", self, _wrap(other))

    def __mul__(self, other: object) -> Arith:
        return Arith("*", self, _wrap(other))

    def __truediv__(self, other: object) -> Arith:
        return Arith("/", self, _wrap(other))

    def is_null(self) -> IsNull:
        """Return the condition ``self IS NULL``, which is never UNKNOWN.

        :return: the condition.
        """
        return IsNull(self)

    def is_not_null(self) -> Not:
        """Return the condition ``self IS NOT NULL``.

        :return: the condition.
        """
        return Not(IsNull(self))

    def isin(self, *values: Value | None) -> In:
        """Return the condition ``self IN (values)``.

        :param values: the values to look for.
        :return: the condition.
        """
        return In(self, values)

    def __bool__(self) -> NoReturn:
        raise TypeError("use & | ~ to combine expressions, not and/or/not")


def _wrap(value: object) -> Expr:
    """Turn a Python value into a constant; leave expressions alone."""
    return value if isinstance(value, Expr) else Const(cast("Value | None", value))


class Col(Expr):
    """Read a column: ``Col("age")``, or ``Col("u.age")`` qualified by an alias.

    :param name: the column's name, qualified or not.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        return row[self.name]

    @override
    def columns(self) -> set[str]:
        return {self.name}

    def __repr__(self) -> str:
        return self.name


class Const(Expr):
    """Hold a constant value.

    :param value: the value; ``None`` is NULL.
    """

    def __init__(self, value: Value | None) -> None:
        self.value = value

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        return self.value

    def __repr__(self) -> str:
        return "NULL" if self.value is None else repr(self.value)


_COMPARE: dict[CompareOp, Callable[[Ordered, Ordered], bool]] = {
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}
_FLIPPED: dict[CompareOp, CompareOp] = {"=": "=", "!=": "!=", "<": ">", "<=": ">=", ">": "<", ">=": "<="}


class Compare(Expr):
    """Compare two expressions; UNKNOWN if either side is NULL.

    >>> Compare("<", Col("a"), Const(3))({"a": 1}), (col("a") < 3)({"a": None})
    (True, None)

    :param op: one of ``= != < <= > >=``.
    :param left: the left operand.
    :param right: the right operand.
    """

    def __init__(self, op: CompareOp, left: Expr, right: Expr) -> None:
        self.op, self.left, self.right = op, left, right

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        a, b = self.left.eval(row), self.right.eval(row)
        if a is None or b is None:
            return None  # UNKNOWN
        return _COMPARE[self.op](ordered(a), ordered(b))

    @override
    def columns(self) -> set[str]:
        return self.left.columns() | self.right.columns()

    def flipped(self) -> Compare:
        """Return the same condition with the operands swapped: ``3 < a`` becomes ``a > 3``.

        :return: the flipped comparison.
        """
        return Compare(_FLIPPED[self.op], self.right, self.left)

    def column_first(self) -> Compare:
        """Return this comparison with a column on the left, if either side is one.

        :return: ``self`` or :meth:`flipped`.
        """
        return self.flipped() if isinstance(self.right, Col) and not isinstance(self.left, Col) else self

    @override
    def selectivity(self, stats: Statistics) -> float:
        c = self.column_first()
        if isinstance(c.left, Col) and isinstance(c.right, Col):
            if c.op != "=":
                return RANGE_SELECTIVITY
            known = [n for n in (stats.distinct(c.left.name), stats.distinct(c.right.name)) if n]
            return 1 / max(known) if known else EQ_SELECTIVITY
        if not isinstance(c.left, Col):
            return OTHER_SELECTIVITY
        eq = _eq_selectivity(stats.distinct(c.left.name))
        if c.op in ("=", "!="):
            return eq if c.op == "=" else 1 - eq
        return RANGE_SELECTIVITY

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"


class And(Expr):
    """Combine conditions with AND: false if any is false, else UNKNOWN if any is.

    :param items: the conditions.
    """

    def __init__(self, *items: Expr) -> None:
        self.items = items

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        results = [item.eval(row) for item in self.items]
        if any(r is False for r in results):
            return False
        return None if any(r is None for r in results) else True

    @override
    def columns(self) -> set[str]:
        return set[str]().union(*(i.columns() for i in self.items))

    @override
    def selectivity(self, stats: Statistics) -> float:
        result = 1.0
        for item in self.items:
            result *= item.selectivity(stats)  # the independence assumption
        return result

    def __repr__(self) -> str:
        return "(" + " AND ".join(map(repr, self.items)) + ")"


class Or(Expr):
    """Combine conditions with OR: true if any is true, else UNKNOWN if any is.

    :param items: the conditions.
    """

    def __init__(self, *items: Expr) -> None:
        self.items = items

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        results = [item.eval(row) for item in self.items]
        if any(r is True for r in results):
            return True
        return None if any(r is None for r in results) else False

    @override
    def columns(self) -> set[str]:
        return set[str]().union(*(i.columns() for i in self.items))

    @override
    def selectivity(self, stats: Statistics) -> float:
        result = 0.0
        for item in self.items:
            s = item.selectivity(stats)
            result = result + s - result * s
        return result

    def __repr__(self) -> str:
        return "(" + " OR ".join(map(repr, self.items)) + ")"


class Not(Expr):
    """Negate a condition; NOT UNKNOWN is UNKNOWN.

    :param item: the condition.
    """

    def __init__(self, item: Expr) -> None:
        self.item = item

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        v = self.item.eval(row)
        return None if v is None else not v

    @override
    def columns(self) -> set[str]:
        return self.item.columns()

    @override
    def selectivity(self, stats: Statistics) -> float:
        return 1 - self.item.selectivity(stats)

    def __repr__(self) -> str:
        return f"NOT {self.item!r}"


class IsNull(Expr):
    """Test for NULL; the result is never UNKNOWN.

    :param item: the expression to test.
    """

    def __init__(self, item: Expr) -> None:
        self.item = item

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool:
        return self.item.eval(row) is None

    @override
    def columns(self) -> set[str]:
        return self.item.columns()

    @override
    def selectivity(self, stats: Statistics) -> float:
        return EQ_SELECTIVITY

    def __repr__(self) -> str:
        return f"{self.item!r} IS NULL"


class In(Expr):
    """Test membership in a list of constants, SQL-style.

    ``x IN (1, NULL)`` is UNKNOWN, not false, when ``x`` is 2.

    :param item: the expression to test.
    :param values: the constants.
    """

    def __init__(self, item: Expr, values: tuple[Value | None, ...]) -> None:
        self.item, self.values = item, values

    @override
    def eval(self, row: Mapping[str, Value | None]) -> bool | None:
        v = self.item.eval(row)
        if v is None:
            return None
        if v in self.values:
            return True
        return None if None in self.values else False

    @override
    def columns(self) -> set[str]:
        return self.item.columns()

    @override
    def selectivity(self, stats: Statistics) -> float:
        if not isinstance(self.item, Col):
            return OTHER_SELECTIVITY
        return min(1.0, len(self.values) * _eq_selectivity(stats.distinct(self.item.name)))

    def __repr__(self) -> str:
        return f"{self.item!r} IN {self.values!r}"


_ARITH: dict[ArithOp, Callable[[Value, Value], Value]] = {
    "+": lambda a, b: cast("Value", arithmetic(a) + arithmetic(b)),
    "-": lambda a, b: cast("Value", arithmetic(a) - arithmetic(b)),
    "*": lambda a, b: cast("Value", arithmetic(a) * arithmetic(b)),
    "/": lambda a, b: cast("Value", arithmetic(a) / arithmetic(b)),
}


class Arith(Expr):
    """Apply ``+ - * /`` to two expressions; NULL if either is NULL.

    :param op: the operator.
    :param left: the left operand.
    :param right: the right operand.
    """

    def __init__(self, op: ArithOp, left: Expr, right: Expr) -> None:
        self.op, self.left, self.right = op, left, right

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        a, b = self.left.eval(row), self.right.eval(row)
        return None if a is None or b is None else _ARITH[self.op](a, b)

    @override
    def columns(self) -> set[str]:
        return self.left.columns() | self.right.columns()

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"


def col(name: str) -> Col:
    """Return an expression that reads column ``name``.

    :param name: the column, qualified (``"u.age"``) or not (``"age"``).
    :return: the column expression.
    """
    return Col(name)


def lit(value: Value | None) -> Const:
    """Return a constant expression.

    :param value: the constant; ``None`` is NULL.
    :return: the constant expression.
    """
    return Const(value)


def conjuncts(predicate: Expr) -> list[Expr]:
    """Split a condition on its top-level ANDs.

    >>> conjuncts((col("a") == 1) & (col("b") == 2) & (col("c") == 3))
    [(a = 1), (b = 2), (c = 3)]

    :param predicate: the condition.
    :return: the parts which must all be true.
    """
    if isinstance(predicate, And):
        return [c for item in predicate.items for c in conjuncts(item)]
    return [predicate]
