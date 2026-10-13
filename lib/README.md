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

`curses/__init__.py` is Pystachy's own stand-in: CPython's wraps the C extension `_curses`, and
so is `functools.py` (below).

## `getopt`, a port of CPython's

`getopt.py` is CPython 3.13.16's `Lib/getopt.py` (SHA-256
`0ce875700c8798193b8e2748f7a27fc542cc4d525a1e6fc403767450ec92be99`) edited in 15 places, each
marked `# Pystachy port:` but for the six messages, which the comment that replaces the `gettext`
import describes. It has the whole module, as CPython's code: `getopt()` and `gnu_getopt()` (also
with a leading `+` in the short options, or `POSIXLY_CORRECT` set), with unique prefixes of long
options, `GetoptError` (with `msg`, `opt` and the old name `error`) and its messages.

- CPython's messages go through `gettext`'s `_()`, but `gettext` reads `sys.base_prefix`, which
  Pystachy does not have, and `%` formatting takes only a literal format string. So each message
  is `%` formatted as it is, untranslated (CPython ships no translation of them either).
- `GetoptError.__init__`'s parameters and `__str__`'s return are annotated `str`: an exception
  class is no class template, and a method without a return annotation returns `None`.
- `longopts` is annotated `list[str]` in `getopt()` and `gnu_getopt()`, since its default `[]`
  has no type otherwise. CPython also takes one str (`'alpha='`); here that is a compile-time
  error (`tests/errors/lib_getopt_longopts_str.py`).
- `opts` is annotated `list[tuple[str, str]]`: `do_longs()` and `do_shorts()`, which fill it, are
  templates, and an empty list is not typed through them.
- `do_longs()` declares `optarg: str | None` first: it is `None` or a str, set in the two arms of
  a `try`.
- `gnu_getopt()` reads `POSIXLY_CORRECT` with `os.getenv()` where CPython calls
  `os.environ.get()`: Pystachy has no `os.environ`.

`tests/lib_getopt.py` compares it with CPython's on the cases of CPython's
`Lib/test/test_getopt.py`. Run by CPython, the edited module passes that file's 8 tests and its
doctest (not the test of the translation catalogs, which needs CPython's `Tools/`).
[`examples/cut`](../examples/cut/README.md), a `cut` with GNU's options, is an application of it.

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
- An inline flag that is no flag, `(?iⅠ)` or `(?-Ⅰ:x)`, is an "unknown flag" where the character
  may begin an identifier, else "missing -, : or )" or "missing flag": CPython asks
  `str.isalpha()`, which differs for 262 characters such as U+2160 ROMAN NUMERAL ONE (`Ⅰ`).
- The flags are ints, not `RegexFlag` members; `groupindex` is a dict; `re.error` is the base class
  of the `PatternError` the module raises (CPython 3.13 has one class); a replacement function
  must return a str (CPython's may return `None`); and there is no `DEBUG` output, `Scanner`,
  `__index__` group number, warning or `bytes` pattern.

`tests/lib_re.py` compares it with CPython's `re`, and `tests/upstream_re_*.py` with CPython
3.13.16's own tests of it, JIT and AOT, against what CPython's `re` printed: the 403 cases of
`Lib/test/re_tests.py` (each also searched with IGNORECASE, with UNICODE and within its match,
as `test_re_tests` does) and its benchmarks, and some 1,200 cases of `Lib/test/test_re.py`, the
ones that apply to str patterns: matches and the groups backtracking restores, atomic groups and
possessive repeats, lookaround, backreferences and conditionals, flags and case folding, escapes
and Unicode classes, `sub()` and its templates, `split()`, `findall()` and `finditer()` past
empty matches, and the errors, with their messages and positions. Their headers list what they
leave out and why: the deviations above, bytes patterns, warnings, CPython's internals
(`re._compiler`, `DEBUG`) and its C types' own behaviour (immutable objects, `copy`, pickling,
the `TypeError` of a non-str argument), str subclasses, and the cases too big for `make
verify`'s run with a collection at every allocation, which run there on smaller inputs.
`tools/re_fuzz.py` (`make re-fuzz`, a step of `make verify`) runs the port on CPython against
CPython's `re`, deterministically: 2,000 random patterns must compile to the same code (or raise
the same error), and match, split and substitute 19 strings each as CPython's `re` does, every
other pattern on strs that hold UTF-8 as Pystachy's do; and the test cases too big for the
compiled tests run there at upstream's size (`make re-fuzz RE_FUZZ="20000 2"` runs 20,000
patterns of seed 2). With it, unmodified roman 5.2 prints what CPython prints. It is about 3
times slower than `_sre`.

