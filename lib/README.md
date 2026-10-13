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

## `textwrap`, a port of CPython's

`textwrap.py` is CPython 3.13.16's `Lib/textwrap.py` (SHA-256
`30f3d833950d53e168cc021961574b553f56aed84458712b2eb29c6495843d46`) edited in 7 places, each
marked `# Pystachy port:`. It has the whole module, as CPython's code: `wrap()`, `fill()`,
`shorten()`, `dedent()`, `indent()` and `TextWrapper`, with each of its options (also changed on
a wrapper after it is made) and its class attributes (which a wrapper can override with its own).
Its regular expressions are `lib/re`'s.

- `TextWrapper`'s class body makes the patterns `word_punct`, `letter`, `whitespace` and
  `nowhitespace`, builds `wordsep_re` and `wordsep_simple_re` of them, and then `del`s them: a
  class body can neither read its own attributes (#126) nor `del`. They are the module's
  `_word_punct`, `_letter`, `_whitespace_class` and `_nowhitespace`, which the class body reads.
- The four class attributes, each a call's result, are annotated (`dict[int, int]`,
  `re.Pattern`), and `unicode_whitespace_trans` is `dict.fromkeys()` of a list comprehension
  where CPython's is of `map(ord, ...)`, which Pystachy takes only where its items are taken at
  once.
- `wordsep_re`'s pattern is `%` of a mapping (`%(wp)s`), which Pystachy does not support:
  `str.replace()` of each name makes the same pattern.
- `max_lines=None` is annotated `int | None`: a field that a class template gives `None` needs
  its type.
- `_munge_whitespace()` replaces each character through `unicode_whitespace_trans` with
  `''.join([chr(trans.get(ord(c), ord(c))) for c in text])`: Pystachy has no `str.translate()`.
- `dedent()` enumerates `list(zip(margin, indent))`: `zip()` nested in `enumerate()` is not
  supported.

Where it differs from CPython (`tests/deviations/lib_textwrap.py`):

- A width counts a str's bytes, as `len()` does in Pystachy: past ASCII, fewer characters fit
  on a line, and a word longer than the width (`break_long_words`) is broken after that many
  bytes, which can fall inside a character, whose bytes two lines then hold apart.
- `unicode_whitespace_trans` is looked up byte by byte: a table that a wrapper is given maps the
  bytes of a character past ASCII, not the character (CPython's table maps only ASCII
  whitespace).
- A subclass of `TextWrapper` is an error: only an exception class may have a base (#7).

`tests/lib_textwrap.py` compares it with CPython's on the cases of CPython's
`Lib/test/test_textwrap.py`, and on a wrapper's own options and class attributes. Run by
CPython, the edited module passes that file's 66 tests.

In an AOT executable, `wrap()` of a 500-character paragraph of 79 words takes 137 µs, `fill()`
136 µs and `shorten()` 134 µs, against CPython's 64, 66 and 54 µs; `dedent()` of a 15-line
block takes 45 µs (CPython: 11 µs) and `indent()` 1.2 µs (CPython: 2.3 µs). Most of the time
is `lib/re`'s: `wordsep_re.split()` takes 122 µs of `wrap()`'s 137 (CPython's `_sre`: 38 of 64),
and the lookups that stand in for `str.translate()` 10 µs (CPython: 2.7 µs), while the rest of
`wrap()`, the wrapping itself, takes 6 µs, against CPython's 17 µs. `dedent()`'s three regular
expressions take 20, 14 and 13 µs (CPython: 3 µs each). (Medians of 3 runs, each the median of
5 rounds over 200 generated ASCII paragraphs or blocks.)

These modules behave as their pure-Python code, which CPython replaces with C accelerators that
differ at the edges: errors can be worded differently (`heappop([])` raises `IndexError: pop
from empty list` here, `index out of range` from CPython's `_heapq`), keyword arguments the C
functions reject are accepted, `bisect`'s `hi=-1` is a plain bound (`len(a)` for `_bisect`),
`stat`'s tests read the module's constants (`_stat` has its own), and `heapify` of more than
2,500 items calls `__lt__` in another order (`_heapq` switches to a cache-friendly loop).

These files are part of Python and are used under the PSF License Version 2; see
`THIRD_PARTY_NOTICES`. `tools/import_sweep.py` tries every module of a CPython standard library
this way; [`docs/stdlib.md`](../docs/stdlib.md) reports which import and why the others do not.
