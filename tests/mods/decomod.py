"""Decorated defs of an imported module (decorators_mod.py): CPython applies their decorators
when the module is imported, and each name binds what they gave, a module variable."""

REGISTRY: list[str] = []


def register(name):
    print("register", name)

    def wrap(f):
        REGISTRY.append(name)
        return f
    return wrap


def trace(f):
    def w(x):
        print("call", x)
        return f(x)
    return w


@register("add")
def add(a, b):
    return a + b


@register("neg")
@trace
def neg(x):
    return -x


def twice_add(x: int) -> int:
    return add(x, x)
