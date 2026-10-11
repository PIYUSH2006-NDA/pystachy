# ordered-set 4.1.0, ported to Pystachy

[ordered-set](https://pypi.org/project/ordered-set/) gives Python an `OrderedSet`: a mutable set
that remembers the order in which its items were added, so that each item has an index, as in a
list. It keeps the items in a list and a dict from each item to its index: `add()` returns the
index, `index()` (also `get_loc()` and `get_indexer()`, for compatibility with pandas' `Index`)
and `in` are dict lookups, and the set algebra keeps the order of the first operand. It is the
usual way to deduplicate while keeping order, or to number the distinct values of a stream. It
is rank 662 on PyPI in October 2026. deepdiff (rank 402) required it up to version 7 (deepdiff
8 moved to orderly-set, by deepdiff's author), and setuptools vendored its version 3.1
(`setuptools/_vendor/ordered_set.py`, in setuptools 65.5.0 for one).

This port is `OrderedSet` of `str`. `__init__.py` is the one module of the sdist
`ordered-set-4.1.0.tar.gz` (SHA-256
`694a8e44c87657c59292ede72891eb91d34131f6531463aab3009191c77364a8`), which is MIT licensed
(`LICENSE` is the sdist's `MIT-LICENSE` as it is).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `cad6b380ab3204a8bdb85b41b7ddfcc97c50b5d6add55082ebcd6cf6cd0232a8` | 50 marked edits in 29 diff hunks |

`py.typed`, the empty marker file that tells type checkers the package is typed, is left out, and
so are the sdist's packaging files, its README and its tests. Every edit is marked
`# Pystachy port:` in the source, and `diff -ru` against the sdist's `ordered_set/` shows them
all. They change no algorithm: `items` and `map` hold under Pystachy what they hold under
CPython, step by step (the tests print `map`).

## The edits, and the feature each one stands in for

**M2, full classes ([#7](https://github.com/den-run-ai/pystachy/issues/7)).**

- `class OrderedSet(MutableSet[T], Sequence[T])` loses its two bases (inheritance), and `str`
  stands in for `T` in the two fields and in every signature: Pystachy has no generic classes,
  and rejects a method that mentions a `TypeVar` ("method 'copy' of class 'OrderedSet' mentions
  TypeVar 'T', which is not supported"). M2's classes as templates would compile the methods for
  each item type. The `"OrderedSet[T]"` return annotations are `"OrderedSet"`.
- `__init__`'s `self |= initial` called `MutableSet.__ior__`, which adds the items one by one:
  it calls `self.update(initial)`, which does the same.
- The methods upstream leaves unannotated get annotations: `__len__` (`-> int`, as Pystachy
  reads a missing return annotation as `-> None`), `__getitem__`, `index`, `pop`, and
  `__setstate__`, which only pickling calls: Pystachy rejects a class as a whole, where a program
  uses it, if one of its methods has an unannotated parameter. `_update_items`'s bare `list` is
  `List[str]`.
- `self.__class__` (a class as a value) is `OrderedSet` in `copy()`, in `__repr__`
  (`OrderedSet.__name__`) and in the set algebra (`cls`). `update()`'s `ValueError` message
  has `"<class 'list'>"` for `type(sequence)`; the argument is a list now, and iterating a list
  of `str` raises no `TypeError` anyway.
- `__getitem__` and `index` lose the branch that takes a list of indices or keys and returns a
  list: it tests `isinstance(x, Iterable)` with typing's ABC, which Pystachy does not take (M2's
  `isinstance` over ABCs), and the method's result would be a `str` or a list (M4). Their other
  branches stay: for an `int`, Pystachy decides `isinstance(index, slice)` and
  `hasattr(index, "__index__")` at compile time and compiles only the branch that runs.
- `__eq__` tested `isinstance(other, Sequence)`, true for an `OrderedSet` by its base; Pystachy
  decides it by the static type, and without the base it would be false, so the test is
  `other is not None` (below, under M7, for `None`).

**M3, functions as values ([#8](https://github.com/den-run-ai/pystachy/issues/8)).**

- Three method aliases in the class body, `append = add`, `get_loc = index` and
  `get_indexer = index`, become defs that call the method: Pystachy rejects a class attribute
  bound to a function.
- `union`, `intersection`, `difference` and `difference_update` take `*sets` (`*args` in a
  method); each takes one list. `union` built its items with
  `it.chain.from_iterable(map(list, it.chain([self], sets)))`, which is `list(self) + other`
  for one list (M6 too).

**M4, dynamic values ([#9](https://github.com/den-run-ai/pystachy/issues/9)).**

- `Any` becomes `str` in `__contains__` and `"OrderedSet"` in `__eq__`.
- The module's two aliases, `SetLike = Union[AbstractSet[T], Sequence[T]]` and
  `OrderedSetInitializer`, which adds `Iterable[T]`, are dropped: Pystachy rejects `Union` used
  as a value ("unsupported module attribute typing.Union"). The 12 signatures that use them take
  a `List[str]` (`__init__` also `None`, its default), so `copy()` and `symmetric_difference()`,
  which passed an `OrderedSet` along, pass `self.items` or `list(...)` of it.
- `__getitem__` and `index`: see M2.

**M6, native standard-library hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11)).**

- `import itertools as it` is dropped; `union` was its only user (see M3).

**M7, the long tail ([#12](https://github.com/den-run-ai/pystachy/issues/12)).**

- The set algebra and the `*_update` methods make a `set` of the other items to test membership
  against: an `OrderedSet` of them stands in (5 places), with the same dict lookup behind `in`.
  The generator expressions they gave to `cls(...)` are list comprehensions.
- `__eq__` compared as sets when `other` is no sequence. Of the values an `OrderedSet` parameter
  holds, only `None` gets there, where `set(None)` raised `TypeError` and `__eq__` returned
  `False`: the port returns `False`.
- `_update_items`'s dict comprehension is a loop.
- `clear()`'s `del self.items[:]` (a del of a slice) is `self.items.clear()`.
- `SLICE_ALL = slice(None)` (a slice object) is dropped. Only the slice branch of `__getitem__`
  reads it, which neither Pystachy nor CPython reaches with an `int` index.

## What compiles as it is

The rest of the module: `add`, which returns the new or existing index; `update`, its
`try`/`except TypeError` and its result (the index of the last item, 0 for an empty list);
`index` and `__contains__` through the dict; `pop` with `del self.items[index]` and its
`KeyError("Set is empty")`; `discard`, whose loop over `self.map.items()` decrements the indices
after the one removed while it iterates; `clear`; `__iter__`, which returns `iter(self.items)`;
`__repr__`'s `%r` of a list; `issubset` and `issuperset`, with their length test and `all()`
over generator expressions that iterate the set; `symmetric_difference_update`; `__and__`; the
`@overload` stubs; the `typing` imports and `T = TypeVar("T")`; `_is_atomic` (nothing calls it
now); `__getstate__` and `__setstate__` (Pystachy has no `pickle`); and the docstrings. A
program can take the truth of a set (by `__len__`), test `in`, and iterate it in `for` loops,
comprehensions, `list()`, `sorted()`, `min()`, `max()`, `enumerate()`, `zip()`, `str.join()` and
`list.extend()`, and `==`, `!=`, `in`, `index()` and `count()` of lists of sets call `__eq__`.

That includes a bug of 4.1.0: `pop(i)` for an `i` before the last item deletes it from `items`
and `map` but leaves the indices in `map` of the items after it as they were, where `discard()`
decrements them. After `c = OrderedSet(["p", "q", "r", "s", "t"])` and `c.pop(1)`,
`c.index("t")` is 4, `c.discard("s")` deletes `"t"` (`items[3]`) and leaves `"s"`, which `in`
then no longer finds, and `c.pop()` raises `KeyError: 's'` after it has removed `"s"` from
`items`. The port does all this as upstream does; the tests check it.

## What the port leaves out

- Items that are not `str`: `OrderedSet([1, 2])` is rejected (`expected str, got int`).
- Arguments that are not a `list[str]`, where upstream takes any iterable, set or sequence:
  `OrderedSet("abc")` (`expected list[str] | None, got str`; pass `list("abc")`, but see the
  deviation below), `OrderedSet(other)` and `a.union(b)` of an `OrderedSet` `b`
  (`expected list[str], got OrderedSet`; pass `list(b)`), sets, tuples and generators. `union`,
  `intersection`, `difference` and `difference_update` take exactly one list: chain the calls
  for more, and use `copy()` for none.
- What the `MutableSet` and `Sequence` bases supplied: `remove()`
  (`'ordered_set.OrderedSet' object has no method 'remove'`), `isdisjoint()`, `count()`, the
  operators `|`, `-`, `^`, `<`, `<=`, `>` and `>=` and the in-place `|=`, `&=`, `-=` and `^=`,
  and `isinstance()` against those ABCs. The class defines `__and__`, but Pystachy does not send
  `&` to an object's method yet (`unsupported operand type(s) for &: 'OrderedSet' and 'list'`):
  call `a.intersection(b)` or `a.__and__(b)`.
- `==` with a list, tuple or set (`expected OrderedSet, got list[str]`): compare `list(s)`.
- Slices and lists of indices (`s[1:3]`, `s[[1, 2]]`: "slicing an object is not supported"),
  `index()` of a list of keys (`expected str, got list[str]`), `reversed(s)` (Pystachy rejects
  `reversed()` of an object; `reversed(list(s))` works), and pickling.

## Deviations it hits

- **`str` is UTF-8 bytes** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  Items are hashed and compared whole, so sets of any text behave as in CPython: the tests use
  `é`, `€`, `😀`, a zero-width space, `Ω≈ç`, NUL and DEL as items and `ünï` as a missing key.
  What a program computes from a `str` itself counts bytes, as `len()` of an item does. The
  idiom of upstream's tests, `OrderedSet("abracadabra")`, spelled `OrderedSet(list(...))` here,
  makes a set of the bytes of non-ASCII text: `OrderedSet(list("naïve café"))` has 10 items (the
  UTF-8 bytes of `ï` and `é`, whose first byte, 0xC3, they share, in place of the two letters)
  where CPython's has 9, and `"é" in` it is `False`. ASCII text is not affected.
- **`int` is 64-bit.** The only ints are indices and lengths, and indices at both ends of the
  range work: `s[i]` and `s.pop(i)` for `i` = 2**63 - 1, -(2**63 - 1) and -2**63 raise CPython's
  `IndexError: list index out of range` (the tests check them). A program cannot make a bigger
  index: `s[2 ** 63]` raises `OverflowError: integer result does not fit in 64 bits` computing
  `2 ** 63`, where CPython raises `IndexError: cannot fit 'int' into an index-sized integer`.

## Tests

`tests/port_ordered_set_api.py` runs the cases of ordered-set's own test suite
(`test/test_ordered_set.py` of the sdist, run under pytest there) and the examples of its
docstrings as a program, with `str` items: order, `!=`, the set algebra as methods (`&` as
`__and__()`), copies and identity, `index()` and its `KeyError`, `get_loc()` and
`get_indexer()`, `discard()` in place of `remove()`, `clear()`, `update()`'s results, `pop()`
down to its `KeyError`, the empty repr, and the operator consistency checks: the `*_update`
methods against the methods that return a new set (equal results, distinct objects) and
`issubset()` and `issuperset()` against a direct test, over upstream's four fixed pairs, 20
pairs of 20 pseudo-random items (a linear congruential generator in place of
`random.Random(0)`) and the pair of `test_bitwise_and_consistency`. It leaves out what the port
leaves out (pickling, slices, fancy indexing, tuple items, `remove()`, the operators, and
comparisons with lists, tuples, deques, sets, dicts and iterators).

`tests/port_ordered_set_edges.py` takes the edge cases that the evaluation of this port met and
that its independent check added: the empty set (each lookup and its error, the set algebra);
quotes, escapes, 2-, 3- and 4-byte UTF-8, NUL, DEL, a zero-width space and the empty string as
items, in the repr and as `KeyError`s; indices out of range by one and at 2**63 - 1,
-(2**63 - 1) and -2**63, for `s[i]` and `pop(i)`; what `add()`, `append()` and `update()`
return; `pop(1)` and what `index()`, `discard()`, `s[i]` and `pop()` do after it (above);
`discard()`'s reindexing; duplicates in the lists the set algebra takes (`issuperset()` of
`["a", "a", "a", "a"]` is `False` for a set of 3, by its length test, and
`symmetric_difference_update()` with a duplicate puts it in `items` twice); `==` and `!=` with
copies, reorderings and `None`, and `in`, `index()` and `count()` of lists of sets; iteration in
the forms listed above; and 3,000 tokens deduplicated, with `index()` of each, 143 `discard()`s
and the lookups again.

`tests/run.sh` compares what they print with CPython's, JIT and AOT. Run under CPython against
the unmodified upstream package, both print exactly what they print against this port. Both
pass JIT and AOT with `PYSTACHY_IRCHECK=1`, with the native compiler (also with
`PYSTACHY_OPT=-all`) and with the CPython-hosted one; `tools/check_ir.sh` accepts their IR, and
`tests/run.sh` passes as a whole (1,935 passed, 0 failed). They are small: with the native
compiler, each JIT run takes 0.2 s (0.12 s of CPU), the AOT builds 1.3 s and 1.4 s (1.0 s and
1.1 s of CPU), and the executables run in 0.005 s. In `make verify`'s gc-stress form (the
compiler collecting every 1,000 allocations, the program at every allocation), the JIT run and
the AOT build and run of `port_ordered_set_api` take 1.7 s in all (1.3 s of CPU), and those of
`port_ordered_set_edges` 3.5 s (1.5 s of CPU): medians of 3 on a VM that was running other jobs
(load 9 to 13 on its 4 cores).

## Speed

The headline workload: 600,000 tokens from a linear congruential generator (`"tok%d"` of 60,000
values) deduplicated into an `OrderedSet` of 59,998, `index()` of each of the 600,000, 200
`discard()`s (each walks the 59,998 entries of `map` to decrement the indices after the one it
removes), then `in` and `index()` of each token again. Median of 3 runs, wall clock with process
start-up and CPU time, on a 4-core x86-64 VM that was running other jobs (load 13):

| | wall clock | CPU |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.448 s | 0.307 s |
| CPython 3.13.16, unmodified ordered-set 4.1.0 | 2.395 s | 1.704 s |
| CPython 3.13.16, this port | 1.906 s | 1.294 s |

All three print the same checksums. The executable is 5.6 times faster than CPython on upstream
in CPU time (5.3 times in wall clock), and 4.2 times faster than CPython on the same edited code.
A second set of runs, at load 14, took 0.297 s, 1.638 s and 1.287 s of CPU (0.608 s, 2.563 s and
1.984 s of wall clock).

Part of the difference comes from an edit: upstream's `index()` first tests
`isinstance(key, Iterable)` against typing's ABC, 1.2 million times here, and the port drops
that branch (M2, M4 above); CPython running upstream with only those two lines removed takes
1.26 s of CPU, as it does on the port. ordered-set has no C extension, so CPython runs it as
Python everywhere. The executable is 72 KB and links only libc, libm and libgcc_s. The
evaluation that made the port measured, in wall clock, 0.30 to 0.34 s for the executable, 1.58
to 1.78 s for CPython on upstream and 1.30 s for CPython on the port.
