# error: generator.send() is not supported: generators have no send(), throw() or close() (for loops, yield from, next() and the functions that take an iterable run them)
from collections.abc import Iterator


def averager() -> Iterator[float]:
    total = 0.0
    while True:
        yield total


g = averager()
for v in g:
    break
g.send(5.0)
