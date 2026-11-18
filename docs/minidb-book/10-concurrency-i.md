[🏠 Contents](index.md) · [← Previous: Chapter 9 — Unit of Work II](09-unit-of-work-ii.md)

# Chapter 10 — Concurrency I: Threads and One Big Lock

A database is shared. A web server handles many requests at once, each in its own thread, each with its own Unit of Work. In this chapter we break minidb with threads, look at *why* it breaks, and fix it in the simplest way that is actually correct: one lock for the whole database. The next two chapters make it fast.

## 10.1 Python threads in 2026

For most of Python's history, the **Global Interpreter Lock** (GIL) allowed only one thread to run Python bytecode at a time. Threads could interleave, but not run in parallel. CPython 3.13 shipped an experimental **free-threaded** build without the GIL ([PEP 703](references.md#pep703)). In Python 3.14 that build is officially supported ([PEP 779](references.md#pep779)), installed as `python3.14t`. You can check which one you're running:

```python
import sys
sys._is_gil_enabled()     # True on the default build, False on 3.14t
```

The free-threaded build changes *performance*, not *correctness*. Even with the GIL, the interpreter can switch threads between any two bytecodes. An operation like `self._next_rowid += 1` is several bytecodes: load, add, store. Two threads can both load 41, both store 42, and hand out the same rowid. The GIL makes such races *rarer*, which arguably makes them worse: they pass your tests and fail in production. Without the GIL they happen constantly.

## 10.2 Breaking minidb

Here are three experiments, run against the code from [Chapter 9](09-unit-of-work-ii.md). Their output is from a real run on both builds.

**Experiment 1: a lost update in the rowid counter.** Four threads each ask a table for 20,000 new rowids:

```python
def worker():
    for i in range(20_000):
        users.new_rowid()           # self._next_rowid += 1
```

```text
GIL enabled: True  | rowids handed out: 80000, counter is at: 80000
GIL enabled: False | rowids handed out: 80000, counter is at: 56019
```

With the GIL it happened to survive this run. Without it, about 24,000 increments were lost: tens of thousands of rowids were handed out twice.

**Experiment 2: reading during a write.** One thread inserts 20,000 users while another repeatedly counts them with a query:

```text
GIL enabled: True  | reader errors: 43
GIL enabled: False | reader errors: 18824
RuntimeError: dictionary changed size during iteration
```

`Scan` iterates over `table.rows` while `Table.put` adds to it. Python detects that and raises an exception, but only because the dict's *size* changed. An update that replaces a value isn't detected at all, and a scan can see some of a transaction's changes but not others.

**Experiment 3: duplicate primary keys.** Eight threads each try to insert ids 0–1999 into a table whose primary key is `id`, ignoring `UniqueViolation`:

```text
GIL True  rows: 2002 distinct ids: 2000
GIL False rows: 2040 distinct ids: 2000
```

**This happens even with the GIL.** Two Units of Work each checked "is `id = 17` free?" in their private workspace, both saw yes, and both committed. Nothing in the data structures broke; every dict operation was individually fine. The *logic* broke: each transaction made a decision based on a read that was no longer true when it wrote. This is the **check-then-act** race, and it has a name in database theory: a violation of **isolation**.

You don't need threads to see it. One thread is enough, with two interleaved Units of Work:

```python
u1, u2 = db.unit_of_work(), db.unit_of_work()
u1.insert("users", {"id": 5})       # checks: 5 is free
u2.insert("users", {"id": 5})       # checks: 5 is free (u1 hasn't committed)
u1.commit()
u2.commit()                         # duplicate key: the unique index now holds two rowids for 5
```

## 10.3 Two kinds of protection

The experiments show two different problems, and databases use two different words for the cures:

| | Problem | Cure (database jargon) |
|---|---|---|
| Experiments 1, 2 | Concurrent access corrupts a *data structure* (counter, dict, index) | **Latch**: a short-term mutex held for the duration of one operation |
| Experiment 3 | Concurrent *transactions* make decisions on stale data | **Lock** (or validation): isolation for the duration of a transaction |

