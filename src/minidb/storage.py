"""Make data durable: pluggable formats, an atomic snapshot and a write-ahead log."""

import hashlib
import json
import os
import struct
import threading
import zlib
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Protocol
from typing import TypedDict
from typing import cast

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from io import BufferedRandom
    from io import BufferedWriter

    from minidb.schema import ForeignKey
    from minidb.schema import TableSchema
    from minidb.table import Table
    from minidb.values import Primitive
    from minidb.values import Row


class Format(Protocol):
    """Describe a file format: how to turn primitives into bytes, and back."""

    name: str
    suffix: str

    def dumps(self, obj: object) -> bytes:
        """Encode a structure of primitives (dicts, lists, strings, numbers, None)."""
        ...

    def loads(self, data: bytes) -> object:
        """Decode what :meth:`dumps` produced."""
        ...


class LogRecord(TypedDict):
    """Describe one commit in the write-ahead log."""

    seq: int
    changes: list[tuple[str, int, list[Primitive] | None]]  # (table, rowid, values or None)


class Snapshot(TypedDict):
    """Describe a snapshot: the whole database at one commit."""

    format: int
    fingerprint: str
    commit_seq: int
    tables: dict[str, TableData]


class TableData(TypedDict):
    """Describe one table in a snapshot."""

    next_rowid: int
    rows: list[tuple[int, list[Primitive]]]


_FRAME = struct.Struct(">II")  # payload length, crc32


def _frame_at(data: bytes, pos: int) -> bytes | None:
    """Return the payload of the intact frame at ``pos``, or ``None`` if there isn't one."""
    if pos + _FRAME.size > len(data):
        return None
    length, crc = _FRAME.unpack_from(data, pos)
    payload = data[pos + _FRAME.size : pos + _FRAME.size + length]
    if len(payload) < length or zlib.crc32(payload) != crc:
        return None  # torn write
    return payload


def decode_row(schema: TableSchema, values: Sequence[Primitive]) -> Row:
    """Decode what :func:`encode_row` produced, validating every value.

    :param schema: the row's table.
    :param values: one primitive per column.
    :return: the row.
    :raises ValueError: if the number of values is wrong.
    :raises DomainError: if a value is not valid for its column.
    """
    if len(values) != len(schema.columns):
        raise ValueError(f"{schema.name}: stored row has {len(values)} values")
    return {c.name: c.type.from_primitive(v) for c, v in zip(schema.columns, values, strict=True)}


def encode_row(schema: TableSchema, row: Row) -> list[Primitive]:
    """Encode a row as a list of primitives, in column order.

    :param schema: the row's table.
    :param row: the row.
    :return: one primitive per column.
    """
    return [c.type.to_primitive(row[c.name]) for c in schema.columns]


def schema_fingerprint(tables: Mapping[str, Table], foreign_keys: Sequence[ForeignKey]) -> str:
    """Hash everything declarative about a schema; checks and defaults are code, and left out.

    :param tables: the tables, by name.
    :param foreign_keys: the foreign keys between them.
    :return: a short hexadecimal digest.
    """
    parts: list[object] = []
    for name in sorted(tables):
        s = tables[name].schema
        parts.append((name, [(c.name, repr(c.type), c.nullable) for c in s.columns], s.primary_key, sorted(s.unique)))
    parts.append(sorted((fk.table, fk.columns, fk.ref_table, fk.ref_columns, fk.on_delete) for fk in foreign_keys))
    return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]


class JsonFormat:
    """Store primitives as compact UTF-8 JSON.

    >>> JsonFormat().loads(JsonFormat().dumps({"a": [1, None, "x"]}))
    {'a': [1, None, 'x']}
    """

    name = "json"
    suffix = ".json"

    def dumps(self, obj: object) -> bytes:
        """Encode ``obj`` as JSON; NaN and infinities are refused.

        :param obj: a structure of primitives.
        :return: the encoded bytes.
        :raises ValueError: if ``obj`` contains NaN or an infinity.
        """
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()

    def loads(self, data: bytes) -> object:
        """Decode JSON bytes.

        :param data: what :meth:`dumps` produced.
        :return: the decoded structure.
        :raises ValueError: if ``data`` is not valid JSON.
        """
        result: object = json.loads(data.decode())
        return result


class Storage:
    """Keep a database in a directory: ``snapshot<suffix>`` plus ``wal.log``.

    :param directory: where the files live; created if missing.
    :param fmt: the format of the snapshot and log payloads;
        ``None`` (the default) means :class:`JsonFormat`.
    :param sync: whether to ``fsync`` before reporting a write as done;
        ``True`` by default. ``False`` is faster but not crash-safe.
    """

    def __init__(self, directory: str | os.PathLike[str], fmt: Format | None = None, *, sync: bool = True) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.format: Format = fmt if fmt is not None else JsonFormat()
        self.sync = sync
        self.snapshot_path = self.dir / f"snapshot{self.format.suffix}"
        self.log_path = self.dir / "wal.log"
        self._latch = threading.Lock()  # serializes file operations
        self._log: BufferedWriter | None = None

    # -- snapshot ----------------------------------------------------------------------

    def read_snapshot(self) -> Snapshot | None:
        """Return the last snapshot, or ``None`` if there is none yet.

        :return: the snapshot, or ``None``.
        """
        if not self.snapshot_path.exists():
            return None
        return cast("Snapshot", self.format.loads(self.snapshot_path.read_bytes()))

    def write_snapshot(self, state: Snapshot) -> None:
        """Replace the snapshot atomically: write a temporary file, then rename it.

        :param state: the whole database.
        """
        tmp = self.snapshot_path.with_name(self.snapshot_path.name + ".tmp")
        with self._latch:
            with tmp.open("wb") as f:
                f.write(self.format.dumps(state))
                self._fsync(f)
            tmp.replace(self.snapshot_path)  # atomic switch
            self._fsync_dir()

    # -- log ------------------------------------------------------------------------------

    def append(self, record: LogRecord) -> None:
        """Append one framed record to the log, and make it durable.

        :param record: the commit to log.
        """
        payload = self.format.dumps(record)
        frame = _FRAME.pack(len(payload), zlib.crc32(payload)) + payload
        with self._latch:
            if self._log is None:
                self._log = self.log_path.open("ab")
            self._log.write(frame)
            self._fsync(self._log)

    def close(self) -> None:
        """Close the log file, if it is open."""
        with self._latch:
            if self._log is not None:
                self._log.close()
                self._log = None

    def read_log(self) -> Iterator[LogRecord]:
        """Yield the intact records, then cut off any torn or corrupt tail.

        :return: an iterator over the logged commits, oldest first.
        """
        if not self.log_path.exists():
            return
        data = self.log_path.read_bytes()
        pos = 0
        while (payload := _frame_at(data, pos)) is not None:
            yield cast("LogRecord", self.format.loads(payload))
            pos += _FRAME.size + len(payload)
        if pos < len(data):
            with self._latch, self.log_path.open("r+b") as f:
                f.truncate(pos)
                self._fsync(f)

    def truncate_log(self) -> None:
        """Empty the log, after a snapshot has made its records redundant."""
        with self._latch:
            if self._log is not None:
                self._log.close()
                self._log = None
            with self.log_path.open("wb") as f:
                self._fsync(f)

    # -- fsync helpers --------------------------------------------------------------------

    def _fsync(self, f: BufferedWriter | BufferedRandom) -> None:
        f.flush()
        if self.sync:
            os.fsync(f.fileno())

    def _fsync_dir(self) -> None:
        if not self.sync or os.name != "posix":
            return  # Windows can't open directories
        fd = os.open(self.dir, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
