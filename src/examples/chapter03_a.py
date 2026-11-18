from minidb.types import *


def normalize(t: Type, content: object) -> object:
    try:
        value = t.normalize(content)
    except DomainError as e:
        print(e)
    else:
        print(f"\"{content}\" <{type(content).__name__}> --> '{value}' <{type(value).__name__}>")
        return value
    finally:
        print()


def validate(t: Type, content: object) -> None:
    try:
        t.validate(content)
    except DomainError as e:
        print(e)
    else:
        print(f"\"{content}\" <{type(content).__name__}> --> valid!")
    finally:
        print()


def main() -> None:
    normalize(Boolean(), "Yes")

    normalize(Integer(), True)

    normalize(Integer(min=0, max=150), " 42 ")
    validate(Integer(min=0, max=150), 200)

    normalize(Numeric(6, 2), 0.1)
    normalize(Numeric(6, 2), "2.675")  # half-even: 2.675 -> 2.68

    normalize(Numeric(4, 2), "123.4")
    validate(Numeric(4, 2), Numeric(4, 2).normalize("123.4"))

    validate(Text(max_length=3), "abcd")

    normalize(Date(), "2026-11-18")

    normalize(Timestamp(), "2026-11-18T10:00:00+01:00")


if __name__ == '__main__':
    main()
    print("Done.")
