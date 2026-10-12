# error: isinstance_tuple_unbound.py:7: error: isinstance() is only supported with the builtin types and classes as its second argument
# CPython reads every item of the tuple: y is not assigned yet (UnboundLocalError), although the test
# would stop at int


def f(n: int) -> bool:
    r = isinstance(n, (int, y))
    y = 5
    return r and y > 0


print(f(1))
