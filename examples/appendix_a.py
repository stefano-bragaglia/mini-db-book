from typing import Callable

from minidb import Database
from minidb import connect


def exec(fn: Callable) -> None:
    try:
        value = fn()
    except Exception as e:
        print(e)
    else:
        print(value)
    finally:
        print()


def main() -> None:
    conn = connect(Database())
    exec(
        lambda: conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT,
            age INTEGER CHECK (age >= 0)
        )""")
    )
    exec(
        lambda: conn.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE,
            total NUMERIC(8, 2) NOT NULL,
            placed DATE
        )""")
    )
    exec(
        lambda: conn.execute(
            "INSERT INTO users VALUES (1, 'Ada', 'London', 36), (2, 'Alan', 'London', 41),"
            " (3, 'Grace', 'New York', 85), (4, 'Edgar', NULL, NULL)"
        )
    )
    exec(
        lambda: conn.execute(
            "INSERT INTO orders (id, user_id, total, placed) VALUES"
            " (10, 1, 25.00, '2026-11-01'), (11, 2, 40.00, '2026-11-02'),"
            " (12, 1, 15.50, '2026-11-03'), (13, 3, 9.99, '2026-11-03')"
        )
    )

    # -------------------------------------------------------------------------------------------------------------------
    exec(lambda: conn.execute("SELECT name, age FROM users WHERE age > ? ORDER BY age DESC", [40]))
    exec(lambda: conn.execute("SELECT name FROM users WHERE city IS NULL OR age IN (36, 41)"))
    exec(
        lambda: conn.execute("""
        SELECT u.name, COUNT(*) AS orders, SUM(o.total) AS spent
        FROM users u JOIN orders o ON u.id = o.user_id
        WHERE o.placed >= '2026-11-02'
        GROUP BY u.name
        ORDER BY spent DESC""")
    )
    exec(lambda: conn.execute("SELECT city, COUNT(*) AS n FROM users GROUP BY city HAVING COUNT(*) > 1"))

    # ------------------------------------------------------------------------------------------------------------------
    exec(lambda: conn.execute("UPDATE users SET age = age + 1 WHERE city = 'London'"))
    exec(lambda: conn.execute("SELECT name, age FROM users WHERE city = 'London'"))
    exec(lambda: conn.execute("UPDATE users SET age = -1 WHERE id = 1"))
    exec(lambda: conn.execute("DELETE FROM users WHERE name = 'Ada'"))
    exec(lambda: conn.execute("SELECT COUNT(*) AS n FROM orders"))

    # ------------------------------------------------------------------------------------------------------------------
    exec(lambda: conn.execute("BEGIN"))
    exec(lambda: conn.execute("INSERT INTO users (id, name) VALUES (5, 'Barbara')"))
    exec(lambda: conn.execute("SELECT COUNT(*) AS n FROM users"))  # sees its own insert
    exec(lambda: conn.execute("ROLLBACK"))
    exec(lambda: conn.execute("SELECT COUNT(*) AS n FROM users"))

    # ------------------------------------------------------------------------------------------------------------------
    exec(lambda: conn.execute("SELEC * FROM users"))
    exec(lambda: conn.execute("SELECT * FROM users WHERE"))
    exec(lambda: conn.execute("SELECT * FROM users WHERE name = ?", ["x' OR '1'='1"]))  # no injection


if __name__ == "__main__":
    main()
    print("Done.")
