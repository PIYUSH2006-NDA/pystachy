# error: closure_decorator.py:8: error: a decorator on a def inside a function is not supported (inner())
def deco(g):
    return g


def f(n):
    @deco
    def inner(k):
        return k + n
    return inner(1)


print(f(1))
