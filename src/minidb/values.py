"""Name the types of the values that tables hold."""
import datetime as dt
from decimal import Decimal
from typing import cast
from typing import Protocol
from typing import Self

type Value = bool | int | float | str | Decimal | dt.date | dt.datetime
type Row = dict[str, Value | None]


class Ordered(Protocol):
    """Describe values that can be ordered among themselves."""

    def __lt__(self, other: Self, /) -> bool: ...

    def __le__(self, other: Self, /) -> bool: ...

    def __gt__(self, other: Self, /) -> bool: ...

    def __ge__(self, other: Self, /) -> bool: ...


class Arithmetic(Protocol):
    """Describe values that support the four arithmetic operators among themselves."""

    def __add__(self, other: Self, /) -> Self: ...

    def __sub__(self, other: Self, /) -> Self: ...

    def __mul__(self, other: Self, /) -> Self: ...

    def __truediv__(self, other: Self, /) -> Self: ...


def ordered(value: Value | None) -> Ordered:
    """Return ``value``, typed as orderable.

    Values from one column share a Python type, so they can be compared;
    the type checker can't know that, and this function says so.

    :param value: a value from a column (or a constant of the column's type).
    :return: the same object.
    """
    return cast("Ordered", value)


def arithmetic(value: Value) -> Arithmetic:
    """Return ``value``, typed as supporting arithmetic; see :func:`ordered`.

    :param value: a numeric value.
    :return: the same object.
    """
    return cast("Arithmetic", value)
