# A generic def's type parameters are its body's names (#505), as a generic class's are its
# methods': where the body binds the name again (a local, a parameter, a comprehension's or a
# lambda's) or declares it global, it reads that; a default value reads the module's; a nested
# def's annotations name the outer def's, which make the nested def a template too.
T = 5


def default[T](x: int = T) -> int:
    return x


def local[T](x: T) -> int:
    T = 3
    return T + 1


def param[T](T: int) -> int:
    return T + 1


def module[T](x: T) -> int:
    global T
    return T + 1


def scopes[T](x: T) -> int:
    return [T for T in range(3)][-1] + (lambda T: T * 2)(4)


def outer[T](x: T) -> list[T]:
    def inner(y: T) -> list[T]:
        return [y, y]

    return inner(x)


def twice[U](u: U) -> list[U]:
    def again[T](t: T) -> list[T]:
        return [t, t]

    return again(u) + again(u)


print(default(), local(1), param(2), module("x"), scopes(1.5))
print(outer(1), outer("a"), twice(2.5), T)
