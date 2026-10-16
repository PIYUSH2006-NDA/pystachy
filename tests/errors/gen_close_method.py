# error: generator.close() is not supported: generators have no send(), throw() or close() (for loops, yield from, next() and the functions that take an iterable run them)
from collections.abc import Iterator


def nums() -> Iterator[int]:
    yield 1


g = nums()
g.close()
