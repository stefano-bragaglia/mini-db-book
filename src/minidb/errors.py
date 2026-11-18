"""Exceptions raised by minidb."""


class DatabaseError(Exception):
    """Base class for every error minidb raises on purpose."""


class SchemaError(DatabaseError):
    """A table or column does not exist, or a definition is invalid."""
