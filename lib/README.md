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
| `heapq` | `Lib/heapq.py` | `6d43277e5c76fc0f073cd388fcff852d14d068f6bb6d4886c340f8b75a1229a9` | `heappush`, `heappop`, `heapify`, `heapreplace`, `heappushpop` and the `_max` variants; not `merge` (a generator), `nlargest`, `nsmallest` (`iter`, `key=`) |
| `operator` | `Lib/operator.py` | `c048f8a6852832d5fa750d6ae772d7658c52c3511d261cb902f7edfd262e9127` | the operator functions; not `attrgetter`, `itemgetter`, `methodcaller` (class templates whose `_call` field holds a closure of `__init__`, which a field's type cannot be inferred from), `call`, `length_hint`, `index`; the in-place functions only where the result keeps its type (`itruediv(1, 2)` would rebind an int to a float) |
| `stat` | `Lib/stat.py` | `07217986d9b2172b509dab3578d18ac05ba768b418e1f1e8c90e38a8f7c2b3c6` | the constants and `S_IS*()`, `S_IMODE`, `S_IFMT`; not `filemode` (it iterates a tuple of tuples of different lengths) |
| `this` | `Lib/this.py` | `481d0cb3de511eae0b5713dad18542b07eafd9c013bb7690f7497bad49923a71` | everything (it prints the Zen of Python) |
| `posixpath` | `Lib/posixpath.py` | `69acb9e294987cd6056a2237048373cf8d6201faf1e43a49c38889b47d2fb28e` | the constants and `normcase`, `isabs`, `split`, `splitext`, `splitdrive`, `splitroot`, `basename`, `dirname`, `normpath` on `str` paths; not `join`, `relpath`, `commonpath`, `abspath`, `expanduser`, `expandvars`, `realpath`, `exists` and the other file tests (`try`, `*args`, `map`, `os.environ`, `re`) |
| `genericpath` | `Lib/genericpath.py` | `cdac5a68dd738051e0d66fc81d5947d6a1776248fc6fe862253477608d870ec4` | what `posixpath` uses of it; not `commonprefix` (`map`) or the file tests (`try`) |
| `curses.ascii` | `Lib/curses/ascii.py` | `780dd8bbaf0ee7e832f164c1772953e694a9cd1031d1ab1471af65344d3645e6` | everything, for ASCII characters (strings are byte strings) |

`curses/__init__.py` is Pystachy's own stand-in: CPython's wraps the C extension `_curses`.

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

## `string`, a port of CPython's

`string.py` is CPython 3.13.16's `Lib/string.py` (SHA-256
`c000d9c4340c910b869399f0f0acc1b70e39391ad9344c4e08d8d0f80210a916`) edited in 16 places, each
marked `# Pystachy port:`. It has the constants, `capwords()` and `Template`, as CPython's code:
`substitute()` and `safe_substitute()` with a mapping (a dict, or an object with `__getitem__`),
keyword arguments or both, `is_valid()`, `get_identifiers()`, the `template` attribute, the class
attributes `delimiter`, `idpattern`, `braceidpattern`, `flags` and `pattern`, and the `ValueError`
of an invalid placeholder, with its line and column. Its regular expression is `lib/re`'s.
`Formatter` stays in the file, uncompiled: a program that uses it is an error where it does (it
needs CPython's C module `_string`, whose import is optional here, and sets of mixed items).

- `import _string` is an optional import (`try:` ... `except ImportError: pass`): Pystachy has no
  `_string`, which only `Formatter` uses, and runs the handler; CPython imports it, and its
  `Formatter` works.
- `from collections import ChainMap` is gone (no `collections` here), and so is its one use: where
  `substitute()` and `safe_substitute()` are given no mapping, CPython binds `mapping` to `kws`,
  and where they are given both, to `ChainMap(kws, mapping)`, which a variable of one type cannot
  hold. Their `convert()` looks a name up in `kws` first, then in `mapping`,
  `str(kws[named]) if kws and named in kws else str(mapping[named])`, where an empty `kws` (a
  `**kwargs` record, which the call decides) is not looked in; with no mapping, `mapping` is the
  empty `_sentinel_dict`, whose `KeyError` names the key as CPython's does.
- `_sentinel_dict = {}`, `mapping`'s default, is annotated `dict[str, str]`, as nothing fills it.
- In `Template`'s class body, `braceidpattern` and `flags` are annotated (`str | None`, `int`):
  `None` and another module's variable (`re.IGNORECASE`) give a class attribute no type. `pattern`
  is bound, to `None`, so that the module's code may assign it.
- The module's `Template.__init_subclass__()`, which computes `pattern`, is
  `Template.pattern = _template_pattern()`, a function of `__init_subclass__()`'s lines with
  `Template` for `cls`: Pystachy compiles no `__init_subclass__()`, which calls `super()` and reads
  `cls.__dict__`. CPython still calls it for a subclass.
- `__init__` annotates its parameter (`template: str`), and so `is_valid()` and
  `get_identifiers()` annotate their returns (`-> bool`, `-> list[str]`): with an unannotated
  `__init__`, `Template` is a class template, whose objects compile its special methods,
  `__init_subclass__()` too; with an annotated one, a method without unannotated parameters
  returns `None` unless it says otherwise.
- `capwords()` annotates `sep` as `str | None`: `s.split(sep)` of a template's parameter whose
  argument is `None` is an error, and of an optional `str` it is CPython's default.
- `safe_substitute()`'s `convert()` returns `mo.group() or ''`, a `str` (group 0 is never `None`),
  where `lib/re`'s `group()` is a `str | None`, and `_invalid()` passes `splitlines()` its
  `keepends` by position, as Pystachy takes it.

Where it differs from CPython (`tests/deviations/lib_string.py`):

- `Template.flags` is an int, `2`, where CPython's is `re.IGNORECASE` (`lib/re`'s flags are ints).
- The column of an invalid placeholder counts the str's bytes past ASCII, as `lib/re`'s positions
  do, and `capwords()` capitalizes ASCII letters alone, as `str.capitalize()` does.

