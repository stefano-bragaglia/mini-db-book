# src/minidb/types.py
"""Define column types: how each one normalizes and validates its values."""

import datetime as dt
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from decimal import InvalidOperation
from decimal import ROUND_HALF_EVEN
from typing import ClassVar
from typing import override

from minidb.errors import DomainError
from minidb.values import Value

_INT_RE = re.compile(r"[+-]?\d+")
_TRUE = frozenset({"true", "t", "yes", "y", "on", "1"})
_FALSE = frozenset({"false", "f", "no", "n", "off", "0"})


class Type[T: Value]:
    """Describe a column type: how to normalize its values, and which are valid.

    :meth:`normalize` turns an acceptable input into the one canonical value
    that is stored; :meth:`validate` checks that a value already is canonical
    and inside the type's domain. NULL (``None``) passes through both
    untouched: whether a column may hold NULL is a constraint, not a type.

    Subclasses set :attr:`exact_types`, override :meth:`coerce`, and extend
    :meth:`validate` with rules such as ranges and lengths.
    """

    exact_types: ClassVar[tuple[type, ...]] = ()

    def normalize(self, value: object) -> T | None:
        """Convert ``value`` to this type's canonical form.

        :param value: any input; ``None`` is returned unchanged.
        :return: the canonical value, or ``None``.
        :raises DomainError: if ``value`` can't be converted.
        """
        return None if value is None else self.coerce(value)

    def coerce(self, value: object) -> T:
        """Convert a non-NULL ``value``; subclasses override this.

        :param value: the input, never ``None``.
        :return: the canonical value.
        :raises DomainError: always, in the base class.
        """
        raise self.error(value)

    def validate(self, value: object) -> None:
        """Check that ``value`` is canonical and inside the domain.

        The check is on the *exact* Python type: ``bool`` is a subclass of
        ``int``, but ``True`` is not a valid integer.

        :param value: the value to check; ``None`` always passes.
        :raises DomainError: if the value is not valid.
        """
        if value is not None and type(value) not in self.exact_types:
            raise self.error(value)

    def error(self, value: object, reason: str = "") -> DomainError:
        """Build the error that rejects ``value``.

        :param value: the rejected value.
        :param reason: why it was rejected; empty by default.
        :return: an exception for the caller to raise.
        """
        return DomainError(f"{value!r} is not a valid {self!r}" + (f": {reason}" if reason else ""))


def _integral(value: object) -> int | None:
    """Return ``value`` as an int if it is a whole float or Decimal, or a numeric string."""
    match value:
        case float() if value.is_integer():
            return int(value)
        case Decimal() if value.is_finite() and value == value.to_integral_value():
            return int(value)
        case str() if _INT_RE.fullmatch(value.strip()):
            return int(value.strip())
        case _:
            return None


@dataclass(frozen=True)
class Integer(Type[int]):
    """Hold whole numbers, optionally between ``min`` and ``max``.

    >>> Integer(min=0).normalize(" 42 ")
    42

    :param min: the smallest valid value; ``None`` (the default) for no limit.
    :param max: the largest valid value; ``None`` (the default) for no limit.
    """

    min: int | None = None
    max: int | None = None
    exact_types: ClassVar[tuple[type, ...]] = (int,)

    @override
    def coerce(self, value: object) -> int:
        if isinstance(value, bool):
            raise self.error(value, "booleans are not integers")
        if isinstance(value, int):
            return value
        number = _integral(value)
        if number is None:
            raise self.error(value)
        return number

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, int):
            if self.min is not None and value < self.min:
                raise self.error(value, f"below minimum {self.min}")
            if self.max is not None and value > self.max:
                raise self.error(value, f"above maximum {self.max}")


@dataclass(frozen=True)
class Real(Type[float]):
    """Hold finite floating-point numbers; NaN and infinities are rejected.

    >>> Real().normalize("2.5")
    2.5
    """

    exact_types: ClassVar[tuple[type, ...]] = (float,)

    @override
    def coerce(self, value: object) -> float:
        if isinstance(value, bool):
            raise self.error(value, "booleans are not numbers")
        if isinstance(value, int | float | Decimal):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                raise self.error(value) from None
        raise self.error(value)

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, float) and not math.isfinite(value):
            raise self.error(value, "NaN and infinities are not allowed")


@dataclass(frozen=True)
class Text(Type[str]):
    """Hold strings, optionally no longer than ``max_length`` characters.

    >>> Text().normalize(42)
    Traceback (most recent call last):
      ...
    minidb.errors.DomainError: 42 is not a valid Text(max_length=None): no implicit conversion to text

    :param max_length: the longest valid string; ``None`` (the default) for no limit.
    """

    max_length: int | None = None
    exact_types: ClassVar[tuple[type, ...]] = (str,)

    @override
    def coerce(self, value: object) -> str:
        if not isinstance(value, str):
            raise self.error(value, "no implicit conversion to text")
        return value

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, str) and self.max_length is not None and len(value) > self.max_length:
            raise self.error(value, f"longer than {self.max_length} characters")


