# An itertools iterator that an exception has left (from its predicate, key or function, or from
# its iterator) is finished, as a generator is, where CPython's C iterators of takewhile(),
# dropwhile(), filterfalse(), accumulate(), starmap(), groupby() and the others but islice()
# can go on (lib/compatibility.md)
from itertools import filterfalse, takewhile

seen: list[int] = []


def odd(x: int) -> bool:
    seen.append(x)
    if x == 2:
        raise ValueError("two")
    return x % 2 == 1


ff = filterfalse(odd, [1, 2, 3, 4, 5, 6])
try:
    print(next(ff))
except ValueError as e:
    print("ValueError:", e)
print(list(ff), seen)
tw = takewhile(lambda x: 10 // x > 0, [5, 0, 3])
try:
    print(list(tw))
except ZeroDivisionError as e:
    print("ZeroDivisionError:", e)
print(list(tw))
