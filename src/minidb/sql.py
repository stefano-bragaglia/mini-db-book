"""Run a useful subset of SQL, compiled onto minidb's own API.

The module has four parts: a tokenizer, syntax-tree dataclasses, a parser
(recursive descent, with precedence climbing for expressions), and a
:class:`Connection` that compiles each statement and runs it.
"""

import re
from dataclasses import dataclass
from dataclasses import field
from decimal import Decimal
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Literal
from typing import override

from minidb.errors import DatabaseError
from minidb.expr import And
from minidb.expr import Arith
from minidb.expr import Col
from minidb.expr import Compare
from minidb.expr import Const
from minidb.expr import Expr
from minidb.expr import In
from minidb.expr import IsNull
from minidb.expr import Not
from minidb.expr import Or
from minidb.operators import Avg
from minidb.operators import Count
from minidb.operators import Max
from minidb.operators import Min
from minidb.operators import Sum
from minidb.schema import Check
from minidb.schema import Column
from minidb.schema import ForeignKey
from minidb.types import Boolean
from minidb.types import Date
from minidb.types import Integer
from minidb.types import Numeric
from minidb.types import Real
from minidb.types import Text
from minidb.types import Timestamp

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence

    from minidb.database import Database
    from minidb.expr import ArithOp
    from minidb.expr import CompareOp
    from minidb.operators import Accumulator
    from minidb.operators import AggregateFunction
    from minidb.operators import JoinKind
    from minidb.operators import RowFunction
    from minidb.query import Query
    from minidb.schema import OnDelete
    from minidb.types import Type
    from minidb.uow import UnitOfWork
    from minidb.values import Value

type Result = list[dict[str, Value | None]] | int | None


class SQLError(DatabaseError):
    """Signal SQL text that can't be parsed or compiled."""


# -- 1. tokens ------------------------------------------------------------------------------
KEYWORDS = frozenset(
    {
        "SELECT",
        "DISTINCT",
        "FROM",
        "AS",
        "JOIN",
        "INNER",
        "LEFT",
        "OUTER",
        "ON",
        "WHERE",
        "GROUP",
        "BY",
        "HAVING",
        "ORDER",
        "ASC",
        "DESC",
        "LIMIT",
        "OFFSET",
        "AND",
        "OR",
        "NOT",
        "IS",
        "NULL",
        "IN",
        "TRUE",
        "FALSE",
        "INSERT",
        "INTO",
        "VALUES",
        "UPDATE",
        "SET",
        "DELETE",
        "CREATE",
        "TABLE",
        "INDEX",
        "UNIQUE",
        "PRIMARY",
        "KEY",
        "DEFAULT",
        "REFERENCES",
        "CHECK",
        "CASCADE",
        "RESTRICT",
        "USING",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
    }
)

_TOKEN = re.compile(
    r"""
      (?P<space>\s+|--[^\n]*)
    | (?P<number>\d+\.\d*|\.\d+|\d+)
    | (?P<string>'(?:[^']|'')*')
    | (?P<name>[A-Za-z_][A-Za-z_0-9]*)
    | (?P<quoted>"(?:[^"]|"")+")
    | (?P<op><=|>=|<>|!=|[=<>(),.*+\-/;?])
    """,
    re.VERBOSE,
)

type TokenKind = Literal["number", "string", "name", "keyword", "op", "end"]
type TokenValue = int | Decimal | str | None


@dataclass(frozen=True)
class Token:
    """Hold one token: its kind, its value and where it starts in the text.

    :param kind: one of ``number string name keyword op end``.
    :param value: the number, the unquoted string or name, the upper-cased
        keyword, or the operator; ``None`` for the end.
    :param pos: the offset of its first character.
    """

    kind: TokenKind
    value: TokenValue
    pos: int


def _name_token(text: str, pos: int) -> Token:
    upper = text.upper()
    return Token("keyword", upper, pos) if upper in KEYWORDS else Token("name", text, pos)


