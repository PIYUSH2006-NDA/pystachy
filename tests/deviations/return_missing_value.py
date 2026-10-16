# Documented deviation: a function declared to return a value, here a class's objects without
# None, that ends without a return raises RuntimeError where CPython returns None; declared to
# return C | None, it returns None (#494)
class A:
    pass


def f(x: int) -> A:
    if x:
        return A()


def g(x: int) -> A | None:
    if x:
        return A()


print(g(0))
print(f(0))
