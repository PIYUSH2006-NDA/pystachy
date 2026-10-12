# error: dstar_call.py:6: error: ** arguments (f(**d)) are not supported
def two(a: int, b: int) -> int:
    return a + b


print(two(**{"a": 1, "b": 2}))