_MAKERS: dict[str, Callable[[str, int], Token | None]] = {
    "space": lambda _text, _pos: None,
    "number": lambda text, pos: Token("number", Decimal(text) if "." in text else int(text), pos),
    "string": lambda text, pos: Token("string", text[1:-1].replace("''", "'"), pos),
    "name": _name_token,
    "quoted": lambda text, pos: Token("name", text[1:-1].replace('""', '"'), pos),
    "op": lambda text, pos: Token("op", "!=" if text == "<>" else text, pos),
}


def tokenize(sql: str) -> list[Token]:
    """Split SQL text into tokens, ending with an ``end`` token.

    >>> [t.value for t in tokenize("SELECT name FROM users WHERE age >= 3.5")]
    ['SELECT', 'name', 'FROM', 'users', 'WHERE', 'age', '>=', Decimal('3.5'), None]

    :param sql: the text.
    :return: the tokens.
    :raises SQLError: on a character that starts no token.
    """
    tokens: list[Token] = []
    pos = 0
    while pos < len(sql):
        m = _TOKEN.match(sql, pos)
        if m is None or m.lastgroup is None:
            raise SQLError(f"unexpected character {sql[pos]!r} at position {pos}")
        token = _MAKERS[m.lastgroup](m.group(), pos)
        if token is not None:
            tokens.append(token)
        pos = m.end()
    tokens.append(Token("end", None, pos))
    return tokens


# -- 2. syntax tree -----------------------------------------------------------------------------
@dataclass(eq=False, repr=False)  # keep Expr's == (it builds a Compare) and its repr
class AggCall(Expr):
    """Stand for ``COUNT(*)``, ``SUM(x)`` and so on inside an expression.

    Grouping computes each aggregate under its :attr:`key`, so evaluating the
    call afterwards just reads that column.

    :param func: the aggregate's name, upper-cased.
    :param column: its column, or ``None`` for ``*``.
    """

    func: str
    column: str | None

    @property
    def key(self) -> str:
        """Return the output column the aggregate is computed into, e.g. ``"SUM(o.total)"``."""
        return f"{self.func}({self.column or '*'})"

    @override
    def eval(self, row: Mapping[str, Value | None]) -> Value | None:
        return row[self.key]

    def __repr__(self) -> str:
        return self.key


@dataclass
class Select:
    """Hold a parsed ``SELECT``; ``items`` is ``None`` for ``SELECT *``."""

    items: list[tuple[Expr, str | None]] | None
    distinct: bool
    table: tuple[str, str | None]
    joins: list[tuple[str, str | None, Expr, JoinKind]]
    where: Expr | None
    group_by: list[str]
    having: Expr | None
    order_by: list[tuple[Expr, bool]]
    limit: int | None
    offset: int


@dataclass
class Insert:
    """Hold a parsed ``INSERT``; ``columns`` is ``None`` for all, in order."""

    table: str
    columns: list[str] | None
    rows: list[list[Value | None]]


@dataclass
class Update:
    """Hold a parsed ``UPDATE``."""

    table: str
    assignments: dict[str, Expr]
    where: Expr | None


@dataclass
class Delete:
    """Hold a parsed ``DELETE``."""

    table: str
    where: Expr | None


@dataclass
class CreateTable:
    """Hold a parsed ``CREATE TABLE``."""

    name: str
    columns: list[Column] = field(default_factory=list[Column])
    primary_key: tuple[str, ...] = ()
    unique: list[tuple[str, ...]] = field(default_factory=list[tuple[str, ...]])
    checks: list[Expr] = field(default_factory=list[Expr])
    foreign_keys: list[ForeignKey] = field(default_factory=list[ForeignKey])


@dataclass
class CreateIndex:
    """Hold a parsed ``CREATE INDEX``."""

    name: str
    table: str
    columns: list[str]
    unique: bool
    kind: str


@dataclass
class TransactionControl:
    """Hold ``BEGIN``, ``COMMIT`` or ``ROLLBACK``."""

    action: str


type Statement = Select | Insert | Update | Delete | CreateTable | CreateIndex | TransactionControl


@dataclass
class _ColumnOptions:
    nullable: bool = True
    default: Value | None = None


