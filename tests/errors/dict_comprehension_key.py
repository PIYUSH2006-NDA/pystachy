# error: dict keys must be int or str, or tuples of int, bool, str and str | None items, not float
squares = {x / 2: x for x in range(3)}
print(squares)
