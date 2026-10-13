# lib/: standard library modules for Pystachy

A program's `import NAME` finds `NAME.py` or `NAME/__init__.py` next to the program, then on
`PYSTACHY_PATH`, then here (Pystachy's builtin modules, `sys`, `os`, `math` and the others
listed in [docs/language.md](../docs/language.md#builtins-and-library-modules), come first). The modules here are **unmodified** copies of CPython
3.13.16's pure-Python standard library modules that Pystachy compiles as they are: their
unannotated functions are templates, compiled for the argument types of each call, and the
code they never run (CPython's C accelerators, generators) is never compiled. `tests/lib_*.py`
checks each against CPython.

| module | from CPython 3.13.16 | SHA-256 | what works |
|---|---|---|---|
| `bisect` | `Lib/bisect.py` | `f1cf7b85fc36b5da249813fc5ab97d9464f8cc1bc817f7146206fa2713e35999` | everything, `key=` too (a function of the program or a builtin, compiled into each call) |
| `colorsys` | `Lib/colorsys.py` | `65e3dfbf7bad61d4d7d7731a69dd7e75a347fd350d91327a51010a94e6fd2f1d` | everything |
| `operator` | `Lib/operator.py` | `c048f8a6852832d5fa750d6ae772d7658c52c3511d261cb902f7edfd262e9127` | the operator functions; not `attrgetter`, `itemgetter`, `methodcaller` (class templates whose `_call` field holds a closure of `__init__`, which a field's type cannot be inferred from), `call`, `length_hint`, `index`; the in-place functions only where the result keeps its type (`itruediv(1, 2)` would rebind an int to a float) |
| `stat` | `Lib/stat.py` | `07217986d9b2172b509dab3578d18ac05ba768b418e1f1e8c90e38a8f7c2b3c6` | the constants and `S_IS*()`, `S_IMODE`, `S_IFMT`; not `filemode` (it iterates a tuple of tuples of different lengths) |
| `this` | `Lib/this.py` | `481d0cb3de511eae0b5713dad18542b07eafd9c013bb7690f7497bad49923a71` | everything (it prints the Zen of Python) |
| `posixpath` | `Lib/posixpath.py` | `69acb9e294987cd6056a2237048373cf8d6201faf1e43a49c38889b47d2fb28e` | the constants and `normcase`, `isabs`, `split`, `splitext`, `splitdrive`, `splitroot`, `basename`, `dirname`, `normpath` on `str` paths; not `join`, `relpath`, `commonpath`, `abspath`, `expanduser`, `expandvars`, `realpath`, `exists` and the other file tests (`try`, `*args`, `map`, `os.environ`, `re`) |
| `genericpath` | `Lib/genericpath.py` | `cdac5a68dd738051e0d66fc81d5947d6a1776248fc6fe862253477608d870ec4` | what `posixpath` uses of it; not `commonprefix` (`map`) or the file tests (`try`) |
| `curses.ascii` | `Lib/curses/ascii.py` | `780dd8bbaf0ee7e832f164c1772953e694a9cd1031d1ab1471af65344d3645e6` | everything, for ASCII characters (strings are byte strings) |

`curses/__init__.py` is Pystachy's own stand-in: CPython's wraps the C extension `_curses`.

## `heapq`, with `nlargest()` and `nsmallest()` ported

`heapq.py` is CPython 3.13.16's `Lib/heapq.py` (SHA-256
`6d43277e5c76fc0f073cd388fcff852d14d068f6bb6d4886c340f8b75a1229a9`) with `nsmallest()` and
`nlargest()` edited, each edit marked `# Pystachy port:`; the rest of the file is CPython's byte for
byte. It has `heappush`, `heappop`, `heapify`, `heapreplace`, `heappushpop` and the `_max`
variants, as CPython's code, and `nlargest()` and `nsmallest()`, with and without `key=`, of a list
or of another iterable the subset passes (a tuple, a str, a dict, a set, `d.items()`, an object
with `__iter__`, with or without `__len__`), as CPython's algorithm: the same heap operations, so
the same comparisons and calls of `key` in the same order, and the same ties, as the
`(elem, order)` and `(key, order, elem)` tuples keep the input's order among equal items.

The edits, the same in both functions:

- `it = iter(iterable)` is `iterable` itself for a list, else a list of its items: the subset has
  no iterators. The list is a comprehension, `[elem for elem in iterable]`: `list(iterable)` would
  call an object's `__len__` (its length hint), which `iter()` does not.
- For n of 1, `min(it, default=sentinel, key=key)` with an `object()` sentinel is
  `[min(it, key=key)] if it else []`: the subset has neither `object()` nor `default=`.
- In `try: size = len(iterable)`, the `TypeError` of an iterable without `__len__` is raised before
  `len()`, under `if not hasattr(iterable, '__len__')`, which the argument's type decides: `len()`
  of an object without `__len__` is a compile-time error. A `__len__` that raises `TypeError` is
  caught, as in CPython.
- `zip(range(n), it)` (`range(0, -n, -1)` in `nlargest()`), which takes the first n items, is a
  comprehension over `range(min(n, len(it)))` that indexes `it`: `range()` cannot be nested in
  `zip()`. The loop over the other items, which goes on with `zip()`'s iterator in CPython, is
  `for i, elem in enumerate(it)`, which skips the first n: a list is read in place, as CPython's
  iterator reads it, with no copy.
- An empty `result` returns `[]`, not `result`: its tuples are not of the items' type, which the
  function returns elsewhere.

Where it differs from CPython:

- The items of an iterable other than a list are taken into a list first, so a `key` or a
  comparison that changes the dict or set being read does not raise CPython's `RuntimeError`.
- For an n above 2,500 that is less than the length, `heapify()` of the decorated items compares
  in another order than CPython's `_heapq` does (see the end of this page), with the same result.

`merge()` is an error where a program calls it: it is a generator. So is an open file as the
iterable of `nlargest()` or `nsmallest()`, as `hasattr()` of a file is not supported (its
`readlines()` is an argument), and a generator expression, which the subset has only as the
argument of `list()`, `sorted()`, `sum()` and the like (`list()` of it is an argument).

`tests/lib_heapq_topk.py` compares them with CPython's on ints, floats, strs and tuples, n of -1,
0, 1, 2, the length and around it, empty input, `key=` (a lambda, a function, a builtin,
`str.lower`, a bound method), ties, the iterables above, and objects whose `__lt__`, `__eq__`,
`__iter__` and `__len__` log their calls, so that the comparisons are CPython's, in its order. Run
by CPython, the edited module passes CPython's `Lib/test/test_heapq.py` (51 tests), and its
`nlargest()` and `nsmallest()` make the same comparisons and calls of `key`, with the same results,
as CPython's own in 36,000 calls on random inputs with many ties (lists, tuples and an object
without `__len__`, n from -2 to past the length, with and without `key`).

In an AOT executable, `nlargest(10, xs)` and `nsmallest(10, xs)` of 100,000 ints take 45 and
47 µs, against CPython's 1,970 and 1,936 µs: most items are only compared with the heap's top, an
int comparison in the compiled loop, where CPython steps an iterator and calls a rich comparison
for each; `nlargest(10, pairs, key=second)` of 100,000 `(str, int)` tuples takes 108 µs (CPython:
4,263 µs). Where the heap does more of the work the gain is smaller: `nsmallest(1000, xs)` takes
867 µs (CPython: 3,363 µs), most of it replacing and sifting `(elem, order)` tuples, and
`nlargest(1, xs)`, `max()` of the list, 234 µs (CPython: 590 µs). The `sorted()` that an n at or
past the length takes is slower than CPython's: 38 µs for 1,000 ints (CPython: 27 µs), whose sort
compares ints with a function of their own, where Pystachy's compares through a descriptor of the
items' type. (Medians of 3
runs, each the median of 5 rounds of 20 calls, 2,000 for 1,000 ints, on items from a linear
congruential generator.) [`examples/topk`](../examples/topk/README.md) picks the most frequent
words of a text with them.

## `re`, a port of CPython's

`re/` is no copy: CPython's `re` is a pure-Python parser and compiler (`Lib/re/_parser.py` and
`_compiler.py`) over the C matching engine `_sre` (`Modules/_sre/`), and neither compiles as it
is (the parser's tuples of mixed types, and C). `re/__init__.py` ports CPython 3.13.16's
`Lib/re/__init__.py`, `_parser.py` and `_compiler.py` to the subset, and `re/_sre.py` ports the
engine of `sre_lib.h` and `sre.c` op for op, with its explicit stack of match contexts. They make
CPython's code of a pattern and run it as CPython's engine does, so a pattern matches, splits
and substitutes as in CPython, and raises CPython's errors, with their messages and positions.
`re/_constants.py` holds `Lib/re/_constants.py`'s numbers, and `re/_unicode.py`, which
`tools/re_tables.py` generates from CPython's own Unicode functions, the tables `_sre` reads
(`\w`, `\d`, `\s`, line breaks, the case mappings and `_casefix.py`'s extra cases), and the
identifier characters a group name may have.

It has `compile`, `match`, `fullmatch`, `search`, `findall`, `finditer`, `split`, `sub` and
`subn` (with a template or a function as the replacement), `escape`, `purge`, the flags, and
`error` with `msg`, `pos`, `lineno` and `colno`; `Pattern`'s methods, also with `pos` and
`endpos`, its `pattern`, `flags`, `groups` and `groupindex`, and `==`; `Match`'s `group()` (of up
to 5 groups at once), `m[g]`, `groupdict()`, `start()`, `end()`, `span()`, `expand()`, `pos`,
`endpos`, `lastindex`, `lastgroup`, `re` and `string`; and the reprs. It has all of 3.13's syntax:
classes, greedy, lazy and possessive repeats, named groups, backreferences, lookahead and
lookbehind, conditional and atomic groups, inline and scoped flags, the `\x`, `\u`, `\U` and
octal escapes, and Unicode's `\w`, `\d`, `\s`, `\b` and case folding. A string is matched
character by character (code point by code point). Where it differs from CPython
(`tests/deviations/lib_re.py`):

- A position (`pos`, `endpos`, `start()`, `end()`, `span()`, an error's `pos`) is an index into
  the str, which holds UTF-8, as slicing and `find()` count it: past ASCII, it counts bytes.
- `findall()` of a pattern with 2 groups or more raises `NotImplementedError`, and
  `Match.groups()` and `Match.regs` are errors where the program uses them: their tuples are as
  long as the pattern's group count, which runtime-length tuples (M4) would type.
- `split()` returns a `list[str]`, so it raises `NotImplementedError` for a pattern with a group
  that takes no part in a match, where CPython's list holds `None`. That is the signature's
  choice: a `list[str | None]` would hold it.
- `finditer()` returns a list of the matches, found before it returns.
- `\N{...}` is a pattern error: Pystachy has no table of the characters' names.
- The flags are ints, not `RegexFlag` members; `groupindex` is a dict; `re.error` is the base class
  of the `PatternError` the module raises (CPython 3.13 has one class); a replacement function
  must return a str (CPython's may return `None`); and there is no `DEBUG` output, `Scanner`,
  `__index__` group number, warning or `bytes` pattern.

`tests/lib_re.py` compares it with CPython's `re`. Run by CPython as a package of its own, it
passes CPython 3.13's `Lib/test/test_re.py` but for the cases above, the tests of CPython's
internals (`re._compiler`), of its C types' own behaviour (immutable objects, `copy`, no
instantiation, the `TypeError` of a non-str argument), of str subclasses and of a time limit;
and it makes the same code, errors and results as CPython's `re` for 18,000 random patterns,
each matched against 19 strings. With it, unmodified roman 5.2 prints what CPython prints. It
is about 3 times slower than `_sre`.

These modules behave as their pure-Python code, which CPython replaces with C accelerators that
differ at the edges: errors can be worded differently (`heappop([])` raises `IndexError: pop
from empty list` here, `index out of range` from CPython's `_heapq`), keyword arguments the C
functions reject are accepted, `bisect`'s `hi=-1` is a plain bound (`len(a)` for `_bisect`),
`stat`'s tests read the module's constants (`_stat` has its own), and `heapify` of more than
2,500 items calls `__lt__` in another order (`_heapq` switches to a cache-friendly loop).

These files are part of Python and are used under the PSF License Version 2; see
`THIRD_PARTY_NOTICES`. `tools/import_sweep.py` tries every module of a CPython standard library
this way; [`docs/stdlib.md`](../docs/stdlib.md) reports which import and why the others do not.
