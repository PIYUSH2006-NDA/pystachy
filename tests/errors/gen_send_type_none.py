# error: a generator's send type must be one that may be None (next() sends None), not BaseException
from collections.abc import Generator


def acc() -> Generator[int, BaseException, None]:
    e = yield 1
    print(e)


for v in acc():
    print(v)