The distinction matters in real systems: latches are cheap and held for microseconds, while locks can be held for seconds and need deadlock handling ([Graefe 2010](references.md#graefe2010)). In this chapter we use one mechanism for both. That's simple and correct, but heavy. [Chapter 12](12-isolation.md) separates them.

## 10.4 One big lock

Our fix: the database owns one `threading.Lock`.

- **A Unit of Work holds the lock for its whole life**, from creation to commit or rollback. While it runs, no other transaction can read or write anything, so its checks can't go stale.
- **Reads outside a transaction** (`db.select`, `db.get`, `db.query(...).all()`) take the lock for the duration of the read.

This is **serial execution**: transactions run one after another. It's trivially correct: whatever each transaction does alone, it does the same when run "concurrently". Some real systems use it on purpose. VoltDB and Redis both execute operations serially on each partition, because when every transaction is in memory and short, the lock is rarely contended.

Two traps need closing.

**Nested transactions in one thread.** If thread T holds the lock in a Unit of Work and then calls `db.insert(...)`, which opens a *second* Unit of Work, then with a re-entrant lock (`RLock`) T would get in, and we'd have the interleaved-transactions bug from §10.2 again. With a plain `Lock`, T would wait for itself forever. We do better than both: the database remembers each thread's active Unit of Work in a `threading.local()` and refuses nested ones with a clear error.

**Lazy queries.** `Query.__iter__` was a lazy generator. If it takes the lock, when would it release it? After the last row, unless the caller stops iterating early. Then the lock is held until the generator is garbage collected. **A lock must never be held across a `yield` that hands control to code you don't control.** Queries therefore materialize their results under the lock, and iteration walks the finished list.

### The code

```python
# minidb/database.py (imports)
import threading
from contextlib import contextmanager
from minidb.uow import TransactionError
```

```python
# minidb/database.py (replace Database.__init__)
    def __init__(self):
        self.tables: dict[str, Table] = {}
        self.foreign_keys: list[ForeignKey] = []
        self._lock = threading.Lock()
        self._local = threading.local()         # .uow: this thread's active UoW
```

```python
# minidb/database.py (add to Database)
    # -- concurrency control ------------------------------------------------------------
    def _active_uow(self):
        return getattr(self._local, "uow", None)

    def _begin(self, uow) -> None:
        """Called by a new UnitOfWork: wait for exclusive access."""
        if self._active_uow() is not None:
            raise TransactionError("this thread already has an active unit of work")
        self._lock.acquire()
        self._local.uow = uow

    def _end(self, uow) -> None:
        """Called when a UnitOfWork commits or rolls back."""
        self._local.uow = None
        self._lock.release()

    @contextmanager
    def reading(self):
        """Hold the lock for one read outside any unit of work."""
        if self._active_uow() is not None:
            raise TransactionError("inside a unit of work, read through the unit of work")
        with self._lock:
            yield self
```

```python
# minidb/database.py (replace Database.get)
    def get(self, table: str, rowid: int) -> Row | None:
        with self.reading():
            return self.table(table).get(rowid)
```

```python
# minidb/database.py (replace Database.select)
    def select(self, table: str, where: Where = None) -> list[Row]:
        with self.reading():
            return self.table(table).select(where)
```

The Unit of Work calls `_begin` as the last step of `__init__` (so a failure to start leaves nothing half-built) and `_end` when it finishes. It also provides its own `reading()`, which does nothing: a Unit of Work already holds the lock.

```python
# minidb/uow.py (replace UnitOfWork.__init__)
    def __init__(self, db, *, deferred: bool = False):
        self.db = db
        self.deferred = deferred
        self.state = "active"
        self._views: dict[str, TableView] = {}
        self._changes: list[Change] = []
        self._identity: dict[tuple[str, int], Record] = {}
        self._snapshots: dict[tuple[str, int], Row] = {}
        db._begin(self)
```

```python
# minidb/uow.py (replace UnitOfWork.commit)
    def commit(self) -> None:
        self._require_active()
        self.flush()
        if self.deferred:
            ch.check_deferred(self, self._changes)
        self.db.apply(ch.net_changes(self._changes))
        self.state = "committed"
        self.db._end(self)
```

```python
# minidb/uow.py (replace UnitOfWork.rollback)
    def rollback(self) -> None:
        self._require_active()
        self._views.clear()
        self._changes.clear()
        self._identity.clear()
        self.state = "rolled back"
        self.db._end(self)
```

```python
# minidb/uow.py (add to UnitOfWork)
    def reading(self):
        return nullcontext(self)                # we already hold the lock
```

```python
# minidb/uow.py (imports)
from contextlib import nullcontext
```

If `commit` raises, say from a deferred constraint, the Unit of Work stays active and keeps the lock. The caller can fix things and commit again, or roll back. Inside a `with` block that happens automatically: the exception reaches `__exit__`, which rolls back.

Queries materialize under the state's `reading()`:

```python
# minidb/query.py (replace Query.__iter__)
    def __iter__(self) -> Iterator[Row]:
        with self._db.reading():
            rows = list(self.plan())          # materialize while protected
        return iter(rows)
```

```python
# minidb/query.py (replace Query.all)
    def all(self) -> list[dict]:
        with self._db.reading():
            return [dict(row) for row in self.plan()]
```

```python
# minidb/query.py (replace Query.first)
    def first(self) -> dict | None:
        rows = self.limit(1).all()
        return rows[0] if rows else None
```

## 10.5 Checking the fix

The single-thread interleaving is now refused:

```python
>>> from minidb import *
>>> db = Database()
>>> _ = db.create_table("users", [Column("id", Integer())], primary_key="id")
>>> u1 = db.unit_of_work()
>>> u2 = db.unit_of_work()
Traceback (most recent call last):
  ...
minidb.uow.TransactionError: this thread already has an active unit of work
>>> db.insert("users", {"id": 1})                  # also a nested unit of work
Traceback (most recent call last):
  ...
minidb.uow.TransactionError: this thread already has an active unit of work
>>> u1.rollback()
```

With two threads, the second transaction waits for the first, and its uniqueness check sees the first one's committed row:

```python
>>> import threading
>>> inside = threading.Event()
>>> results = []
>>> def first():
...     with db.unit_of_work() as uow:
...         uow.insert("users", {"id": 5})
...         inside.set()                            # let the second thread try
...         threading.Event().wait(0.2)             # ...while we still hold the lock
>>> def second():
...     inside.wait()
...     try:
...         db.insert("users", {"id": 5})
...     except UniqueViolation as e:
...         results.append("second: " + str(e))
>>> threads = [threading.Thread(target=first), threading.Thread(target=second)]
>>> for t in threads: t.start()
>>> for t in threads: t.join()
>>> results
['second: users: duplicate key (id=5)']
```

And a stress test: the three experiments again, plus an invariant check. Concurrent money transfers must never create or destroy money.

```python
# run
import random, sys, threading
from minidb import *

db = Database()
db.create_table("accounts", [Column("id", Integer()), Column("balance", Integer(min=0))],
                primary_key="id")
for i in range(10):
    db.insert("accounts", {"id": i, "balance": 1000})

def transfer(seed):
    rnd = random.Random(seed)
    for _ in range(500):
        a, b = rnd.sample(range(10), 2)
        amount = rnd.randint(1, 100)
        try:
            with db.unit_of_work() as uow:
                src, dst = uow.find("accounts", {"id": a})[0], uow.find("accounts", {"id": b})[0]
                src["balance"] -= amount            # DomainError if it would go negative
                dst["balance"] += amount
        except DomainError:
            pass

def auditor(stop, problems):
    while not stop.is_set():
        total = db.query("accounts").group_by(total=Sum("balance")).first()["total"]
        if total != 10_000:
            problems.append(total)

stop, problems = threading.Event(), []
workers = [threading.Thread(target=transfer, args=(s,)) for s in range(8)]
audit = threading.Thread(target=auditor, args=(stop, problems))
audit.start()
for w in workers: w.start()
for w in workers: w.join()
stop.set(); audit.join()

final = sum(r["balance"] for r in db.select("accounts"))
print(f"GIL={sys._is_gil_enabled()} final total={final} audit problems={len(problems)}")
assert final == 10_000 and not problems
```

```text
GIL=True final total=10000 audit problems=0
GIL=False final total=10000 audit problems=0
```

The auditor never sees money in flight, because a query can't run while a transfer holds the lock.

## 10.6 The price of one big lock

Correct, yes. But look at what the lock serializes:

1. **Readers block readers.** Ten threads running reports take turns, even though none of them changes anything. On the free-threaded build that wastes every core but one.
2. **A slow transaction blocks everyone.** A Unit of Work that does a network call between two writes holds the whole database for the duration.
3. **A forgotten transaction blocks everyone forever.** Create a Unit of Work, never finish it, and every other thread waits indefinitely.

Problem 1 is solved by noticing that reads don't conflict with reads: a **readers–writer lock**, the subject of [Chapter 11](11-readers-writer-locks.md). Problems 2 and 3 are solved by not holding any lock during the transaction at all, and checking at commit that nothing it read has changed: **optimistic concurrency control**, in [Chapter 12](12-isolation.md).

## Questions and exercises

1. Explain, bytecode by bytecode, how `self._next_rowid += 1` loses an update. (`import dis; dis.dis(Table.new_rowid)` shows the bytecode.)
2. Why is Experiment 3 *not* fixed by making every `Table` method thread-safe with its own lock? Which property of a transaction needs a lock that spans several methods?
3. Add a `lock_timeout` parameter to `Database`: if a Unit of Work can't get the lock within that many seconds, raise `TransactionError`. Which of the three problems in §10.6 does this solve, and which does it only turn into an error?
4. A thread starts a Unit of Work and then crashes with an unhandled exception *outside* a `with` block. What happens to the lock? How would you detect such abandoned transactions? (Python's `weakref.finalize` may help, but read its caveats.)
5. Why does `Database.reading()` refuse to run when the thread has an active Unit of Work, instead of just reading? What would a read from the *database* (not the Unit of Work) show in that situation?
6. *(Thought experiment)* Our `Query.all()` materializes everything. A query over 10 million rows now needs 10 million dicts in memory. How do real databases stream results to clients without holding locks forever? (Hint: look up *cursors* and *MVCC*.)
7. *(Measure)* On a free-threaded build, run four threads each doing a 100,000-row aggregate query, first through `db.query` (lock held) and then directly via the operators with no lock. Compare wall-clock times. You'll redo this experiment in [Chapter 11](11-readers-writer-locks.md).

---

[🏠 Contents](index.md) · [Next: Chapter 11 — Readers–Writer Locks →](11-readers-writer-locks.md)
