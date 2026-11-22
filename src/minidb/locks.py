"""Implement readers-writer locks: any number of readers, or exactly one writer."""

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING
from typing import Protocol
from typing import override

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import AbstractContextManager


class RWLock(Protocol):
    """Describe a readers-writer lock: shared mode for readers, exclusive for a writer."""

    def acquire_read(self) -> None:
        """Wait until the lock can be held in shared mode, and take it."""
        ...

    def release_read(self) -> None:
        """Release a shared hold."""
        ...

    def acquire_write(self) -> None:
        """Wait until the lock can be held exclusively, and take it."""
        ...

    def release_write(self) -> None:
        """Release the exclusive hold."""
        ...

    def read(self) -> AbstractContextManager[None]:
        """Return a context manager that holds the lock in shared mode."""
        ...

    def write(self) -> AbstractContextManager[None]:
        """Return a context manager that holds the lock exclusively."""
        ...


class RWLockBase:
    """Provide :meth:`read` and :meth:`write` on top of the four acquire/release methods.

    Subclasses implement the four methods; the context managers make sure
    every acquire is matched by a release, even when an exception escapes.
    """

    def acquire_read(self) -> None:
        """Wait until the lock can be held in shared mode, and take it."""
        raise NotImplementedError

    def release_read(self) -> None:
        """Release a shared hold."""
        raise NotImplementedError

    def acquire_write(self) -> None:
        """Wait until the lock can be held exclusively, and take it."""
        raise NotImplementedError

    def release_write(self) -> None:
        """Release the exclusive hold."""
        raise NotImplementedError

    @contextmanager
    def read(self) -> Iterator[None]:
        """Hold the lock in shared mode for the duration of a ``with`` block.

        :return: a context manager.
        """
        self.acquire_read()
        try:
            yield
        finally:
            self.release_read()

    @contextmanager
    def write(self) -> Iterator[None]:
        """Hold the lock exclusively for the duration of a ``with`` block.

        :return: a context manager.
        """
        self.acquire_write()
        try:
            yield
        finally:
            self.release_write()


class ReaderPreferringLock(RWLockBase):
    """Never make readers wait for waiting writers: Courtois et al.'s first problem.

    A steady stream of readers starves writers forever.
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._readers = 0
        self._writer = False

    @override
    def acquire_read(self) -> None:
        with self._cond:
            self._cond.wait_for(lambda: not self._writer)
            self._readers += 1

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    @override
    def acquire_write(self) -> None:
        with self._cond:
            self._cond.wait_for(lambda: not self._writer and self._readers == 0)
            self._writer = True

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._cond.notify_all()


class WriterPreferringLock(RWLockBase):
    """Make new readers wait while a writer waits: Courtois et al.'s second problem.

    A steady stream of writers starves readers forever.
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._readers = 0
        self._writer = False
        self._writers_waiting = 0

    @override
    def acquire_read(self) -> None:
        with self._cond:
            self._cond.wait_for(lambda: not self._writer and self._writers_waiting == 0)
            self._readers += 1

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    @override
    def acquire_write(self) -> None:
        with self._cond:
            self._writers_waiting += 1
            self._cond.wait_for(lambda: not self._writer and self._readers == 0)
            self._writers_waiting -= 1
            self._writer = True

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._cond.notify_all()


class FairRWLock(RWLockBase):
    """Admit requests strictly in arrival (ticket) order, so nobody starves.

    Consecutive readers are admitted together; a writer waits for the
    readers ahead of it to leave, and nobody behind it can overtake it.

    >>> lock = FairRWLock()
    >>> with lock.read(), lock.read():  # readers share
    ...     pass
    >>> with lock.write():
    ...     pass
    """

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._next_ticket = 0  # handed to the next arrival
        self._serving = 0  # ticket at the head of the queue
        self._readers = 0  # readers inside
        self._writer = False  # writer inside?

    def _take_ticket(self) -> int:
        ticket = self._next_ticket
        self._next_ticket += 1
        return ticket

    @override
    def acquire_read(self) -> None:
        with self._cond:
            ticket = self._take_ticket()
            self._cond.wait_for(lambda: self._serving == ticket and not self._writer)
            self._readers += 1
            self._serving += 1
            self._cond.notify_all()  # the next ticket may be a reader too

    @override
    def release_read(self) -> None:
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()  # a writer may be waiting at the head

    @override
    def acquire_write(self) -> None:
        with self._cond:
            ticket = self._take_ticket()
            self._cond.wait_for(lambda: self._serving == ticket and not self._writer and self._readers == 0)
            self._writer = True
            self._serving += 1

    @override
    def release_write(self) -> None:
        with self._cond:
            self._writer = False
            self._cond.notify_all()
