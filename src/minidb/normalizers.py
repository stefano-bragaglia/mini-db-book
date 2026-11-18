"""Small value normalizers for Column(normalizers=...).

Every normalizer must be idempotent: f(f(x)) == f(x). Rows are re-normalized
whenever they are updated, so a non-idempotent normalizer would change data
that nobody touched.
"""
import unicodedata
from collections.abc import Callable

type Normalizer[T] = Callable[[T], T]


def strip(s: str) -> str:
    """Remove leading and trailing whitespace from a string.

    >>> strip("  hello world  ")
    'hello world'

    :param s: The input string.
    :return: The stripped string.
    """
    return s.strip()


def lower(s: str) -> str:
    """Convert a string to lowercase.

    >>> lower("Hello World!")
    'hello world!'

    Careful with lower. Lower-casing is fine for e-mail domains but technically
    wrong for the part before the @, which the standard allows to be case-sensitive.
    For caseless matching of natural-language text, str.casefold() is more
    correct than lower() ("Straße".casefold() == "strasse"). Normalisation is
    a policy, which is why it's per column and opt-in.

    :param s: The input string.
    :return: The lowercase string.
    """
    return s.lower()


def upper(s: str) -> str:
    """Convert a string to uppercase.

    >>> upper("Hello World!")
    'HELLO WORLD!'

    :param s: The input string.
    :return: The uppercase string.
    """
    return s.upper()


def collapse_spaces(s: str) -> str:
    """Collapse consecutive whitespace characters into a single space.

    Strips leading and trailing whitespace, and normalises internal runs
    of whitespace.

    >>> collapse_spaces('  Ada   Lovelace ')
    'Ada Lovelace'

    :param s: The input string to process.
    :return: The string with extra whitespace collapsed.
    """
    return " ".join(s.split())


def nfc(s: str) -> str:
    """Normalize the string `s` to its Unicode Normalisation Form C (NFC).

    NFC uses canonical composition, ensuring that characters like "é" are stored
    as a single precomposed code point (U+00E9) rather than a base character
    followed by a combining accent (U+0065 U+0301). This ensures that visually
    identical strings with different underlying byte sequences (such as precomposed
    'é' versus 'e' followed by a combining acute accent) compare as equal.

    >>> composed = "café"           # Single code point (U+00E9)
    >>> decomposed = "cafe\u0301"   # 'e' + combining acute accent (U+0301)
    >>> composed == decomposed
    False
    >>> nfc(decomposed) == composed
    True

    Text pasted from a macOS file name is often decomposed, whereas text typed
    on most keyboards is composed. Without NFC, a unique index on names would
    accept both "café" strings. The Unicode standard defines these
    normalisation forms in UAX #15.

    :param s: the input string to normalize
    :return: the NFC-normalized string
    """
    return unicodedata.normalize("NFC", s)
