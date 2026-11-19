"""Build a small relational database, one chapter at a time."""

from minidb import normalizers
from minidb.database import Database
from minidb.errors import CheckError
from minidb.errors import ConstraintError
from minidb.errors import DatabaseError
from minidb.errors import DomainError
from minidb.errors import NotNullError
from minidb.errors import SchemaError
from minidb.errors import UniqueError
from minidb.schema import Check
from minidb.schema import Column
from minidb.schema import TableSchema
from minidb.types import Boolean
from minidb.types import Date
from minidb.types import Integer
from minidb.types import Numeric
from minidb.types import Real
from minidb.types import Text
from minidb.types import Timestamp

__all__ = [
    "Boolean",
    "Check",
    "CheckError",
    "Column",
    "ConstraintError",
    "Database",
    "DatabaseError",
    "Date",
    "DomainError",
    "Integer",
    "NotNullError",
    "Numeric",
    "Real",
    "SchemaError",
    "TableSchema",
    "Text",
    "Timestamp",
    "UniqueError",
    "normalizers",
]


def main() -> None:
    print("Hello from minidb!")
