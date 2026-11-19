"""Build a small relational database, one chapter at a time."""

from minidb import normalizers
from minidb.changes import Change
from minidb.database import Database
from minidb.errors import CheckError
from minidb.errors import ConstraintError
from minidb.errors import DatabaseError
from minidb.errors import DomainError
from minidb.errors import ForeignKeyError
from minidb.errors import NotNullError
from minidb.errors import SchemaError
from minidb.errors import UniqueError
from minidb.locks import FairRWLock
from minidb.operators import Avg
from minidb.operators import Count
from minidb.operators import Max
from minidb.operators import Min
from minidb.operators import Sum
from minidb.query import Query
from minidb.schema import Check
from minidb.schema import Column
from minidb.schema import ForeignKey
from minidb.schema import TableSchema
from minidb.types import Boolean
from minidb.types import Date
from minidb.types import Integer
from minidb.types import Numeric
from minidb.types import Real
from minidb.types import Text
from minidb.types import Timestamp
from minidb.uow import Record
from minidb.uow import TransactionError
from minidb.uow import UnitOfWork

__all__ = [
    "Avg",
    "Boolean",
    "Change",
    "Check",
    "CheckError",
    "Column",
    "ConstraintError",
    "Count",
    "Database",
    "DatabaseError",
    "Date",
    "DomainError",
    "FairRWLock",
    "ForeignKey",
    "ForeignKeyError",
    "Integer",
    "Max",
    "Min",
    "NotNullError",
    "Numeric",
    "Query",
    "Real",
    "Record",
    "SchemaError",
    "Sum",
    "TableSchema",
    "Text",
    "Timestamp",
    "TransactionError",
    "UniqueError",
    "UnitOfWork",
    "normalizers",
]


def main() -> None:
    print("Hello from minidb!")