AGGREGATES: dict[str, Callable[[str | None], AggregateFunction[Accumulator]]] = {
    "COUNT": Count,
    "SUM": Sum,
    "AVG": Avg,
    "MIN": Min,
    "MAX": Max,
}

_TYPES: dict[str, Callable[[list[int]], Type[Value]]] = {
    "INT": lambda _: Integer(),
    "INTEGER": lambda _: Integer(),
    "BIGINT": lambda _: Integer(),
    "REAL": lambda _: Real(),
    "FLOAT": lambda _: Real(),
    "DOUBLE": lambda _: Real(),
    "TEXT": lambda args: Text(*args[:1]),
    "VARCHAR": lambda args: Text(*args[:1]),
    "CHAR": lambda args: Text(*args[:1]),
    "BOOL": lambda _: Boolean(),
    "BOOLEAN": lambda _: Boolean(),
    "NUMERIC": lambda args: Numeric(*args[:2]),
    "DECIMAL": lambda args: Numeric(*args[:2]),
    "DATE": lambda _: Date(),
    "TIMESTAMP": lambda _: Timestamp(),
}

_ON_DELETE: dict[str, OnDelete] = {"CASCADE": "cascade", "SET": "set null", "RESTRICT": "restrict"}


# -- 3. the parser ----------------------------------------------------------------------------
class Parser:
    """Parse one SQL statement: recursive descent, with precedence climbing for expressions.

    >>> Parser("SELECT name FROM users WHERE age > ?", [40]).statement().where
    (age > 40)

    :param sql: the statement's text.
    :param params: the values for the ``?`` placeholders, in order; none by default.
    """

    # binding power of each infix operator: higher binds tighter
    INFIX: ClassVar[dict[str, int]] = {
        "OR": 10,
        "AND": 20,
        "=": 40,
        "!=": 40,
        "<": 40,
        "<=": 40,
        ">": 40,
        ">=": 40,
        "IS": 40,
        "IN": 40,
        "NOT": 40,
        "+": 50,
        "-": 50,
        "*": 60,
        "/": 60,
    }

    def __init__(self, sql: str, params: Sequence[Value | None] = ()) -> None:
        self.tokens = tokenize(sql)
        self.i = 0
        self.params = list(params)
        self.used_params = 0

    # -- token helpers ------------------------------------------------------------------
    def peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[min(self.i, len(self.tokens) - 1)]

    def next(self) -> Token:
        """Consume and return the current token."""
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, *values: str) -> Token | None:
        """Consume the current token if it is one of these keywords or operators.

        :param values: the acceptable keywords and operators.
        :return: the token, or ``None`` if it didn't match (and wasn't consumed).
        """
        tok = self.peek()
        if tok.kind in ("keyword", "op") and tok.value in values:
            self.i += 1
            return tok
        return None

    def expect(self, *values: str) -> Token:
        """Consume the current token, which must be one of these keywords or operators.

        :param values: the acceptable keywords and operators.
        :return: the token.
        :raises SQLError: if it is something else.
        """
        tok = self.accept(*values)
        if tok is None:
            got = self.peek()
            raise SQLError(f"expected {' or '.join(values)} at position {got.pos}, got {got.value!r}")
        return tok

    def name(self) -> str:
        """Consume a name.

        :return: the name.
        :raises SQLError: if the current token is not a name.
        """
        tok = self.next()
        if tok.kind != "name" or not isinstance(tok.value, str):
            raise SQLError(f"expected a name at position {tok.pos}, got {tok.value!r}")
        return tok.value

    def name_list(self) -> list[str]:
        """Consume ``(name, name, ...)``.

        :return: the names.
        """
        self.expect("(")
        names = [self.name()]
        while self.accept(","):
            names.append(self.name())
        self.expect(")")
        return names

    # -- statements -----------------------------------------------------------------------
    def statement(self) -> Statement:
        """Parse the whole text as one statement, optionally ending with ``;``.

        :return: the statement's syntax tree.
        :raises SQLError: if the text isn't one valid statement, or the
            number of parameters doesn't match the placeholders.
        """
        tok = self.peek()
        handlers: dict[TokenValue, Callable[[], Statement]] = {
            "SELECT": self.select,
            "INSERT": self.insert,
            "UPDATE": self.update,
            "DELETE": self.delete,
            "CREATE": self.create,
            "BEGIN": self.transaction,
            "COMMIT": self.transaction,
            "ROLLBACK": self.transaction,
        }
        handler = handlers.get(tok.value) if tok.kind == "keyword" else None
        if handler is None:
            raise SQLError(f"expected a statement at position {tok.pos}")
        stmt = handler()
        self.accept(";")
        if self.peek().kind != "end":
            raise SQLError(f"unexpected {self.peek().value!r} at position {self.peek().pos}")
        if self.used_params != len(self.params):
            raise SQLError(f"{len(self.params)} parameters given, {self.used_params} used")
        return stmt

    def transaction(self) -> TransactionControl:
        """Parse ``BEGIN``, ``COMMIT`` or ``ROLLBACK``."""
        return TransactionControl(str(self.next().value))

    def select(self) -> Select:
        """Parse a ``SELECT`` statement, clause by clause."""
        self.expect("SELECT")
        distinct = self.accept("DISTINCT") is not None
        items = None if self.accept("*") else self._items()
        self.expect("FROM")
        table = self.table_ref()
        joins = self._joins()
        where = self.expr() if self.accept("WHERE") else None
        group_by = self._group_by()
        having = self.expr() if self.accept("HAVING") else None
        order_by = self._order_by()
        limit, offset = self._limit()
        return Select(items, distinct, table, joins, where, group_by, having, order_by, limit, offset)

    def _items(self) -> list[tuple[Expr, str | None]]:
        items = [self._item()]
        while self.accept(","):
            items.append(self._item())
        return items

    def _item(self) -> tuple[Expr, str | None]:
        e = self.expr()
        if self.accept("AS") or self.peek().kind == "name":
            return e, self.name()
        return e, None

    def _joins(self) -> list[tuple[str, str | None, Expr, JoinKind]]:
        joins: list[tuple[str, str | None, Expr, JoinKind]] = []
        while (kind := self._join_kind()) is not None:
            name, alias = self.table_ref()
            self.expect("ON")
            joins.append((name, alias, self.expr(), kind))
        return joins

    def _join_kind(self) -> JoinKind | None:
        if self.accept("JOIN") or (self.accept("INNER") and self.expect("JOIN")):
            return "inner"
        if self.accept("LEFT"):
            self.accept("OUTER")
            self.expect("JOIN")
            return "left"
        return None

    def _group_by(self) -> list[str]:
        if not self.accept("GROUP"):
            return []
        self.expect("BY")
        columns = [self.column_name()]
        while self.accept(","):
            columns.append(self.column_name())
        return columns

    def _order_by(self) -> list[tuple[Expr, bool]]:
        if not self.accept("ORDER"):
            return []
        self.expect("BY")
        keys = [self._order_key()]
        while self.accept(","):
            keys.append(self._order_key())
        return keys

    def _order_key(self) -> tuple[Expr, bool]:
        e = self.expr()
        descending = self.accept("DESC") is not None
        if not descending:
            self.accept("ASC")
        return e, descending

    def _limit(self) -> tuple[int | None, int]:
        if not self.accept("LIMIT"):
            return None, 0
        limit = self.integer()
        return limit, self.integer() if self.accept("OFFSET") else 0

    def table_ref(self) -> tuple[str, str | None]:
        """Parse ``name [AS] [alias]``."""
        name = self.name()
        if self.accept("AS") or self.peek().kind == "name":
            return name, self.name()
        return name, None

    def column_name(self) -> str:
        """Parse ``name`` or ``alias.name``."""
        name = self.name()
        return f"{name}.{self.name()}" if self.accept(".") else name

    def integer(self) -> int:
        """Parse an integer literal (or a parameter holding one).

        :raises SQLError: if it is something else.
        """
        e = self.primary()
        if not isinstance(e, Const) or not isinstance(e.value, int):
            raise SQLError("expected an integer")
        return e.value

    def insert(self) -> Insert:
        """Parse ``INSERT INTO t [(columns)] VALUES (...), (...)``."""
        self.expect("INSERT")
        self.expect("INTO")
        table = self.name()
        columns = self.name_list() if self.peek().value == "(" else None
        self.expect("VALUES")
        rows = [self._value_row()]
        while self.accept(","):
            rows.append(self._value_row())
        return Insert(table, columns, rows)

    def _value_row(self) -> list[Value | None]:
        self.expect("(")
        row = [self.constant()]
        while self.accept(","):
            row.append(self.constant())
        self.expect(")")
        return row

    def constant(self) -> Value | None:
        """Parse an expression that must be a constant.

        :raises SQLError: if it isn't.
        """
        e = self.expr()
        if not isinstance(e, Const):
            raise SQLError("VALUES must contain constants")
        return e.value

    def update(self) -> Update:
        """Parse ``UPDATE t SET column = expr, ... [WHERE expr]``."""
        self.expect("UPDATE")
        table = self.name()
        self.expect("SET")
        assignments: dict[str, Expr] = {}
        while True:
            column = self.name()
            self.expect("=")
            assignments[column] = self.expr()
            if not self.accept(","):
                break
        where = self.expr() if self.accept("WHERE") else None
        return Update(table, assignments, where)

    def delete(self) -> Delete:
        """Parse ``DELETE FROM t [WHERE expr]``."""
        self.expect("DELETE")
        self.expect("FROM")
        table = self.name()
        return Delete(table, self.expr() if self.accept("WHERE") else None)

    def create(self) -> CreateTable | CreateIndex:
        """Parse ``CREATE TABLE`` or ``CREATE [UNIQUE] INDEX``."""
        self.expect("CREATE")
        unique = self.accept("UNIQUE") is not None
        if self.accept("INDEX"):
            return self._create_index(unique=unique)
        if unique:
            raise SQLError("expected INDEX after CREATE UNIQUE")
        self.expect("TABLE")
        stmt = CreateTable(self.name())
        self.expect("(")
        self._table_element(stmt)
        while self.accept(","):
            self._table_element(stmt)
        self.expect(")")
        return stmt

    def _create_index(self, *, unique: bool) -> CreateIndex:
        name = self.name()
        self.expect("ON")
        table = self.name()
        columns = self.name_list()
        kind = self.name().lower() if self.accept("USING") else "hash"
        return CreateIndex(name, table, columns, unique, kind)

    def _table_element(self, stmt: CreateTable) -> None:
        if self.accept("PRIMARY"):
            self.expect("KEY")
            stmt.primary_key = tuple(self.name_list())
        elif self.accept("UNIQUE"):
            stmt.unique.append(tuple(self.name_list()))
        elif self.accept("CHECK"):
            stmt.checks.append(self._parenthesized())
        else:
            self._column_def(stmt)

    def _parenthesized(self) -> Expr:
        self.expect("(")
        e = self.expr()
        self.expect(")")
        return e

    def _column_def(self, stmt: CreateTable) -> None:
        name = self.name()
        type_ = self.type_name()
        options = _ColumnOptions()
        while self._column_option(name, stmt, options):
            pass
        stmt.columns.append(Column(name, type_, nullable=options.nullable, default=options.default))

    def _column_option(self, name: str, stmt: CreateTable, options: _ColumnOptions) -> bool:
        """Parse one column option, if there is one; return whether there was."""
        actions: dict[str, Callable[[], None]] = {
            "NOT": lambda: self._not_null(options),
            "NULL": lambda: self._nullable(options),
            "PRIMARY": lambda: self._key_option(name, stmt, primary=True),
            "UNIQUE": lambda: self._key_option(name, stmt, primary=False),
            "DEFAULT": lambda: self._default(options),
            "CHECK": lambda: stmt.checks.append(self._parenthesized()),
            "REFERENCES": lambda: stmt.foreign_keys.append(self._references(name)),
        }
        tok = self.accept(*actions)
        if tok is None:
            return False
        actions[str(tok.value)]()
        return True

    def _not_null(self, options: _ColumnOptions) -> None:
        self.expect("NULL")
        options.nullable = False

    @staticmethod
    def _nullable(options: _ColumnOptions) -> None:
        options.nullable = True

    def _default(self, options: _ColumnOptions) -> None:
        options.default = self.constant()

    def _key_option(self, name: str, stmt: CreateTable, *, primary: bool) -> None:
        if primary:
            self.expect("KEY")
            stmt.primary_key = (name,)
        else:
            stmt.unique.append((name,))

    def _references(self, column: str) -> ForeignKey:
        ref_table = self.name()
        ref_columns = tuple(self.name_list()) if self.peek().value == "(" else ()
        on_delete: OnDelete = "restrict"
        if self.accept("ON"):
            self.expect("DELETE")
            action = self.expect("CASCADE", "SET", "RESTRICT").value
            if action == "SET":
                self.expect("NULL")
            on_delete = _ON_DELETE[str(action)]
        return ForeignKey((column,), ref_table, ref_columns, on_delete)

    def type_name(self) -> Type[Value]:
        """Parse a type such as ``INTEGER``, ``VARCHAR(80)`` or ``NUMERIC(8, 2)``.

        :raises SQLError: if the type is unknown.
        """
        name = self.name().upper()
        args: list[int] = []
        if self.accept("("):
            args.append(self.integer())
            while self.accept(","):
                args.append(self.integer())
            self.expect(")")
        if name not in _TYPES:
            raise SQLError(f"unknown type {name}")
        return _TYPES[name](args)

    # -- expressions: precedence climbing ------------------------------------------------
    def expr(self, min_bp: int = 0) -> Expr:
        """Parse an expression whose operators all bind tighter than ``min_bp``.

        :param min_bp: the binding power of the operator to our left; 0 by default.
        :return: the expression.
        """
        left = self.prefix()
        while True:
            tok = self.peek()
            op = tok.value if tok.kind in ("op", "keyword") and isinstance(tok.value, str) else ""
            bp = self.INFIX.get(op)
            if bp is None or bp <= min_bp:
                return left
            self.next()
            left = self._infix(op, left, bp)

    def _infix(self, op: str, left: Expr, bp: int) -> Expr:
        """Build the expression for ``left op ...``, parsing the right-hand side."""
        if op in ("OR", "AND"):
            right = self.expr(bp)
            return Or(left, right) if op == "OR" else And(left, right)
        if op == "IS":
            negate = self.accept("NOT") is not None
            self.expect("NULL")
            return Not(IsNull(left)) if negate else IsNull(left)
        if op in ("IN", "NOT"):
            return self._in(left, negate=op == "NOT")
        if op in ("+", "-", "*", "/"):
            return Arith(_arith_op(op), left, self.expr(bp))
        return Compare(_compare_op(op), left, self.expr(bp))

    def _in(self, left: Expr, *, negate: bool) -> Expr:
        if negate:
            self.expect("IN")
        self.expect("(")
        values = [self.constant()]
        while self.accept(","):
            values.append(self.constant())
        self.expect(")")
        membership = In(left, tuple(values))
        return Not(membership) if negate else membership

    def prefix(self) -> Expr:
        """Parse ``NOT x``, ``-x`` or a primary expression."""
        if self.accept("NOT"):
            return Not(self.expr(30))
        if self.accept("-"):
            operand = self.expr(70)
            if isinstance(operand, Const) and isinstance(operand.value, int | Decimal):
                return Const(-operand.value)
            return Arith("-", Const(0), operand)
        return self.primary()

    def primary(self) -> Expr:
        """Parse a literal, a parameter, a column, an aggregate or ``(expr)``.

        :raises SQLError: if none of those starts here.
        """
        tok = self.next()
        if tok.kind in ("number", "string"):
            return Const(tok.value)
        if tok.kind == "keyword" and tok.value in ("TRUE", "FALSE", "NULL"):
            return Const({"TRUE": True, "FALSE": False, "NULL": None}[str(tok.value)])
        if tok.value in ("?", "("):
            return self._parameter() if tok.value == "?" else self._group()
        if tok.kind == "name" and isinstance(tok.value, str):
            return self._name_expr(tok.value)
        raise SQLError(f"unexpected {tok.value!r} at position {tok.pos}")

    def _parameter(self) -> Const:
        if self.used_params >= len(self.params):
            raise SQLError("not enough parameters")
        self.used_params += 1
        return Const(self.params[self.used_params - 1])

    def _group(self) -> Expr:
        e = self.expr()
        self.expect(")")
        return e

    def _name_expr(self, name: str) -> Expr:
        if self.peek().value == "(" and name.upper() in AGGREGATES:
            self.next()
            column = None if self.accept("*") else self.column_name()
            self.expect(")")
            return AggCall(name.upper(), column)
        if self.accept("."):
            return Col(f"{name}.{self.name()}")
        return Col(name)


