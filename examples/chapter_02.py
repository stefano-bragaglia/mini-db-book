from minidb import Database


def main() -> None:
    db = Database()

    _ = db.create_table("users", ["id", "name", "age"])

    print(db.insert("users", {"id": 1, "name": "Ada", "age": 36}))
    print(db.insert("users", {"id": 2, "name": "Alan", "age": 41}))
    print(db.insert("users", {"id": 3, "name": "Grace"}))  # age missing -> None
    print(db.select("users"), "\n")

    older_than_40 = lambda row: "age" in row and row["age"] is not None and row["age"] > 40
    print(db.select("users", where=older_than_40), "\n")

    name_is_ada = lambda row: "name" in row and row["name"] == "Ada"
    print(db.update("users", {"age": 37}, where=name_is_ada))
    print(db.select("users"), "\n")

    age_is_none = lambda row: "age" in row and row["age"] is None
    print(db.delete("users", where=age_is_none))
    print(db.select("users"), "\n")

    print(db.insert("users", {"id": 4, "name": "Edgar"}))
    print(db.select("users"), "\n")

    row = db.get("users", 1)
    row["name"] = "Mallory"
    print(row["name"], "!=", db.get("users", 1)["name"], "\n")

    print(db.insert("users", {"nmae": "typo"}))


if __name__ == '__main__':
    main()
    print("Done.")