@dataclass(frozen=True)
class Boolean(Type[bool]):
    """Hold ``True`` or ``False``, accepting 0/1 and words such as "yes" and "off".

    >>> Boolean().normalize("Yes"), Boolean().normalize(0)
    (True, False)
    """

    exact_types: ClassVar[tuple[type, ...]] = (bool,)

    @override
    def coerce(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value in (0, 1):
            return value == 1
        word = value.strip().lower() if isinstance(value, str) else None
        if word in _TRUE or word in _FALSE:
            return word in _TRUE
        raise self.error(value)


def _to_decimal(value: object) -> Decimal | None:
    """Return ``value`` as a Decimal, or ``None`` if it isn't a number."""
    if isinstance(value, float):
        return Decimal(repr(value))  # 0.1 -> Decimal('0.1'), not its binary value
    if isinstance(value, int | Decimal) and not isinstance(value, bool):
        return Decimal(value)
    if isinstance(value, str):
        try:
            return Decimal(value.strip())
        except InvalidOperation:
            return None
    return None


@dataclass(frozen=True)
class Numeric(Type[Decimal]):
    """Hold exact decimals with ``precision`` digits, ``scale`` of them after the point.

    Values are rounded to ``scale`` places with banker's rounding.

    >>> Numeric(6, 2).normalize(0.1)
    Decimal('0.10')

    :param precision: the total number of digits; 18 by default.
    :param scale: the digits after the decimal point; 2 by default.
    :raises ValueError: unless ``0 <= scale <= precision``.
    """

    precision: int = 18
    scale: int = 2
    exact_types: ClassVar[tuple[type, ...]] = (Decimal,)

    def __post_init__(self) -> None:
        if not 0 <= self.scale <= self.precision:
            raise ValueError("need 0 <= scale <= precision")

    @override
    def coerce(self, value: object) -> Decimal:
        number = _to_decimal(value)
        if number is None:
            raise self.error(value)
        if not number.is_finite():
            raise self.error(value, "NaN and infinities are not allowed")
        return number.quantize(Decimal(1).scaleb(-self.scale), ROUND_HALF_EVEN)

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if not isinstance(value, Decimal):
            return
        if value.as_tuple().exponent != -self.scale:
            raise self.error(value, f"expected exactly {self.scale} decimal places")
        if max(value.adjusted() + 1, 0) > self.precision - self.scale:
            raise self.error(value, f"too many digits for NUMERIC({self.precision}, {self.scale})")


@dataclass(frozen=True)
class Date(Type[dt.date]):
    """Hold calendar dates, accepting ISO strings such as ``"2026-11-18"``.

    >>> Date().normalize("2026-11-18")
    datetime.date(2026, 11, 18)
    """

    exact_types: ClassVar[tuple[type, ...]] = (dt.date,)

    @override
    def coerce(self, value: object) -> dt.date:
        if isinstance(value, dt.datetime):
            raise self.error(value, "use .date() to drop the time explicitly")
        if isinstance(value, dt.date):
            return value
        if isinstance(value, str):
            try:
                return dt.date.fromisoformat(value.strip())
            except ValueError:
                raise self.error(value) from None
        raise self.error(value)


@dataclass(frozen=True)
class Timestamp(Type[dt.datetime]):
    """Hold points in time: all timezone-aware (stored in UTC), or all naive.

    Python refuses to compare aware and naive datetimes, so a column must
    pick one kind.

    >>> Timestamp().normalize("2026-11-18T10:00:00+01:00")
    datetime.datetime(2026, 11, 18, 9, 0, tzinfo=datetime.timezone.utc)

    :param with_timezone: whether values must be aware; ``True`` by default.
    """

    with_timezone: bool = True
    exact_types: ClassVar[tuple[type, ...]] = (dt.datetime,)

    @override
    def coerce(self, value: object) -> dt.datetime:
        stamp = self._parse(value)
        aware = stamp.utcoffset() is not None
        if self.with_timezone and not aware:
            raise self.error(value, "a timezone is required")
        if not self.with_timezone and aware:
            raise self.error(value, "timezone not allowed")
        return stamp.astimezone(dt.UTC) if aware else stamp

    def _parse(self, value: object) -> dt.datetime:
        if isinstance(value, dt.datetime):
            return value
        if isinstance(value, str):
            try:
                return dt.datetime.fromisoformat(value.strip())
            except ValueError:
                raise self.error(value) from None
        raise self.error(value)

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, dt.datetime) and self.with_timezone and value.utcoffset() != dt.timedelta(0):
            raise self.error(value, "must be stored in UTC")
