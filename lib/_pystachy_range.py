"""The range type of the builtins, as a class of the subset.

Pystachy's own module, after CPython 3.13's Objects/rangeobject.c: where a program uses range()
as a value (assigns, passes, returns or stores it), the compiler makes an object of this class.
A for loop or a comprehension over one steps through its numbers as it does through range(...)
itself, x in it is the runtime's arithmetic, iter() of one makes a range_iterator
(lib/_pystachy_iterators.py) and a slice of one is _slice's. The compiler loads this module for a
program that reads the builtin range (Loader.program); programs do not import it, it runs no code,
and its methods are compiled where a program calls them. The __pys_range_* calls
are compiler primitives: the runtime's count of the numbers (unsigned, in an int: one of 2**63 or
more is negative), its x in range(start, stop, step) and its list of the numbers, and
start + k * step in 64-bit arithmetic that wraps (an item fits in an int, though k * step may not).
"""
from typing import Iterator


class range:
    __slots__ = ("start", "stop", "step")

    def __init__(self, start: int, stop: int, step: int) -> None:
        if step == 0:
            raise ValueError("range() arg 3 must not be zero")
        self.start = start
        self.stop = stop
        self.step = step

    def __repr__(self) -> str:
        if self.step == 1:
            return f"range({self.start}, {self.stop})"
        return f"range({self.start}, {self.stop}, {self.step})"

    def __len__(self) -> int:
        n = __pys_range_len(self.start, self.stop, self.step)
        if n < 0:
            raise OverflowError("Python int too large to convert to C ssize_t")
        return n

    def __bool__(self) -> bool:
        return __pys_range_len(self.start, self.stop, self.step) != 0

    def __iter__(self) -> Iterator[int]:
        # (a list of the numbers, where a generic path takes the items at once, as a star in a
        # display does: loops and consumers step through them instead)
        return iter(__pys_range_list(self.start, self.stop, self.step))

    def __contains__(self, x: int) -> bool:
        return __pys_range_has(x, self.start, self.stop, self.step)

    def __getitem__(self, i: int) -> int:
        # (a count of 2**63 or more has an item at every index an int can be)
        n = __pys_range_len(self.start, self.stop, self.step)
        if n >= 0 and (i >= n or i < -n):
            raise IndexError("range object index out of range")
        if i < 0:
            return __pys_range_at(__pys_range_at(self.start, self.step, n), self.step, i)
        return __pys_range_at(self.start, self.step, i)

    def __eq__(self, other: "range") -> bool:
        # CPython compares ranges as the sequences they are: range(0) == range(5, 5)
        if other is None:
            return False
        n = __pys_range_len(self.start, self.stop, self.step)
        if n != __pys_range_len(other.start, other.stop, other.step):
            return False
        if n == 0:
            return True
        if self.start != other.start:
            return False
        return n == 1 or self.step == other.step

    def __hash__(self) -> int:
        # hash((len, start, step)), with None for what the items do not decide; a count of 2**63
        # or more is n + 2**64, whose hash is that mod 2**61 - 1 (2**64 mod 2**61 - 1 is 8)
        n = __pys_range_len(self.start, self.stop, self.step)
        h = n if n >= 0 else (n % 2305843009213693951 + 8) % 2305843009213693951
        if n == 0:
            return hash((h, None, None))
        if n == 1:
            return hash((h, self.start, None))
        return hash((h, self.start, self.step))

    def count(self, x: int) -> int:
        return 1 if __pys_range_has(x, self.start, self.stop, self.step) else 0

    def index(self, x: int) -> int:
        if not __pys_range_has(x, self.start, self.stop, self.step):
            raise ValueError(f"{x} is not in range")
        # (x is start + k * step: x // step is start // step + k, exactly)
        return x // self.step - self.start // self.step


def _slice(r: range, lo: int | None, hi: int | None, st: int | None) -> range:
    # r[lo:hi:st] (the compiler calls it): CPython's compute_slice, a range from the item at the
    # index _PySlice_GetLongIndices clamps lo to, to the one at hi's, of step times st
    if r is None:
        raise TypeError("'NoneType' object is not subscriptable")
    step = 1 if st is None else st
    if step == 0:
        raise ValueError("slice step cannot be zero")
    n = __pys_range_len(r.start, r.stop, r.step)
    if n < 0:
        # (2**63 items or more: every index an int can be is within the range, unclamped)
        a = (r.start if step > 0 else r[-1]) if lo is None else r[lo]
        b = (r[-1] + r.step if step > 0 else r.start - r.step) if hi is None else r[hi]
        return range(a, b, r.step * step)
    lower = -1 if step < 0 else 0
    upper = n - 1 if step < 0 else n
    start = (upper if step < 0 else lower) if lo is None else _clamp(lo, n, lower, upper)
    stop = (lower if step < 0 else upper) if hi is None else _clamp(hi, n, lower, upper)
    return range(_item(r, n, start), _item(r, n, stop), r.step * step)


def _clamp(i: int, n: int, lower: int, upper: int) -> int:
    # a slice's bound, from the end where it is negative, within lower and upper
    if i < 0:
        i += n
        return lower if i < lower else i
    return upper if i > upper else i


def _item(r: range, n: int, k: int) -> int:
    # start + k * step for k from -1 to n: past either end, CPython's value, if it fits
    if k < 0:
        return r.start - r.step
    if k >= n:
        return r.start if n == 0 else __pys_range_at(r.start, r.step, n - 1) + r.step
    return __pys_range_at(r.start, r.step, k)


def _unpack(r: range, k: int) -> list[int]:
    # the numbers a, b, ... = r assigns, if there are k of them, else CPython's ValueError (it takes
    # an item more than k at most: a longer range is not made a list)
    n = __pys_range_len(r.start, r.stop, r.step)
    if n < 0 or n > k:
        raise ValueError(f"too many values to unpack (expected {k})")
    if n < k:
        raise ValueError(f"not enough values to unpack (expected {k}, got {n})")
    return __pys_range_list(r.start, r.stop, r.step)
