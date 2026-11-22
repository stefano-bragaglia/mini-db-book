"""Measure how long a late reader and a late writer wait under each lock.

A stream of overlapping readers and two looping writers keep each lock busy
for one second; a quarter of the way in, one more reader and one more
writer arrive and time how long they wait.
"""

import threading
import time

from minidb.locks import FairRWLock
from minidb.locks import ReaderPreferringLock
from minidb.locks import RWLockBase
from minidb.locks import WriterPreferringLock

DURATION, HOLD = 1.0, 0.01


def probe(lock: RWLockBase, kind: str, waited: dict[str, float]) -> None:
    """Arrive late, and record how long it takes to get the lock.

    :param lock: the lock under test.
    :param kind: ``"reader"`` or ``"writer"``.
    :param waited: where to record the wait, in seconds.
    """
    time.sleep(DURATION / 4)
    t0 = time.perf_counter()
    with lock.read() if kind == "reader" else lock.write():
        waited[kind] = time.perf_counter() - t0


def reader_stream(lock: RWLockBase, stop: threading.Event, offset: float) -> None:
    """Hold the lock for reading, again and again, until ``stop`` is set.

    :param lock: the lock under test.
    :param stop: set when the experiment is over.
    :param offset: how long to wait before starting, to stagger readers.
    """
    time.sleep(offset)
    while not stop.is_set():
        with lock.read():
            time.sleep(HOLD)


def starvation_test(lock: RWLockBase) -> dict[str, float]:
    """Run the experiment on one lock.

    :param lock: the lock under test.
    :return: the late reader's and late writer's waits, in seconds.
    """
    stop, waited = threading.Event(), dict[str, float]()
    threads = [threading.Thread(target=reader_stream, args=(lock, stop, i * HOLD / 4)) for i in range(4)]
    threads += [threading.Thread(target=writer_stream, args=(lock, stop)) for _ in range(2)]
    threads += [threading.Thread(target=probe, args=(lock, k, waited)) for k in ("reader", "writer")]
    for t in threads:
        t.start()
    time.sleep(DURATION)
    stop.set()
    for t in threads:
        t.join()
    return waited


def writer_stream(lock: RWLockBase, stop: threading.Event) -> None:
    """Hold the lock for writing, briefly, again and again, until ``stop`` is set.

    :param lock: the lock under test.
    :param stop: set when the experiment is over.
    """
    while not stop.is_set():
        with lock.write():
            time.sleep(HOLD / 10)


def main() -> None:
    """Print a table of waits for the three locks."""
    print(f"{'lock':<24}{'reader waited':>15}{'writer waited':>15}")
    for cls in (ReaderPreferringLock, WriterPreferringLock, FairRWLock):
        w = starvation_test(cls())
        print(f"{cls.__name__:<24}{w['reader'] * 1000:>12.1f} ms{w['writer'] * 1000:>12.1f} ms")


if __name__ == "__main__":
    main()
