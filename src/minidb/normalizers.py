"""Provide small value normalizers for ``Column(normalizers=...)``.

Every normalizer must be idempotent, ``f(f(x)) == f(x)``: rows are
re-normalized whenever they are updated, so a normalizer that isn't would
change data nobody touched. Normalizers leave non-text values alone, so any
of them can be put on any column.
"""

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from minidb.values import Value


def collapse_spaces(value: Value) -> Value:
    """Trim text and replace each run of whitespace with a single space.

    >>> collapse_spaces("  Ada   Lovelace ")
    'Ada Lovelace'

    :param value: the value to normalize.
    :return: the collapsed text, or ``value`` unchanged if it isn't text.
    """
    return " ".join(value.split()) if isinstance(value, str) else value


def lower(value: Value) -> Value:
    """Lower-case text.

    >>> lower("Ada@Example.ORG")
    'ada@example.org'

    :param value: the value to normalize.
    :return: the lower-cased text, or ``value`` unchanged if it isn't text.
    """
    return value.lower() if isinstance(value, str) else value


def nfc(value: Value) -> Value:
    """Convert text to Unicode normalization form NFC.

    Visually identical strings can be different sequences of code points;
    NFC picks one canonical sequence for each.

    >>> nfc("café") == "café"
    True

    :param value: the value to normalize.
    :return: the NFC form of the text, or ``value`` unchanged if it isn't text.
    """
    return unicodedata.normalize("NFC", value) if isinstance(value, str) else value


def strip(value: Value) -> Value:
    """Remove leading and trailing whitespace from text.

    >>> strip("  Ada ")
    'Ada'

    :param value: the value to normalize.
    :return: the stripped text, or ``value`` unchanged if it isn't text.
    """
    return value.strip() if isinstance(value, str) else value


def upper(value: Value) -> Value:
    """Upper-case text.

    :param value: the value to normalize.
    :return: the upper-cased text, or ``value`` unchanged if it isn't text.
    """
    return value.upper() if isinstance(value, str) else value
