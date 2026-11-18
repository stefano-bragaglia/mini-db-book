"""Exceptions raised by minidb."""


class DatabaseError(Exception):
    """Base class for every error minidb raises on purpose."""


class SchemaError(DatabaseError):
    """A table or column does not exist, or a definition is invalid."""


class ConstraintError(DatabaseError):
    """Data was rejected because it violates a rule of the schema."""


class DomainError(ConstraintError):
    """A value does not belong to its column's type (domain)."""
