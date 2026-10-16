# Documented deviation: a PEP 695 function's type parameter hides a module-level name of the
# same name only in the function's annotations; its body reads the module's T, where CPython's
# is the TypeVar (TypeError: unsupported operand type(s) for +: 'typing.TypeVar' and 'int')
T = 5


def f[T](x: T) -> int:
    return T + 1


print(f(1))
