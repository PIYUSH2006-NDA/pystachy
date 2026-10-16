# A generator that resumes itself raises ValueError: generator already executing (#490).
from collections.abc import Iterator

holder: list[Iterator[int]] = []


def selfish() -> Iterator[int]:
    yield 1
    for v in holder[0]:
        yield v


g = selfish()
holder.append(g)
print(next(g))
print(next(g))
