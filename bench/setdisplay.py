# set displays of constants evaluated over and over, as code tests membership, loops over a fixed
# set and starts from one: x in {...} and a for loop's {...} are CPython's frozenset constants,
# and a display assigned is a new set of the constant's elements each time it runs


def vowels(s: str) -> int:
    n = 0
    for c in s:
        if c in {"a", "e", "i", "o", "u"}:
            n += 1
    return n


def loops(k: int) -> int:
    t = 0
    for _ in range(k):
        for x in {3, 1, 4, 5, 9, 2, 6}:
            t += x
    return t


def fresh(k: int) -> int:
    t = 0
    for _ in range(k):
        s = {10, 20, 30, 40}
        s.add(t % 7)
        t += len(s)
    return t


text = "the quick brown fox jumps over the lazy dog " * 100000
print(vowels(text), loops(1000000), fresh(1000000))