A subclass of `Template` (another `delimiter`, `idpattern`, `braceidpattern`, `flags` or
`pattern`) is an error: only an exception class may have a base (#7). So are keyword arguments
whose values have different types (`substitute(name="Ann", count=3)`), as a dict of them would be:
Pystachy reads a `**kwargs` record by a name computed as the code runs only where its values share a
type.

`tests/lib_string.py` compares it with CPython's on the cases of CPython's
`Lib/test/test_string.py` that need no subclass of `Template`, and on the class attributes, the
pattern and keyword arguments with a mapping. Run by CPython, the edited module passes that file's
39 tests, also the 25 of `Template`, those that subclass it among them, as `__init_subclass__()`
is CPython's, and those of `Formatter`, as CPython imports `_string`.

In an AOT executable, `substitute()` of a 430-character template with 14 placeholders takes 5.8 µs
with a dict (CPython: 4.6 µs) and 6.1 µs with a dict and two keyword arguments (CPython: 7.3 µs,
which makes a `ChainMap` at each call); `safe_substitute()` 5.7 µs (4.8), `get_identifiers()`
5.3 µs (4.2) and `is_valid()` 5.2 µs (3.8): most of each is `lib/re`'s scan of the template, which
CPython's `_sre` does faster. `substitute()` of `"$who likes $what"` takes 0.78 µs (0.81), and
`capwords()` of 18 words 0.48 µs (1.35). (Medians of 3 runs, each the median of 5 rounds of 2,000
calls, 20,000 for the short ones.) [`examples/mailmerge`](../examples/mailmerge/README.md)
renders a message for each record of a data file with it.

These modules behave as their pure-Python code, which CPython replaces with C accelerators that
differ at the edges: errors can be worded differently (`heappop([])` raises `IndexError: pop
from empty list` here, `index out of range` from CPython's `_heapq`), keyword arguments the C
functions reject are accepted, `bisect`'s `hi=-1` is a plain bound (`len(a)` for `_bisect`),
`stat`'s tests read the module's constants (`_stat` has its own), and `heapify` of more than
2,500 items calls `__lt__` in another order (`_heapq` switches to a cache-friendly loop).

These files are part of Python and are used under the PSF License Version 2; see
`THIRD_PARTY_NOTICES`. `tools/import_sweep.py` tries every module of a CPython standard library
this way; [`docs/stdlib.md`](../docs/stdlib.md) reports which import and why the others do not.
