# reversed(o) calls o.__reversed__, which (as a supported __iter__) is annotated -> Iterator[T]
# and returns iter(xs); every consumer of reversed() steps through that iterator, and a None
# object raises CPython's TypeError.
from typing import Iterator


class Steps:
    def __init__(self, n: int) -> None:
        self.n = n

    def __iter__(self) -> Iterator[int]:
        print("iter")
        return iter(list(range(self.n)))

    def __reversed__(self) -> Iterator[int]:
        print("reversed", self.n)
        return iter([self.n - 1 - i for i in range(self.n)])


class Word:
    def __init__(self, s: str) -> None:
        self.s = s

    def __reversed__(self) -> Iterator[str]:
        return iter(list(reversed(self.s)))


class Nest:
    def __init__(self) -> None:
        self.inner = Steps(2)

    def __reversed__(self) -> Iterator[int]:
        return iter(self.inner)


def label(n: int) -> str:
    print("label", n)
    return str(n)


s = Steps(3)
for i in reversed(s):
    print(i)
print(list(reversed(s)), sorted(reversed(s)), sum(reversed(s)), min(reversed(s)), max(reversed(s)))
print([x * 10 for x in reversed(s) if x != 1], any(x > 1 for x in reversed(s)))
print("-".join([label(x) for x in reversed(s)]), list(reversed(Steps(0))))
print(list(reversed(Word("abc"))), "".join(reversed(Word("xyz"))), list(reversed(Nest())))
xs: list[int] = []
xs.extend(reversed(s))
print(xs)


def tail(o: Steps) -> list[int]:
    return [x for x in reversed(o)][:2]


class Holder:
    def __init__(self) -> None:
        self.steps = Steps(4)

    def back(self) -> list[int]:
        return list(reversed(self.steps))


print(tail(Steps(5)), Holder().back())
none: Steps | None = None
try:
    for i in reversed(none):
        print(i)
except TypeError as e:
    print("TypeError", e)
try:
    print(list(reversed(none)))
except TypeError as e:
    print("TypeError", e)
