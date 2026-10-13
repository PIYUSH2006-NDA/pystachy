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
| `urllib` | `Lib/urllib/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | the package, which is empty; its `parse` is a port (below) |

`curses/__init__.py` is Pystachy's own stand-in: CPython's wraps the C extension `_curses`, and
so is `functools.py` (below).

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

## `fnmatch`, a port of CPython's

`fnmatch.py` is CPython 3.13.16's `Lib/fnmatch.py` (SHA-256
`95391dac2ce9f60084d65eba2f4b9d9735e28136d55b684e1fde7d6342555963`) with 8 regions edited,
each marked `# Pystachy port:`. Its functions are CPython's: `fnmatch()`, `fnmatchcase()`,
`filter()` and `translate()` translate a shell pattern into CPython's regular expression, character
for character, and match it with `lib/re`; `_compile_pattern()` keeps the compiled patterns in an
`lru_cache(maxsize=32768, typed=True)`, so its `cache_info()` counts what CPython's does.

- `_compile_pattern(pat: str) -> Callable[[str], re.Match | None]`, with `from typing import
  Callable`: `lib/functools` types a cache from its function's annotations. A pattern is a `str`
  (CPython's also takes `bytes`, which Pystachy has not), and the matcher is the bound method
  `re.compile(...).match` as a `Callable`.
- `translate()`'s sentinel `STAR = object()` is `None` (#251): `_translate()` and
  `_join_translated_parts()` annotate their lists `list[str | None]` and test `is STAR` as before.
- `_join_translated_parts()` binds `fixed` and `res` to a list and then to the str it joins
  (#248): the lists are `pieces` and `res`, the strs `fixed` and `joined`.
- `filter()` tests `os.name == 'posix'` where CPython tests `os.path is posixpath`: a module is no
  value in Pystachy. `os.path.normcase()` is Pystachy's builtin, posixpath's: a str as it is.

`tests/lib_fnmatch.py` compares `translate()` of 45 patterns (classes, negated, reversed and
dashed ranges, `[]]`, an unclosed `[`, `&&`, `~` and `|` in a class, regex metacharacters,
non-ASCII) and the names each matches with CPython's, and the cache's statistics. A pattern
matches by code point, as `lib/re` does, so a non-ASCII name matches as in CPython.

In an AOT executable, `fnmatchcase()` of 2,000 names against 10 patterns takes 428 ns a match
with the cache and 1,236 ns compiling the pattern each time (CPython: 286 and 3,269 ns): `lib/re`
compiles a pattern about 3.6 times faster than CPython's `re`, whose parser and compiler are
Python, and matches about 1.6 times slower than its C engine `_sre`, so the cache saves Pystachy
less than it saves CPython, but still nearly two thirds of the time.

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
- `unicode_whitespace_trans` maps code points to code points, an int each, the type of its default:
  a table with a str or `None` value, which `str.translate()` takes to replace a character with
  several or to delete it, is a compile-time type error (`tests/errors/lib_textwrap_trans_str.py`).
  It is looked up byte by byte: a table that a wrapper is given maps the bytes of a character past
  ASCII, not the character (CPython's table maps only ASCII whitespace).
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

## `urllib.parse`, a port of CPython's

`urllib/parse.py` is CPython 3.13.16's `Lib/urllib/parse.py` (SHA-256
`491b233e8d87a2ab73964afff029717177d53ad8def328ed9b00575db983da27`) with 27 edits, each marked
`# Pystachy port:`, and `urllib/__init__.py` is CPython's, which is empty. Of CPython's 1,264 lines,
1,156 are as they are; the edits change or remove 108 and add 576. The budget: 257 of the lines
added are the codecs that stand in for `str.encode()` and `bytes.decode()` (Pystachy has no bytes),
87 test bracketed hosts and NFKC forms where CPython calls `ipaddress` and `unicodedata`, 23 quote a
str of bytes, and the other 209 are the result classes, the blocks that only CPython runs, and the
lines and comments of the smaller edits.

What works, on strs, as CPython's code does it:

- `quote()`, `quote_plus()`, `unquote()` and `unquote_plus()`, with `safe`, `encoding` and `errors`.
  A str holds UTF-8 in Pystachy, so `quote()` quotes its bytes as CPython quotes the bytes of
  `str.encode()`, and `unquote()` decodes the bytes of the percent-escapes of each ASCII run as UTF-8
  (with `errors='replace'` by default), each sequence that is no UTF-8 replaced as CPython's decoder
  replaces it (`unquote('%F0%9F%98')` is one U+FFFD, `unquote('%ED%A0%80')` three). The codecs are
  UTF-8, Latin-1 and ASCII, under any of the names `codecs.lookup()` finds them by (`'utf8'`,
  `'ISO-8859-1'`, `'us-ascii'`, `'l1'`, ...), with the error handlers `strict`, `ignore`, `replace`,
  `backslashreplace`, `xmlcharrefreplace`, `surrogateescape` and `surrogatepass` (a surrogate is held
  as Pystachy holds one, its three bytes), CPython's `LookupError` for a handler it does not know and
  `TypeError` for `xmlcharrefreplace` and `namereplace` in `unquote()`, and its messages.
- `parse_qs()` and `parse_qsl()`, with `keep_blank_values`, `strict_parsing`, `encoding`, `errors`,
  `max_num_fields` and `separator` (also of several characters), and their `ValueError`s.
- `urlencode()` of a dict, or of a list or tuple of pairs, with `doseq` (a value that is a list,
  tuple or set is a sequence, an int or `None` is not), `safe`, `encoding`, `errors` and `quote_via`
  (`quote`, `quote_plus` or a function of the program); keys and values that are no strs are
  `str()`-ed, as in CPython.
- `urlsplit()`, `urlparse()`, `urlunsplit()`, `urlunparse()`, `urljoin()`, `urldefrag()` and
  `unwrap()`, with the `ValueError`s of an invalid IPv6 URL or bracketed host and of a netloc whose
  NFKC form holds `/?#@:`, and `uses_relative` and the other lists. `SplitResult`, `ParseResult` and
  `DefragResult` are NamedTuples: their fields, indexing, unpacking, `==` with tuples, `repr()`,
  `_replace()` and `geturl()`.
- A `str | None` for the string of `quote()`, `quote_plus()`, `unquote()` and `unquote_plus()`,
  which raise CPython's `TypeError` or `AttributeError` for `None`.

The edits:

- The imports: `typing.NamedTuple` for `collections.namedtuple`, and `types`, `warnings` and
  `ipaddress` optional (`try:` ... `except ImportError: pass`), as Pystachy has none of them.
- What only CPython runs is in blocks that begin `try: import types`: Pystachy decides an optional
  import as it compiles, and where an import fails it drops the rest of the `try` block
  ([`docs/language.md`](../docs/language.md#optional-imports)). They make the result classes for strs
  again as classes that derive from their NamedTuples and their mixins
  (`type('SplitResult', (SplitResult, _NetlocResultMixinStr), {'__slots__': ()})`), set
  `__class_getitem__`, the fields' docstrings and the result pairs (`_fix_result_transcoding()`),
  make `_ALWAYS_SAFE` and `_ALWAYS_SAFE_BYTES`, which are bytes, and wrap `urlsplit()` and
  `_byte_quoter_factory()` in `functools.lru_cache`, which CPython's decorators did. So CPython,
  running the edited module, has CPython's result classes, bytes paths and caches.
- `DefragResult`, `SplitResult` and `ParseResult` are `typing.NamedTuple` classes, the bases that
  `namedtuple()` made, with the docstrings they were given and `geturl() -> str`: only an exception
  class has a base in Pystachy, so a class has no mixin, and the mixins' properties (`username`,
  `password`, `hostname`, `port`) and `encode()` are CPython's only; `_DefragResultBase` and the
  others name them, for the bytes classes, which stay CPython's.
- `_coerce_args()` names its first argument, as Pystachy decides `isinstance()` of a name as it
  compiles, and puts the return of bytes in an `else` block, which it then leaves out for strs; its
  loop takes all the arguments, as Pystachy slices no tuple. `urlunsplit()` and `urlunparse()`
  unpack their components before they pass them, as Pystachy unpacks only a tuple's items into
  arguments, not a NamedTuple's.
- `urljoin()` makes a new list of the segments, as Pystachy assigns to no slice and has `filter()`
  only as the argument of a consumer.
- `_checknetloc()` replaces each of the 19 characters whose NFKC form holds one of `/?#@:` with that
  form (`_NFKC_DELIMITERS`, from CPython 3.13's Unicode 15.1), for `unicodedata.normalize()`: no
  composition takes one of these five characters in, so that is all NFKC changes of what the test
  reads. `_check_bracketed_host()` calls `_ip_version()`, whose `_is_ipv4()` and `_is_ipv6()` test a
  str as `ipaddress.ip_address()`'s constructors parse it, scope IDs and IPv4 suffixes included, and
  raise its `ValueError`.
- `quote()` returns `_quote_str(_encode(string, encoding, errors), safe)` for `string.encode()` and
  `quote_from_bytes()`; `_encode()` makes the str of the bytes, which holds byte b as `chr(b)` (a
  str's byte in Pystachy, a code point below 256 in CPython), and takes an `encoding` and `errors`
  of `None` as `'utf-8'` and `'strict'`; `_quote_str()` quotes it as `quote_from_bytes()` quotes
  bytes, with the quoted forms of the 256 bytes made once for each `safe`.
- `unquote()`'s `_generate_unquoted_parts()` returns a list of the parts (Pystachy has no
  generators), unquotes an ASCII string at once (`lib/re`'s `finditer()` is slower than `_sre`'s), and
  calls `_unquote_str()` and `_decode()` for `_unquote_impl()` and `bytes.decode()`.
- The codecs (`_codec()`, `_encode()`, `_encode_error()`, `_decode()`, `_utf8_char()`,
  `_decode_error()`) are those of CPython's `unicodeobject.c` and `stringlib/codecs.h` and the
  handlers of `codecs.c`: the same runs of characters an encoder cannot encode, the same ranges of
  bytes the UTF-8 decoder gives its handler (an invalid start byte, an invalid continuation byte,
  the unexpected end of the data), the same replacements and positions. `_UTF8` (a str's length of
  `'\xe9'`) tells Pystachy's strs from CPython's code points, so the module runs under CPython too.
- `urlencode()` names the pairs `pairs` (a dict stays a dict) and the quoted key, value and element
  `qk`, `qv` and `qelt` (a key or value that is no str keeps its type), and an `elif` takes a value
  without `__len__` as no sequence, as `len()` of it, and looping over it, would be compile-time
  errors where CPython's `len()` raises `TypeError`.
- `parse_qsl()` and `_generate_unquoted_parts()` annotate their returns, which their first return,
  of `[]`, would type, and `_typeprog`, `_hostprog` and `_portprog` are annotated, as only a
  function gives them a value other than `None`.

Where it differs from CPython (`tests/deviations/lib_urllib_parse.py`):

- Where CPython's codecs raise `UnicodeEncodeError` or `UnicodeDecodeError` (`errors='strict'`, the
  default of `quote()`), the port raises `UnicodeError` with their message, as Pystachy raises
  neither: an `except` clause that names them does not catch it.
- An encoding other than UTF-8, Latin-1 and ASCII raises `NotImplementedError`, where CPython
  encodes and decodes (or raises `LookupError` for a name it has no codec for), and so does the
  error handler `namereplace` in `quote()`, which needs the names of the characters.
- A str that holds bytes that are no UTF-8, which no CPython str is (`chr(233)` is the byte 0xE9 in
  Pystachy, docs/language.md), is quoted byte for byte; for Latin-1 and ASCII, a byte that begins no
  character is the character of its value, as `lib/re` reads it.
- `urlsplit()` caches nothing, which only its speed shows (and `cache_info()`, an error below); a
  `doseq` value that is a set of strs gives its items in the order of a Pystachy set, which differs
  from CPython's ([`docs/language.md`](../docs/language.md#deviations-from-cpython)).

Each of these is a compile-time error (`tests/errors/lib_urllib_parse_*.py`):

- `username`, `password`, `hostname` and `port` of a `SplitResult` or `ParseResult`, which are
  properties of CPython's mixins (`@property` is not supported; `_hostname.py`), and `encode()` of a
  result (`_encode.py`).
- Bytes: `quote_from_bytes()`, `unquote_to_bytes()` (`_unquote_to_bytes.py`), a bytes argument and
  the bytes result classes.
- `urlsplit.cache_info()`, `cache_clear()` and `clear_cache()` (`_cache.py`).
- `urlencode()` of something other than a mapping or a sequence (`_not_sequence.py`; CPython raises
  `TypeError`), and with `doseq`, a value that is a sequence of items of different types
  (`_doseq_mixed.py`).
- An `allow_fragments` that is an int, not a bool (`_allow_fragments_int.py`): `urlsplit()` rebinds
  it to `bool(allow_fragments)`, and a variable has one type.
- The deprecated `splittype()` and the other split functions, `to_bytes()` and `Quoter`, which warn
  with `warnings` (`_deprecated.py`).

`tests/lib_urllib_parse.py` compares it with CPython's `urllib.parse`: the str cases of CPython's
`Lib/test/test_urlparse.py` and of `test_urllib.py`'s `QuotingTests`, `UnquotingTests` and
`urlencode_Tests`, every codec name and error handler on characters past U+00FF and on surrogates,
then `unquote()` of every one-byte escape and of two to four bytes drawn from each class of bytes
CPython's UTF-8 decoder tells apart, and `quote()` of code points at the ends of each length of
UTF-8, summed up by a digest of their `ascii()`. Run by CPython in place of its own, the edited
module passes all 77 tests of CPython 3.13.16's `test_urlparse.py` (5 subtests skip, as with
CPython's own: they are about non-ASCII bytes) and 28 of the 29 tests of `test_urllib.py`'s
`QuotingTests`, `UnquotingTests` and `urlencode_Tests`: `test_quote_with_unicode` stops at its
`assertRaises(UnicodeEncodeError, ...)`, the deviation above, and passes with `UnicodeError` in its
place; the whole of `test_urllib.py`, 109 tests, gives what it gives with CPython's own module but
for that one. Beyond the
tests, compiled, it gave what CPython gives for `unquote()` of all 65,536 two-byte escapes in 7
codec and handler combinations, of three bytes from 25 values and four from 13, for `quote()` of
all 1,114,112 code points in 4 combinations and back, and for 200,000 random strings of URL
pieces through each function, about 30 calls each.

In an AOT executable (medians of 3 runs, each the median of 5 rounds of 20,000 calls after one that
warms up), `quote()` of `'café crème/menu'` takes 252 ns (CPython 3.13.16: 865 ns), `quote_plus()`
of four ASCII words 134 ns (488), `unquote()` of `'caf%C3%A9%20cr%C3%A8me%2Fmenu'` 418 ns (2,209),
`parse_qsl()` of a query of 7 fields 1.04 µs (8.99) and `parse_qs()` 1.16 µs (9.68), `urlencode()`
of 4 pairs 652 ns (4,583), `urlsplit()` of 1,000 URLs in turn 338 ns (2,061) and `urljoin()` 812 ns
(3,743); `urlsplit()` of one URL again and again takes 338 ns, where CPython's cache gives its result
in 91 ns. [`examples/urlstats`](../examples/urlstats/README.md) reads an access log with it, 5.4 to
5.9 times as fast as CPython.

These modules behave as their pure-Python code, which CPython replaces with C accelerators that
differ at the edges: errors can be worded differently (`heappop([])` raises `IndexError: pop
from empty list` here, `index out of range` from CPython's `_heapq`), keyword arguments the C
functions reject are accepted, `bisect`'s `hi=-1` is a plain bound (`len(a)` for `_bisect`),
`stat`'s tests read the module's constants (`_stat` has its own), and `heapify` of more than
2,500 items calls `__lt__` in another order (`_heapq` switches to a cache-friendly loop).

These files are part of Python and are used under the PSF License Version 2; see
`THIRD_PARTY_NOTICES`. `tools/import_sweep.py` tries every module of a CPython standard library
this way, with the modules here in place of the library's own; [`docs/stdlib.md`](../docs/stdlib.md)
reports which import and why the others do not.
