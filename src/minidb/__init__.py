"""minidb: a small relational database, built in the book."""

from minidb.database import Database
from minidb.errors import DatabaseError
from minidb.errors import SchemaError

__all__ = ["Database", "DatabaseError", "SchemaError"]


def main() -> None:
    print("Hello from minidb!")