_COMPARE_OPS: dict[str, CompareOp] = {"=": "=", "!=": "!=", "<": "<", "<=": "<=", ">": ">", ">=": ">="}
_ARITH_OPS: dict[str, ArithOp] = {"+": "+", "-": "-", "*": "*", "/": "/"}


def _compare_op(op: str) -> CompareOp:
    return _COMPARE_OPS[op]


def _arith_op(op: str) -> ArithOp:
    return _ARITH_OPS[op]


# -- 4. execution ------------------------------------------------------------------------------
class Connection:
    """Run SQL statements against a database.

    Statements outside ``BEGIN ... COMMIT`` run in transactions of their
    own: ``SELECT`` in a read-only one, everything else through
    :meth:`Database.transaction`, with retries.

    :param db: the database.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.uow: UnitOfWork | None = None

    def execute(self, sql: str, params: Sequence[Value | None] = ()) -> Result:
        """Parse and run one statement.

        :param sql: the statement.
        :param params: the values for its ``?`` placeholders; none by default.
        :return: the rows for a ``SELECT``, the number of rows affected for
            ``INSERT``, ``UPDATE`` and ``DELETE``, ``None`` otherwise.
        :raises SQLError: if the statement is invalid.
        :raises DatabaseError: whatever the database refuses.
        """
        stmt = Parser(sql, params).statement()
        if isinstance(stmt, TransactionControl):
            return self._transaction_control(stmt.action)
        if isinstance(stmt, CreateTable | CreateIndex):
            return self._ddl(stmt)
        if self.uow is not None:
            return self._run(stmt, self.uow)
        if isinstance(stmt, Select):
            with self.db.unit_of_work(readonly=True) as uow:
                return self._select(stmt, uow)
        return self.db.transaction(lambda uow: self._run(stmt, uow))

    def _transaction_control(self, action: str) -> None:
        if action == "BEGIN":
            if self.uow is not None:
                raise SQLError("already in a transaction")
            self.uow = self.db.unit_of_work()
            return
        if self.uow is None:
            raise SQLError(f"{action} without BEGIN")
        uow, self.uow = self.uow, None
        if action == "ROLLBACK":
            uow.rollback()
            return
        with uow:  # commits, or rolls back if the commit fails
            pass

    def _ddl(self, stmt: CreateTable | CreateIndex) -> None:
        if self.uow is not None:
            raise SQLError("DDL is not allowed inside a transaction")
        if isinstance(stmt, CreateIndex):
            self.db.create_index(stmt.table, stmt.name, stmt.columns, unique=stmt.unique, kind=stmt.kind)
            return
        checks = [Check(f"check_{i + 1}", e) for i, e in enumerate(stmt.checks)]
        self.db.create_table(
            stmt.name,
            stmt.columns,
            primary_key=stmt.primary_key,
            unique=stmt.unique,
            checks=checks,
            foreign_keys=stmt.foreign_keys,
        )

    def _run(self, stmt: Select | Insert | Update | Delete, uow: UnitOfWork) -> Result:
        if isinstance(stmt, Insert):
            return self._insert(stmt, uow)
        if isinstance(stmt, Update):
            return self._update(stmt, uow)
        if isinstance(stmt, Delete):
            return uow.delete(stmt.table, stmt.where)
        return self._select(stmt, uow)

    @staticmethod
    def _insert(stmt: Insert, uow: UnitOfWork) -> int:
        names = stmt.columns or list(uow.table(stmt.table).columns)
        for values in stmt.rows:
            if len(values) != len(names):
                raise SQLError(f"{len(names)} columns but {len(values)} values")
            uow.insert(stmt.table, dict(zip(names, values, strict=True)))
        return len(stmt.rows)

    @staticmethod
    def _update(stmt: Update, uow: UnitOfWork) -> int:
        """Compute each row's new values from its old ones, and let dirty checking save them."""
        records = uow.find(stmt.table, stmt.where)
        for record in records:
            record.update({c: e.eval(record) for c, e in stmt.assignments.items()})
        uow.flush()
        return len(records)

    def _select(self, s: Select, uow: UnitOfWork) -> list[dict[str, Value | None]]:
        q = uow.query(*s.table)
        for name, alias, on, kind in s.joins:
            q = q.join(name, on, alias, kind)
        if s.where is not None:
            q = q.where(s.where)
        q = _with_ordering(_with_grouping(q, s), s)
        if s.items is not None:
            q = q.select(**_outputs(s.items))
        q = q.distinct() if s.distinct else q
        return (q.limit(s.limit, s.offset) if s.limit is not None or s.offset else q).all()


