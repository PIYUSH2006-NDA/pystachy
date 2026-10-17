# An itertools iterator whose input has ended is finished, as a generator is: called again, it
# reads none of its inputs, where CPython's C iterators of accumulate(), compress(), dropwhile(),
# filterfalse(), groupby(), starmap() and takewhile() read them again (lib/compatibility.md).
# That shows with an input that prints at its end, and with compress(), which, called again
# after its selectors' end, reads an item of its data in CPython.
from itertools import accumulate, compress, filterfalse


class Logged:
    def __init__(self, items: list[int]) -> None:
        self.items = items
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.i >= len(self.items):
            print("  end of input")
            raise StopIteration
        self.i += 1
        return self.items[self.i - 1]


acc = accumulate(Logged([1, 2]))
print(list(acc))
print(next(acc, -1))
ff = filterfalse(None, Logged([0, 3]))
print(list(ff), next(ff, -1))
data = iter([1, 2, 3, 4, 5])
c = compress(data, [True])
print(list(c), next(c, -1), next(data))
