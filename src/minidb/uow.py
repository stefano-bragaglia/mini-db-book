"""Group writes into an all-or-nothing transaction: the Unit of Work."""

from typing import TYPE_CHECKING
from typing import Self

from minidb import changes as ch
from minidb.errors import DatabaseError

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping
    from types import TracebackType

    from minidb.changes import Change
    from minidb.database import Database
    from minidb.table import Where


class TransactionError(DatabaseError):
    """Signal that a unit of work was used in the wrong state, e.g. after commit."""


class UnitOfWork:
    """Record writes, and replay them all at commit, undoing them if one fails.

    Version 1: a command log plus an undo log. Nothing reaches the database
    until :meth:`commit`.

    :param db: the database to write to.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.state = "active"
        self._pending: list[Callable[[], list[Change]]] = []

    # -- recording -------------------------------------------------------------------
    def insert(self, table: str, values: Mapping[str, object]) -> None:
        """Record an insert, to be planned and applied at commit.

        :param table: the table's name.
        :param values: the new row's values, by column name.
        :raises TransactionError: if the unit of work is no longer active.
        """
        self._record(lambda: ch.plan_insert(self.db, table, values))

    def update(self, table: str, changes: Mapping[str, object], where: Where = None) -> None:
        """Record an update, to be planned and applied at commit.

        :param table: the table's name.
        :param changes: the new values, by column name.
        :param where: which rows change; ``None`` (the default) for all.
        :raises TransactionError: if the unit of work is no longer active.
        """
        self._record(lambda: ch.plan_update(self.db, table, changes, where))

    def delete(self, table: str, where: Where = None) -> None:
        """Record a delete, to be planned and applied at commit.

        :param table: the table's name.
        :param where: which rows go; ``None`` (the default) for all.
        :raises TransactionError: if the unit of work is no longer active.
        """
        self._record(lambda: ch.plan_delete(self.db, table, where))

    def _record(self, plan: Callable[[], list[Change]]) -> None:
        self._require_active()
        self._pending.append(plan)

    # -- finishing -------------------------------------------------------------------
    def commit(self) -> None:
        """Plan and apply every recorded operation, in order, or none of them.

        Each applied change is kept in an undo log. If any operation fails,
        the undo log is applied in reverse, with every change inverted, and
        the error is re-raised.

        :raises TransactionError: if the unit of work is no longer active.
        :raises DatabaseError: whatever made an operation fail.
        """
        self._require_active()
        undo: list[Change] = []
        try:
            for plan in self._pending:
                changes = plan()
                self.db.apply(changes)
                undo.extend(changes)
        except BaseException:
            self.db.apply([c.inverted() for c in reversed(undo)])
            self.state = "rolled back"
            raise
        self.state = "committed"

    def rollback(self) -> None:
        """Discard every recorded operation.

        :raises TransactionError: if the unit of work is no longer active.
        """
        self._require_active()
        self._pending.clear()
        self.state = "rolled back"

    def _require_active(self) -> None:
        if self.state != "active":
            raise TransactionError(f"unit of work is already {self.state}")

    # -- context manager: commit on success, roll back on error -------------------------
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        if self.state != "active":
            return
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