## `functools`, Pystachy's own

CPython's `Lib/functools.py` does not compile (it imports `abc`, `collections`, `reprlib` and
`_thread`, and its pure-Python `lru_cache` keeps its links in lists of mixed types and sets
attributes on a function), and its `lru_cache()` is C: `_functools._lru_cache_wrapper`
(`Modules/_functoolsmodule.c`). `functools.py` here has `cache()` and `lru_cache()` in the subset,
written after that C code, with `lru_cache`'s docstring:

- `lru_cache(maxsize)` (128 by default, `@lru_cache` bare too; a negative `maxsize` is 0) keeps the
  results of the `maxsize` most recently used calls, `lru_cache(maxsize=None)` and `cache()` every
  result, and `maxsize=0` none. The wrapper has `cache_info()`, a `CacheInfo` named tuple of
  `hits`, `misses`, `maxsize` and `currsize`, `cache_clear()`, which empties the cache and zeroes
  the statistics, `__wrapped__` and the function's `__name__` and `__qualname__`.
- It counts and updates as C does, so what a program sees of it is CPython's: a hit makes the
  call the most recently used, a miss counts before the function runs (a call that raises is
  counted, and its exception is not cached), a call that added its own key while it ran (a
  recursive call with the same arguments) returns what it computed and leaves the cache as it is,
  and a full cache gives the least recently used entry to the new result. A result is the object
  the function returned, also a falsy one or `None`.
- A dict of Pystachy holds keys of one type and values of another, so each decorated function
  has a cache of its own types: `_lru_cache_wrapper` is a generic class, `Generic[*_Ts, _R]`,
  whose `__init__` takes the function as a `Callable[[*_Ts], _R]`, so each wrapper binds `_Ts` to
  the function's parameter types and `_R` to its return type ([`docs/language.md`](../docs/language.md),
  *Typing rules*). The key of a call is the tuple of its arguments, a `tuple[*_Ts]`, which
  `__call__(self, *args: *_Ts)` takes by position (CPython's key for one `int` or `str` argument
  is the argument itself).

What it does not have, each a compile-time error (`tests/errors/lib_functools_*.py`):

- a function whose parameters or return are not annotated, that returns `None` (`-> None`: its
  results would be a `list[None]`), that takes `*args` or `**kwargs`, or whose parameter is of a
  type Pystachy's dicts cannot key (a `float`, an object; CPython hashes those): the parameters are
  `int`, `bool`, `str`, `str | None` and tuples of those;
- `lru_cache()` of a builtin, a method or a lambda (it caches a def's results, of the program or
  of a function), and of a method in a class body, where Pystachy applies no decorator;
- a call through the cache that passes a keyword argument or leaves out one that has a default
  value: `__call__(self, *args: *_Ts)` takes each of the function's positional parameters, by
  position (CPython caches each form of a call apart, `f(1)`, `f(1, 2)` and `f(1, b=2)` being three
  entries);
- `cache_parameters()`, whose dict mixes `int | None` and `bool` values.

`typed=True` is accepted and keeps no calls apart: a parameter has one type, so the calls it
would keep apart (`f(1)` and `f(1.0)`) cannot both compile. The cache needs no lock, as a
Pystachy program has one thread. `tests/lib_functools.py` and `tests/lib_functools_mod.py`
compare it with CPython's C wrapper.

In an AOT executable, a cache hit costs 24 ns (unbounded) to 31 ns (bounded) for an `int`
argument, 26 ns for a `str` one and 36 ns for a `(str, int)` pair, whose key tuple is made and
hashed for each call; CPython's C wrapper takes 60 to 61, 61 and 84 ns, a loop's step included
(medians of 3 runs over 1,000 warm keys). A miss that evicts takes 68 ns, against 104 ns.

These modules behave as their pure-Python code, which CPython replaces with C accelerators that
differ at the edges: errors can be worded differently (`heappop([])` raises `IndexError: pop
from empty list` here, `index out of range` from CPython's `_heapq`), keyword arguments the C
functions reject are accepted, `bisect`'s `hi=-1` is a plain bound (`len(a)` for `_bisect`),
`stat`'s tests read the module's constants (`_stat` has its own), and `heapify` of more than
2,500 items calls `__lt__` in another order (`_heapq` switches to a cache-friendly loop).

These files are part of Python and are used under the PSF License Version 2; see
`THIRD_PARTY_NOTICES`. `tools/import_sweep.py` tries every module of a CPython standard library
this way; [`docs/stdlib.md`](../docs/stdlib.md) reports which import and why the others do not.
