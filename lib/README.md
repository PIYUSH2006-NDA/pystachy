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

## `csv`, Pystachy's own

`csv.py` is no copy: CPython's `csv` is `Lib/csv.py` over the C module `_csv` (`Modules/_csv.c`),
and Pystachy has no C modules. It is Pystachy's own module, written after CPython 3.13.16's
`_csv.c` and `Lib/csv.py`: a reader runs `_csv.c`'s state machine (`parse_process_char`, from
`START_RECORD` to `AFTER_ESCAPED_CRNL`) over the characters of each line, a writer escapes, doubles
and quotes as `join_append_data` does, and a dialect is checked as `dialect_new` checks it, in its
order, so that what `csv` reads, writes and rejects is CPython's, with CPython's `csv.Error`
messages, and its `TypeError` and `ValueError` messages for a bad setting. The characters the state
machine adds to a field one by one are taken as slices of the line, each run of them found with
`str.find()`.

It has `reader()` and `writer()`, with a dialect and the format parameters `delimiter`,
`quotechar`, `escapechar`, `doublequote`, `skipinitialspace`, `lineterminator`, `quoting` and
`strict`; a reader's `line_num` and `dialect`, and a writer's `writerow()`, `writerows()` and
`dialect`; the six `QUOTE_*` constants, `Error`, `Dialect`, the dialects `excel`, `excel_tab` and
`unix_dialect` (registered as `"excel"`, `"excel-tab"` and `"unix"`), `register_dialect()`,
`get_dialect()`, `unregister_dialect()`, `list_dialects()` and `field_size_limit()`; and
`DictReader` and `DictWriter`. It has no `Sniffer`. A reader reads any iterable of strs (a file,
`sys.stdin`, a list of lines, an object whose `__iter__` steps through a list), and a writer writes
to any object with a `write()` method (a file, `sys.stdout`, an object of the program's class), and
returns what `write()` returns. `writerow()` is a template: a row is a list or a tuple (or a str or
a dict, as in CPython) of strs, ints, floats, bools, `None`s or objects of the program's classes,
each field `str()`-ed as CPython does; a tuple's items may have different types
(`writerow((name, 3, 1.5))`), a list's cannot. Where it differs from CPython
(`tests/deviations/lib_csv.py`):

- A reader parses all of its input when its iteration starts, where CPython's reader is an iterator
  that parses a row at each step: an error in the data is raised before the loop sees a row,
  `line_num` is the last line's throughout the loop, the rows are all held in a list (the memory a
  file takes grows with it), and the reader has no rows left for a second iteration, also where the
  first one stopped early. `next(reader)` does not compile, as the subset has no `next()`: take the
  rows with `list()`, or the header with a `DictReader`.
- A row is a `list[str]`: a reader whose quoting is `QUOTE_NONNUMERIC` or `QUOTE_STRINGS`, which
  make floats of the unquoted fields, raises `NotImplementedError` when it is made, and one of
  `QUOTE_NOTNULL`, which makes `None` of an empty unquoted field, raises it where the row holding
  one ends. A writer quotes with each of the six quoting styles as CPython's does.
- A `DictReader`'s row is a `dict[str, str]`: a row longer than `fieldnames` (whose other fields
  CPython puts in a list under `restkey`), and a shorter one where `restval` is `None`, raise
  `NotImplementedError`; `fieldnames` is a `list[str]` or `None`, `restkey` and `restval` a str or
  `None`. A `DictReader` reads its rows, and the header, when it is made, where CPython's reads the
  header when its `fieldnames` property is first read: `line_num` is then the header's, `fieldnames`
  assigned afterwards names the fields of the rows after the header, and an error in the data is
  raised by the constructor. A `DictWriter`'s `restval` is a str or `None`, and its `ValueError` for
  the keys of a row that are not in `fieldnames` lists them in the dict's order (CPython's, in a
  set's, which varies from run to run for strs).
- `excel`, `excel_tab` and `unix_dialect` are `Dialect` objects, where CPython's are classes: a
  class is no value in the subset, and there is no inheritance to derive a dialect from
  `csv.Dialect` with, so a dialect of the program's is a registered name
  (`register_dialect("pipes", delimiter="|")`) or keyword arguments. `Dialect` is the type CPython
  calls `_csv.Dialect` (what `get_dialect()` returns, and a reader's or writer's `dialect`), whose
  fields can be assigned (CPython's are read-only), and `dialect=` is a registered name, a
  `Dialect` or `None`.
- An uncaught error is reported as `csv.Error` (CPython's class is `_csv.Error`). A writer of an
  object without `write()`, a format parameter that is an object of the program's class, a row that
  cannot be iterated (but an int, float, bool or `None`, which raise CPython's `csv.Error`) and a
  NamedTuple row are compile-time errors, where CPython raises `TypeError` or writes the
  NamedTuple's fields; for `QUOTE_NONNUMERIC`, an object of the program's class is no number, also
  where its class defines `__float__`, `__int__` or `__index__`.

A str holds UTF-8 in Pystachy: where the dialect's characters are ASCII, the state machine reads a
line byte by byte, which reads it character by character, as no byte of a character past ASCII is a
delimiter, quote, escape, space or line break; where one of them is past ASCII, it reads the line
character by character. A field's length, which `field_size_limit()` bounds, counts characters, as
CPython's does.

`tests/lib_csv.py` compares it with CPython's `csv`: the cases of CPython 3.13's
`Lib/test/test_csv.py` that do not use `next()` or classes as dialects (line ends, NUL, escapes,
quoting, `skipinitialspace`, quoted line breaks, the end of the data, `strict`, each error with its
message, the writer's quoting, escaping and empty fields, line terminators, dialects and the
registry, `field_size_limit()`, `DictReader` and `DictWriter`), round trips through files,
characters past ASCII in fields and as the dialect's characters, and 300 random rows written and
read back and 300 random sets of lines read, with random dialects. Beyond the tests, run by
CPython in place of its own `csv`, it read 200,000 random sets of lines and wrote 200,000 random
rows as CPython's does, with random dialects (raising `NotImplementedError` only where a row would
hold a float or `None`), and its `DictReader` made CPython's dicts, `fieldnames` and `line_num` for
50,000 random files (raising `NotImplementedError` exactly where a dict would hold a `None` or a
list); compiled, it printed what it prints under CPython for 120,000 random reads and writes.
`examples/csvstat` is an application of it.

For a file of 200,000 generated orders (16.1 MB, 10 fields a row; `examples/csvstat/rwbench.py`
on a 4-core x86-64 VM, the medians of 11 runs, CPython's and the executable's in turn), compiled AOT
it reads the file in 0.850 µs a row (CPython 3.13.16: 1.333 µs), parses the file's lines already in
memory in 0.713 µs (1.221 µs), and writes the rows to a file in 0.755 µs (1.207 µs).

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
