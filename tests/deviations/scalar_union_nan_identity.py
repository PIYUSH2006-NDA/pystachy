# Native floats have no Python object identity, even inside immutable union boxes.
def inspect(value: float | str) -> None:
    items: list[float | str] = [value]
    print(value == value, value in items, items.count(value))

inspect(float("nan"))
