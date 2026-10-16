# error: the value of a yield expression is not supported: generators have no send(), so yield is a statement (yield v)
from collections.abc import Iterator


def echo() -> Iterator[int]:
    x = yield 1
    print(x)


for v in echo():
    print(v)
