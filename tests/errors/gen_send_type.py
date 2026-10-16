# error: a generator whose send type is not None (Generator[Y, S, R]) is not supported: generators have no send()
from collections.abc import Generator


def acc() -> Generator[int, int, None]:
    yield 1


for v in acc():
    print(v)
