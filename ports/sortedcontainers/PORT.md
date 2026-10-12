# sortedcontainers 2.4.0, ported to Pystachy

[sortedcontainers](https://pypi.org/project/sortedcontainers/) is a pure-Python library of
sorted collections, `SortedList`, `SortedDict` and `SortedSet`, which its author benchmarks
against C extensions. It is rank 135 on PyPI in October 2026; its dependents include Hypothesis,
Trio, fakeredis, Dask's distributed and intervaltree. A `SortedList` keeps its values in a list
of sorted sublists of up to twice its load factor (1,000), the largest value of each sublist in
a second list, and, once a positional operation needs it, a tree of the sublists' lengths in a
third, so that `add`, `remove`, `sl[i]`, `del sl[i]`, `bisect_left`, `count` and `index` take
O(log n). `SortedDict` and `SortedSet` are built on it.

This port is `SortedList` of `int`. These are two of the four modules of the sdist
`sortedcontainers-2.4.0.tar.gz` (SHA-256
`25caa5a06cc30b6b83d11423433f65d1f9d76c4c6a0c90e3379eaa43b9bfdb88`), used under the Apache
License, Version 2.0: `LICENSE` is the sdist's license notice as it is, and the License's text
is at the end of `THIRD_PARTY_NOTICES`.

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `5ff5f92ee463bdeefb2b0b8942b0d44aed13f39e7d61ca28c106c09e3b8ced31` | 1 (the imports of `SortedSet` and `SortedDict`) |
| `sortedlist.py` | `af003574cf1c7b4f5e6f60cc8cb39f1e88a4842c7f45f9399ee13f352b1faf72` | 97 marked edits in 48 diff hunks |

`sortedset.py` and `sorteddict.py` are left out: nothing imports them now. The rest of the sdist
is packaging and the README. Both files here are modified files in the sense of section 4(b) of
the Apache License: each says so in a comment at its top, every edit is marked
`# Pystachy port:` in the source, and `diff -ru` against the sdist's `sortedcontainers/` shows
them all.

## The edits, and the feature each one stands in for

All edits but one serve `SortedList`: they are in the class, in the module's imports and in
two functions added before the class. The data structure and its algorithms stay as upstream
wrote them: `_lists`, `_maxes`, `_index` and `_offset` hold under Pystachy what they hold under
CPython, step by step (the tests print them). `SortedKeyList`, the subclass that takes `key=`,
is left as it is but for one decorator: Pystachy accepts its class statement and rejects the
class where a program uses it (inheritance, M2).

**M2, full classes ([#7](https://github.com/den-run-ai/pystachy/issues/7)).**

- The methods of `SortedList` are annotated (33 signatures, and `-> str` on `__repr__`), with
  `int` for values and indices, `Optional[int]` for the `None` defaults, and `list[int]` where
  upstream takes any iterable (`__init__`, `update`, `+`, `+=`);
  `from typing import Iterator, Optional` is added for them. Pystachy rejects a class as a
  whole, where a program uses it, if one of its methods has an unannotated parameter, so the
  methods a program never calls need annotations too, and it reads a missing return annotation
  as `-> None`. (The methods that take only `self` and return nothing a program can use,
  `_build_index`, `reverse`, `__reversed__`, `__reduce__` and `_check`, stay as they are.) M2's
  classes as templates would compile unannotated methods for each call signature; `int` stands
  in for any comparable value, as Pystachy has no generic classes (a `TypeVar` in a method is
  rejected).
- `class SortedList(MutableSequence)` loses its base (inheritance). `SortedList` overrides every
  method the ABC would supply, so only `isinstance(sl, Sequence)` and the like are lost.
- The three empty list fields of `__init__` are annotated (`self._lists: list[list[int]] = []`
  and the like): Pystachy types a field by what `__init__` assigns, and `[]` does not say.
- `__new__` is dropped: it returns a `SortedKeyList` when `key=` is given (a class as a value).
  Left in as it is, its unannotated parameters would make Pystachy reject the class
  (`parameter 'iterable' of method __new__() has no type annotation`); annotated, it would
  compile and never run, as Pystachy does not call the `__new__` of an imported module's class.
- The `key` property (`@property`, always `None` here) is dropped.
- `self.__class__(...)` becomes `SortedList(...)` in `copy`, `+` and `*` (a class as a value),
  and `__repr__` writes `SortedList` where upstream reads `type(self).__name__`.

**M3, functions as values ([#8](https://github.com/den-run-ai/pystachy/issues/8)).**

- `reduce(iadd, self._lists, [])`, which concatenates the sublists (5 places), becomes
  `_concat(self._lists, [])`, a module function added before the class: it stands in for
  `operator.iadd` as a value and for `functools.reduce` (M6).
- Eight method aliases in the class body (`_clear = clear`, `_update = update`,
  `_getitem = __getitem__`, `bisect = bisect_right`, `_bisect_right = bisect_right`,
  `__copy__ = copy`, `__radd__ = __add__` and `__rmul__ = __mul__`) become two-line defs that
  call the method: Pystachy rejects a class attribute bound to a function ("cannot infer the
  type of class attribute"). The defs call through `self`, so a subclass's override of
  `update` or `bisect_right` would reach `_update` or `bisect`, where upstream's aliases keep
  `SortedList`'s methods; no subclass compiles here (inheritance, M2), and Pystachy rejects
  `SortedList.update(self, ...)`.
- Bound methods kept in locals (`_add = self.add` in `update`, `_pos = self._pos` in `islice`)
  are called through `self`.
- `__init__` loses `key=` (and `assert key is None`): a key function is a function as a value,
  and `SortedKeyList`, which uses it, is not ported.
- `__make_cmp`, a function in the class body that builds `__eq__`, `__ne__`, `__lt__`, `__gt__`,
  `__le__` and `__ge__` as closures over `operator.eq` and its siblings, gives way to six defs.
  The closures take any `Sequence` and return `NotImplemented` for anything else (M4,
  [#9](https://github.com/den-run-ai/pystachy/issues/9)); the defs take a `SortedList` (or
  `None`, which `==` and `!=` find unequal, as CPython does after `NotImplemented`). Each
  compares the two lists of values, which compare item by item and then by length, as the
  closures do. Without them a class has no `__eq__`, and Pystachy, like CPython, compares two
  sorted lists by identity: `a == a.copy()` would be `False`, and so would `b in [a]` for a `b`
  equal to `a`. With them, `==`, `in`, `count()` and `index()` of lists of sorted lists,
  `sorted()`, `min()` and `max()` give CPython's results.
- `@recursive_repr()` is dropped from `SortedList.__repr__` and `SortedKeyList.__repr__`: a
  decorator that wraps the method in a closure when the class is created, against a list that
  contains itself, which a list of ints cannot.

**M6, native standard-library hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11)).**

- The imports of `traceback` (used only by `_check`'s error report), `itertools` (`chain`,
  `repeat`, `starmap`) and `textwrap` (used only for `__make_cmp`'s docstrings) are dropped, and
  so is the Python 2/3 shim, which imports `functools.wraps` and `reduce` and
  `_thread.get_ident` (`wraps` and `get_ident` serve only `recursive_repr`) after a
  `sys.hexversion` test that Pystachy rejects (folding version tests is M1,
  [#6](https://github.com/den-run-ai/pystachy/issues/6)).
- `__iter__` returns `iter()` of a list of the values instead of
  `chain.from_iterable(self._lists)`; Pystachy's `__iter__` steps through a list, a tuple, a
  `str` or such an object (see the deviation below).
- `_build_index` builds the same rows without `map(len, ...)`, `starmap(add, zip(head, tail))`
  over one iterator taken twice, `repeat(0, n)` and `reduce(iadd, reversed(tree), self._index)`
  (5 places, each marked): comprehensions over pairs of indices, `[0] * n` and a loop of
  `extend`.
- `_islice` returns one list of the values between its two index pairs, made by slicing the
  first and last sublists, instead of one of six `chain`s of
  `map(sublist.__getitem__, range(...))` (M3, M7 too): the same values in the same order,
  reversed with `list.reverse()` for `reverse=True`.

**M7, the long tail ([#12](https://github.com/den-run-ai/pystachy/issues/12)).**

- `str.format` becomes `%` in the 8 error messages and in `__repr__`
  (`'{0!r} not in list'.format(value)` is `'%r not in list' % (value,)`).
- `irange`, `islice` and `_islice` return a `list[int]` instead of an iterator (Pystachy takes
  `Iterator[T]` only as what `__iter__` returns), and their `return iter(())` are `return []` (6
  places). `list()`, `for` and `sum()` of what they return see the same values, once (see the
  deviation below).
- `del xs[:]` and `del xs[a:]` (8 places, 6 marks) become `xs.clear()` or a slice of the part
  kept; `self._index[:] = row` (2 places in `_build_index`) becomes `clear()` and `extend()`, in
  place, as `_pos` holds `self._index` across the call; and `slice(start, stop).indices(len)` in
  `islice` becomes `_slice_indices()`, a module function that clamps the bounds the same way.
  `__getitem__` and `__delitem__` take an `int`: their slice branches stay in the source and are
  compiled out.

## What compiles as it is

The rest of `SortedList`: the sublist algorithms (`add` with `insort`, `_expand`'s split at
twice the load factor, `_delete`'s merge below half of it, `_loc` and `_pos`'s walks over the
index tree, `bisect_left`, `bisect_right`, `count` and `index` over the sublists, `pop`,
`__getitem__`'s and `__delitem__`'s fast paths, `_reset`), `bisect_left`, `bisect_right` and
`insort` of `lib/bisect.py` (CPython's, unmodified), `math.log(x, 2)`, the `collections.abc`
import in its `try`/`except ImportError`, the `operator` import, generator expressions given to
`list.extend()` and `sum()`, keyword arguments (`reverse=True`), a tuple default
(`inclusive=(True, True)`), tuple results and unpacking, chained comparisons,
`del self._lists[pos]`, `__contains__`, `__len__` (and the truth of a sorted list by it), `+`,
`+=`, `*`, `*=`, `__repr__` and `str()`, the `NotImplementedError` of `append`, `extend`,
`insert`, `reverse` and `sl[i] = v`, and the module's other code: `recursive_repr`, `identity`,
`SortedKeyList`'s class statement and `SortedListWithKey = SortedKeyList`.

## What the port leaves out

- Values that are not `int`: `SortedList(["b", "a"])` is rejected (`expected int, got str`).
- Iterables that are not `list[int]`, where upstream takes any: `SortedList(range(3))`,
  `SortedList(other)` and `sl + other` of a sorted list `other` are rejected; pass `list(...)`.
- Comparisons with a list or another sequence: `sl == [1, 2, 3]`
  (`expected SortedList, got list[int]`), `[1, 2, 3] == sl` and `sl < [1, 2]` are rejected;
  compare `list(sl)`.
- `key=`, `SortedKeyList` and `SortedListWithKey` (rejected where used: class inheritance),
  `SortedDict` and `SortedSet`, and so `from sortedcontainers import *`, as `__all__` still
  names them.
- Slices (`sl[a:b]`, `del sl[a:b]`), `reversed(sl)`, `iter(sl)`, `tuple(sl)` and `set(sl)`
  (`for`, comprehensions, unpacking, `list()`, `sorted()`, `sum()`, `min()`, `max()`,
  `enumerate()` and `zip()` step through a sorted list), `next()` of what `irange` and `islice`
  return, and the reflected operators `[1] + sl` and `2 * sl`, which Pystachy does not send to
  `__radd__` and `__rmul__` (calling those works): each is rejected at compile time.
- `_check()`, whose error report prints with `traceback` (`name 'traceback' is not defined`,
  where a program calls it; `tests/port_sortedcontainers_index.py` checks the same invariants
  itself), and `__reduce__` (pickling).

## Deviations it hits

- **`int` is 64-bit** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  Values at both ends of the range work, as the code only compares them; the tests use 2**63 - 1
  and -2**63. An index of -2**63 does not: `sl[-2**63]`, `sl.pop(-2**63)` and `del sl[-2**63]`
  raise `OverflowError: integer result does not fit in 64 bits` where CPython raises
  `IndexError: list index out of range`, as `_pos` computes `-idx`. Every other index out of
  range, -2**63 + 1 and 2**63 - 1 included, raises CPython's `IndexError`.
- **`str` is UTF-8 bytes**: not hit. The values are ints, and the only strings are the error
  messages and reprs of ints, which are ASCII.
- **Iteration is over a copy**, a deviation of this port rather than of Pystachy: `for v in sl`
  steps through the values as they were when the loop started, where upstream's
  `chain.from_iterable` reads the sublists as it goes. After

  ```python
  sl = SortedList([1, 2, 3, 4, 5])
  out: list[int] = []
  for v in sl:
      out.append(v)
      if v == 2:
          sl.add(100)
  ```

  `out` is `[1, 2, 3, 4, 5]` here and `[1, 2, 3, 4, 5, 100]` under CPython. Upstream's docstring
  says that iterating while adding or deleting values "may raise a RuntimeError or fail to
  iterate over all values", so a program should not rely on either.
- **`irange()` and `islice()` return lists**, made when they are called, where upstream returns
  iterators (M7 above): Pystachy has no other way for a method to return an iterator. A program
  that takes their values once, with `list()`, `for` or `sum()`, sees the same values. One that
  does more sees other results, without an error:
  - A second pass over the result sees the values again, where upstream's iterator is used up
    and gives none: after `r = sl.irange(2, 4)` on `SortedList([1, 2, 3, 4, 5])`,
    `sum(r), sum(r)` is `(9, 9)` here and `(9, 0)` under CPython. Likewise, a loop that leaves
    the result with `break` and a later loop over it start again at the first value, where
    upstream's second loop goes on after the last value the first one took.
  - An empty result is false (`if sl.irange(lo, hi):`) and equals `[]`; an iterator is always
    true and equals no list.
  - `len()`, indexing, `reversed()` and the list's methods work on the result, where CPython
    raises `TypeError` (`object of type 'map' has no len()`) or `AttributeError`.
- **Ordering against `None`** raises another message: `sl < None` raises
  `TypeError: 'NoneType' object is not iterable`, where CPython raises
  `TypeError: '<' not supported between instances of 'SortedList' and 'NoneType'`.

## Tests

`tests/port_sortedcontainers_api.py` runs the examples of the docstrings, with ints for their
letters, then edge cases: an empty list (every lookup, and the `IndexError` and `ValueError` of
`pop`, `remove`, `sl[0]`, `index` and `del`), duplicates, negative values and both ends of the
64-bit range, `index()` with negative and empty `start`/`stop`, every `inclusive` and `reverse`
form of `irange`, `islice` with negative and out-of-range bounds, indices out of range by one
and at 2**63 - 1 and -(2**63 - 1), copies, `+`, `+=`, `*` (by 0 and by -3), `*=`, the methods
that raise `NotImplementedError`, and the comparisons: `==` and `!=` of copies, ordering by item
and by length, `in`, `count()` and `index()` of lists of sorted lists, also with `None` among
them, `sorted()`, `min()` and `max()` of sorted lists, sorted lists inside tuples and dicts, and
`==` and `remove()` of lists of optional sorted lists; then the methods called with keyword
arguments, by upstream's parameter names, also through the aliases written as defs.
`tests/port_sortedcontainers_index.py` gives about 200 values a load factor of 4 (`_reset(4)`),
so they split into dozens of sublists: it prints the sublists' sizes, `_offset` and the index
tree, and checks `SortedList._check`'s invariants, after positional reads, adds that split
sublists, removes and deletes that merge them, pops at both ends and inside, `update`'s two
paths (value by value, and a rebuild), `irange` and `islice` across many sublists, and 2,100
adds at the default load factor, which split one sublist.

`tests/run.sh` compares what they print with CPython's, JIT and AOT. Run under CPython against
the unmodified upstream package, both print exactly what they print against this port. Both are
small: with the native compiler, the JIT runs take 0.3 s each and the AOT builds 1.6 s and 1.1 s
of CPU time (the executables run in under 0.01 s); under `make verify`'s gc-stress stage (the
compiler collecting every 1,000 allocations, the program at every allocation: 1,853 and 2,660
collections), the JIT run and the AOT build and run take 2.2 s and 1.5 s of CPU time in all
(2.9 s and 2.1 s by the clock, medians of 3 on the VM below at a load average of 10 to 15).

## Speed

The headline workload: a running median and rank over a sliding window of 50,000 values, in a
stream of 400,000 values from a linear congruential generator (400,000 `add`, 350,000 `remove`,
a median `sl[n // 2]` and a `bisect_left` per value, and a `count` and an `irange(v, v + 1000)`
every 1,000 values), then 49,990 `pop(len(sl) // 2)`. Median of 3 runs, with process start-up,
on a 4-core x86-64 VM shared with other jobs:

| | wall | CPU |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.193 s | 0.180 s |
| CPython 3.13.16, unmodified sortedcontainers 2.4.0 | 1.733 s | 1.720 s |

That is 9.0 times faster by wall clock and 9.6 times by CPU time. Runs while the VM was busier
took longer by the clock (0.295 s against 2.566 s) and the same CPU time (0.180 s against
1.740 s). Both print the same checksums. The executable is about 100 KB and links only libc,
libm and libgcc_s. sortedcontainers has no C extension, so CPython runs it in the interpreter;
this does not compare it with C libraries of sorted containers.
