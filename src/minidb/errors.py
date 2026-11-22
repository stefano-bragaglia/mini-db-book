"""Define the exceptions that minidb raises on purpose."""


class DatabaseError(Exception):
    """Signal any error that minidb raises deliberately.

    Catching it catches everything the database rejected, but none of the
    application's own bugs.
    """


class SchemaError(DatabaseError):
    """Signal that a table or column doesn't exist, or a definition is invalid."""


class ConstraintError(DatabaseError):
    """Signal that data was rejected because it breaks a rule of the schema."""


class DomainError(ConstraintError):
    """Signal that a value doesn't belong to its column's type (domain)."""


class NotNullError(ConstraintError):
    """Signal that a NOT NULL column received NULL."""


class CheckError(ConstraintError):
    """Signal that a CHECK constraint evaluated to false."""


class UniqueError(ConstraintError):
    """Signal that a PRIMARY KEY or UNIQUE constraint would be violated."""


class ForeignKeyError(ConstraintError):
    """Signal a reference to a missing row, or a delete that would orphan rows."""


class ConflictError(DatabaseError):
    """Signal that a concurrent transaction changed something this one read; retry it."""


