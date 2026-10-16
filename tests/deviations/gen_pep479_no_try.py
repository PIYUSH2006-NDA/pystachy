# Documented deviation (#490): in a program without try or with statements, a StopIteration
# that a function a generator calls raises ends the program as StopIteration, where CPython's
# PEP 479 makes it RuntimeError: generator raised StopIteration as it leaves the generator.
# Nothing could catch either, and the exit status is the same. (A raise StopIteration or a
# next() in the generator's own body is converted, and so is everything once the program has a
# try or with statement.)
from collections.abc import Iterator


def inner() -> Iterator[int]:
    yield 1


def step(g: Iterator[int]) -> int:
    return next(g)


def outer() -> Iterator[int]:
    g = inner()
    while True:
        yield step(g)


for x in outer():
    print(x)
