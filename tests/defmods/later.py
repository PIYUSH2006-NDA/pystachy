"""Module for tests/deftime_later.py."""


def check(x, fs=(LATER, b"x")):
    "a default value Pystachy cannot compile (bytes): CPython evaluates it, and LATER is unbound"
    return x


LATER = 1
