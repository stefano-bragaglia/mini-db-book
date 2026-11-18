"""Column types. Each type knows how to normalize and validate its values."""
import datetime as dt
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from decimal import InvalidOperation
from decimal import ROUND_HALF_EVEN
from typing import override

from minidb.errors import DomainError

_TRUE = {"true", "t", "yes", "y", "on", "1"}
_FALSE = {"false", "f", "no", "n", "off", "0"}

_INT_RE = re.compile(r"[+-]?\d+")


class Type:
    """Base class for column types.

    normalize(): turn an acceptable input into the canonical stored form.
    validate(): check that a value already is in canonical form.
    NULL (None) passes through both untouched; NOT NULL is a constraint,
    not a type (see Chapter 4).
    """
    exact_types: tuple[type, ...] = (object,)

    def normalize(self, value: object | None) -> object | None:
        """Turn an acceptable input into the canonical stored form.

        `None` is a valid value and its canonical form is `None`.

        :param value: the value to normalize, or `None`
        :return: the normalized value, or `None`
        """
        if value is None:
            return None
        return self._coerce(value)

    def _coerce(self, value: object) -> object:
        """Convert `value` to its canonical form or call self.reject(value).

        This method should be overridden by subclasses.
        `None` is not a coercible value.

        :param value: the value to coerce
        :return: the coerced value
        :raises DomainError: if `value` is not a valid
        """
        raise NotImplementedError()
        return value

    def validate(self, value: object | None) -> None:
        """Validate `value`, if it is not a valid."""
        if value is None:
            return
        if object not in self.exact_types and type(value) not in self.exact_types:
            self._reject(value)
        self._check(value)

    def _check(self, value: object) -> None:
        """Perform extra domain rules checks against `value`, such as ranges and lengths.

        :param value: the value to check
        :raises DomainError: if `value` is not a valid
        """
        raise NotImplementedError()

    def _reject(self, value: object, reason: str = "") -> None:
        """Reject `value` if it is not a valid.

        :param value: the value to reject
        :param reason: the optional reason of rejection
        :raises DomainError: if `value` is not a valid
        """
        raise DomainError(f"{value!r} is not a valid {self!r}"
                          + (f": {reason}" if reason else ""))


@dataclass(frozen=True)
class Integer(Type):
    min: int | None = None
    max: int | None = None
    exact_types = (int,)

    @override
    def _coerce(self, value: object | None) -> int | None:
        result = None
        match value:
            case bool():
                self._reject(value, "booleans are not integers")
            case int():
                result = value
            case float() if value.is_integer():
                result = int(value)
            case Decimal() if value.is_finite() and value == value.to_integral_value():
                result = int(value)
            case str() if _INT_RE.fullmatch(value.strip()):
                result = int(value.strip())
            case _:
                self._reject(value)
        return result

    @override
    def _check(self, value: object) -> None:
        if self.min is not None and value < self.min:
            self._reject(value, f"below minimum {self.min}")
        if self.max is not None and value > self.max:
            self._reject(value, f"above maximum {self.max}")


@dataclass(frozen=True)
class Real(Type):
    exact_types = (float,)

    @override
    def _coerce(self, value: object | None) -> float | None:
        result = None
        match value:
            case bool():
                self._reject(value, "booleans are not numbers")
            case int() | float() | Decimal():
                result = float(value)
            case str():
                try:
                    result = float(value.strip())
                except ValueError:
                    self._reject(value)
            case _:
                self._reject(value)
        return result

    @override
    def _check(self, value: object) -> None:
        if not math.isfinite(value):
            self._reject(value, "NaN and infinities are not allowed")


@dataclass(frozen=True)
class Text(Type):
    max_length: int | None = None
    exact_types = (str,)

    @override
    def _coerce(self, value: object | None) -> object | None:
        if not isinstance(value, str):
            self._reject(value, "no implicit conversion to text")
        return value

    @override
    def _check(self, value: object) -> None:
        if self.max_length is not None and len(value) > self.max_length:
            self._reject(value, f"longer than {self.max_length} characters")


@dataclass(frozen=True)
class Boolean(Type):
    exact_types = (bool,)

    @override
    def _coerce(self, value: object | None) -> object | None:
        result = None
        match value:
            case bool():
                result = value
            case 0 | 1:
                result = bool(value)
            case str() if value.strip().lower() in _TRUE:
                result = True
            case str() if value.strip().lower() in _FALSE:
                result = False
            case _:
                self._reject(value)
        return result


@dataclass(frozen=True)
class Numeric(Type):
    """Exact decimal with `precision` total digits, `scale` after the point."""

    precision: int = 18
    scale: int = 2
    exact_types = (Decimal,)

    def __post_init__(self):
        if not 0 <= self.scale <= self.precision:
            raise ValueError("need 0 <= scale <= precision")

    @override
    def _coerce(self, value: object | None) -> object | None:
        match value:
            case bool():
                self._reject(value)
            case float():
                value = Decimal(repr(value))  # 0.1 -> Decimal('0.1')
            case int() | Decimal():
                value = Decimal(value)
            case str():
                try:
                    value = Decimal(value.strip())
                except InvalidOperation:
                    self._reject(value)
            case _:
                self._reject(value)
        decimal_value: Decimal = value
        if not decimal_value.is_finite():
            self._reject(value, "NaN and infinities are not allowed")
        return decimal_value.quantize(Decimal(1).scaleb(-self.scale), ROUND_HALF_EVEN)

    @override
    def _check(self, value: object) -> None:
        decimal_value: Decimal = value
        if decimal_value.as_tuple().exponent != -self.scale:
            self._reject(value, f"expected exactly {self.scale} decimal places")
        digits_before_point = max(decimal_value.adjusted() + 1, 0)
        if digits_before_point > self.precision - self.scale:
            self._reject(value, f"too many digits for NUMERIC({self.precision}, {self.scale})")


@dataclass(frozen=True)
class Date(Type):
    exact_types = (dt.date,)

    @override
    def _coerce(self, value: object | None) -> object | None:
        result = None
        match value:
            case dt.datetime():
                self._reject(value, "use .date() to drop the time explicitly")
            case dt.date():
                result = value
            case str():
                try:
                    return dt.date.fromisoformat(value.strip())
                except ValueError:
                    self._reject(value)
            case _:
                self._reject(value)
        return result


@dataclass(frozen=True)
class Timestamp(Type):
    """A datetime. With with_timezone=True, values must be aware and are
    stored in UTC; otherwise they must be naive."""

    with_timezone: bool = True
    exact_types = (dt.datetime,)

    @override
    def _coerce(self, value: object | None) -> object | None:
        if isinstance(value, str):
            try:
                value = dt.datetime.fromisoformat(value.strip())
            except ValueError:
                self._reject(value)

        if not isinstance(value, dt.datetime):
            self._reject(value)

        datetime_value: dt.datetime = value
        aware = datetime_value.tzinfo is not None and datetime_value.utcoffset() is not None
        if self.with_timezone:
            if not aware:
                self._reject(value, "a timezone is required")
            return datetime_value.astimezone(dt.UTC)

        if aware:
            self._reject(value, "timezone not allowed")

        return datetime_value

    @override
    def _check(self, value: object) -> None:
        if self.with_timezone:
            datetime_value: dt.datetime = value
            if datetime_value.utcoffset() != dt.timedelta(0):
                self._reject(value, "must be stored in UTC")