def _with_grouping(q: Query, s: Select) -> Query:
    """Add GROUP BY and HAVING, computing every aggregate the statement mentions."""
    aggregates = {call.key: AGGREGATES[call.func](call.column) for e in _all_exprs(s) for call in _agg_calls(e)}
    if s.group_by or aggregates:
        q = q.group_by(*s.group_by, **aggregates)
    return q.having(s.having) if s.having is not None else q


def _with_ordering(q: Query, s: Select) -> Query:
    """Add ORDER BY; a name that is a SELECT alias sorts by what the alias stands for."""
    if not s.order_by:
        return q
    aliases = {a: e for e, a in s.items or () if a}
    keys = [_sort_key(aliases.get(e.name, e) if isinstance(e, Col) else e, d) for e, d in s.order_by]
    return q.order_by(*keys)


def _outputs(items: list[tuple[Expr, str | None]]) -> dict[str, str | RowFunction]:
    """Name each output: its alias, else its column's name, else its text."""
    return {alias or (e.name.rpartition(".")[2] if isinstance(e, Col) else repr(e)): e for e, alias in items}


def _sort_key(e: Expr, descending: bool) -> str | RowFunction:  # noqa: FBT001 - a pair with e, from the parser
    """Turn an ORDER BY item into a key for :meth:`Query.order_by`."""
    if isinstance(e, Col | AggCall):  # by name: works in either direction
        return ("-" if descending else "") + (e.name if isinstance(e, Col) else e.key)
    if descending:
        raise SQLError("ORDER BY <expression> DESC is not supported; use an alias")
    return e


def _all_exprs(s: Select) -> Iterator[Expr]:
    yield from (e for e, _ in s.items or ())
    if s.having is not None:
        yield s.having
    yield from (e for e, _ in s.order_by)


def _agg_calls(e: Expr) -> Iterator[AggCall]:
    """Yield every aggregate call inside ``e``."""
    if isinstance(e, AggCall):
        yield e
    for child in _children(e):
        yield from _agg_calls(child)


def _children(e: Expr) -> tuple[Expr, ...]:
    if isinstance(e, Compare | Arith):
        return (e.left, e.right)
    if isinstance(e, Not | IsNull | In):
        return (e.item,)
    if isinstance(e, And | Or):
        return e.items
    return ()


def connect(db: Database) -> Connection:
    """Open a SQL connection to ``db``.

    >>> from minidb.database import Database
    >>> conn = connect(Database())
    >>> conn.execute("CREATE TABLE t (n INTEGER PRIMARY KEY)")
    >>> conn.execute("INSERT INTO t VALUES (1), (2)")
    2
    >>> conn.execute("SELECT COUNT(*) AS n FROM t")
    [{'n': 2}]

    :param db: the database.
    :return: a new connection.
    """
    return Connection(db)
