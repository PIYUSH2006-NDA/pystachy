# error: walrus_retype.py:7: error: expected int, got str
# x := v gives x a value of x's type, as x = v does (CPython: x holds the str from there on)


def f() -> None:
    x = 1
    print((x := "s"), x)


f()
