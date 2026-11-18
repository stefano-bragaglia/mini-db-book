"""minidb: a small relational database, built in the book."""
from minidb import normalizers
from minidb.database import Database
from minidb.errors import ConstraintError
from minidb.errors import DatabaseError
from minidb.errors import DomainError
from minidb.errors import SchemaError
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
    "Database", "DatabaseError", "SchemaError", "ConstraintError", "DomainError",
    "Column", "TableSchema",
    "Integer", "Real", "Text", "Boolean", "Numeric", "Date", "Timestamp",
    "normalizers",
]


def main() -> None:
    print("Hello from minidb!")
