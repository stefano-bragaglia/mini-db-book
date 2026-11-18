from typing import Callable

type Attribute = str
type Value = None | bool | int | float | str
type Tuple = dict[Attribute, Value]
type Relation = list[Tuple]
type Body = set[Relation]
type Predicate = Callable[[Tuple], bool]
type Condition = Callable[[Tuple, Tuple], bool]


def select(relation: Relation, predicate: Predicate) -> Body:
    return [t for t in relation if predicate(t)]


def project(relation: Relation, *attributes: Attribute, distinct: bool = False) -> Body:
    seen, result = set(), []
    for t in relation:
        row = {a: t[a] for a in attributes}
        key = tuple(row.items())
        if not distinct or key not in seen:
            seen.add(key)
            result.append(row)
    return result


def join(left: Relation, right: Relation, on: Condition) -> Relation:
    return [
        {
            **{f"l_{k}": v for k, v in l.items()},
            **{f"r_{k}": v for k, v in r.items()},
        }
        for l in left for r in right if on(l, r)]


def main() -> None:
    users = [
        {"id": 1, "name": "Ada", "age": 36},
        {"id": 2, "name": "Alan", "age": 41},
        {"id": 3, "name": "Grace", "age": None},
        {"id": 4, "name": "Alan", "age": 43},
    ]
    orders = [
        {"order_id": 10, "user_id": 1, "total": 25},
        {"order_id": 11, "user_id": 2, "total": 40},
        {"order_id": 12, "user_id": 1, "total": 15},
    ]

    older_than_40 = lambda user: "age" in user and user["age"] is not None and user["age"] > 40

    users_older_than_40 = select(users, older_than_40)
    print(users_older_than_40)

    names_of_users_older_than_40 = project(users_older_than_40, "name")
    print(names_of_users_older_than_40)

    print(project(select(users, older_than_40), "name", distinct=True))

    same_id = lambda user, order: user["id"] == order["user_id"]

    users_and_orders = join(users, orders, same_id)
    print(users_and_orders)

    users_and_orders_total = project(users_and_orders, "l_name", "r_total")
    print(users_and_orders_total)

    print(project(join(users, orders, same_id), "l_name", "r_total"))

    print(project(join(select(users, older_than_40), orders, same_id), "l_name", "r_total"))


if __name__ == '__main__':
    main()
    print("Done.")
