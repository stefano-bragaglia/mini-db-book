"""Name the types of the values that tables hold."""
import datetime as dt
from decimal import Decimal

type Value = bool | int | float | str | Decimal | dt.date | dt.datetime
type Row = dict[str, Value | None]
