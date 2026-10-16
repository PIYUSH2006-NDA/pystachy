"""A module that imports collections, then collections.abc (as asyncio and ElementTree do), and
re-exports names of collections.abc."""
import collections
import collections.abc
from collections.abc import Sequence
import collections.abc as cabc


def first(xs: collections.abc.Sequence[int]) -> int:
    return xs[0]


def is_seq(x: list[int] | dict[int, int]) -> bool:
    return isinstance(x, collections.abc.Sequence)


def queue(xs: list[str]) -> collections.deque[str]:
    return collections.deque(xs, 2)
