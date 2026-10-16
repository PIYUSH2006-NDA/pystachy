# Library compatibility

This reference describes compiled behavior. The adapted sources may expose more
APIs when CPython runs them, because optional imports select CPython's C modules
and dynamic features. Differential cases live in `tests/lib_*.py`; deliberate
differences live in `tests/deviations/`, and rejected inputs in `tests/errors/`.

Pystachy uses 64-bit integers, homogeneous containers and UTF-8 byte strings.
Unless a module explicitly decodes characters, lengths and positions count bytes.
See [language compatibility](../docs/language/compatibility.md).

## Operator

Arithmetic, comparison, logical, sequence and bitwise operator functions compile
for supported operand types. `call()` forwards a supported callable's arguments.
In-place functions require a result that keeps its input type: `itruediv(1.0, 2.0)`
works; rebinding an integer to a float does not.

`itemgetter`, `attrgetter` and `methodcaller` are callable objects: call them
directly, store them, or pass them as `key=` to `sorted`, `min`, `max`, `list.sort`
and the library's key parameters. A getter specializes on its literal arguments,
so `itemgetter(1)` reads a fixed tuple's or NamedTuple's item with its static type
and `attrgetter("name")` reads `o.name`; each literal value makes a getter type of
its own, so `itemgetter(0)` and `itemgetter(1)` cannot share a list or variable.
`itemgetter(i)` of a variable `i` indexes lists, strings and dicts, and a fixed
tuple at run time with the union of its items' types. Dotted names, several
items or names (a tuple result) and `methodcaller` arguments work as in CPython,
and reprs match C's. A literal getter's constants cannot be assigned.

Attribute and method names must be string literals: a missing attribute and a
name that is not a string fail compilation, rather than raising `AttributeError`
or `TypeError` when the getter runs (a single non-string literal still raises
CPython's `TypeError` when the getter is made). Pickling is unsupported.
`length_hint` and `index` are not general substitutes for CPython's versions:
for example, `length_hint([1, 2])` and `index(2)` fail compilation.

## Path modules

`posixpath` supports string constants, `normcase`, `isabs`, `join`, `split`,
`splitext`, `splitdrive`, `splitroot`, `basename`, `dirname` and `normpath`.
`genericpath` supplies their helpers. `abspath`, `relpath`, `commonpath`,
`commonprefix`, `expanduser`, `expandvars`, `realpath` and filesystem tests are
outside this supported API set. Builtin `os.path` has its own documented APIs.

`stat` supports constants, `S_IS*`, `S_IMODE` and `S_IFMT`, but not `filemode`.
`curses.ascii` supports ASCII characters; byte strings are not Unicode character
sequences.

## Pure-Python accelerators

`bisect`, `heapq`, `operator` and `stat` execute their Python implementations
when the C accelerators cannot import. Consequently, edge behavior can differ
from CPython's accelerated modules:

- `heappop([])` reports `pop from empty list`, rather than `index out of range`.
- Some keyword arguments rejected by C functions are accepted by Python functions.
- `bisect` treats `hi=-1` as a bound; `_bisect` treats it as `len(a)`.
- `stat` tests use the module's constants rather than `_stat`'s separate constants.
- For more than 2,500 items, `heapify` compares in a different order from `_heapq`'s
  cache-friendly loop, with the same result.
- `operator.__doc__` is the Python module's docstring, which CPython replaces with
  `_operator`'s.

## Module docstrings

A module's `__doc__` is its docstring, as in CPython, but for the modules written for
Pystachy: `collections`, `curses`, `functools` and `io` have docstrings of their own.

## Html and HTMLParser

`html.escape`, `html.unescape` and the HTML4/HTML5 entity mappings reuse the
adaptations merged in [#378](https://github.com/den-run-ai/pystachy/pull/378). Numeric references
are bounded before checked-int conversion and named references use the upstream HTML5 table.

`html.parser.HTMLParser` retains CPython 3.13.16's incremental parser and uses
ordinary single inheritance. Typed subclasses can override the start/end tag,
data, comment, declaration, processing-instruction and reference callbacks.
`feed`, `close`, `reset`, `getpos`, `get_starttag_text`, `convert_charrefs` and
`scripting` are exercised by the probe tests, including RAWTEXT and RCDATA.
Attribute records use `list[tuple[str, str | None]]`; missing values remain None.

Native column offsets count UTF-8 bytes, and tag/attribute name case conversion
uses ASCII-only `str.lower`. Unicode text and entity output remain supported,
but these behaviors differ from CPython for non-ASCII columns and uppercase
names. User subclass constructors and callback signatures need compatible
annotations. Multiple inheritance and dynamic attributes remain unavailable.

`_markupbase` is an internal implementation detail. Its abstract-construction
guard is omitted and its field layout is declared in `__init__`. Its legacy SGML
helpers remain in the source but are outside the compiled surface tested here.
See [the probe record](../docs/html-parser-probe.md) for provenance and commands.

## Difflib

`SequenceMatcher` accepts strings or lists of strings, including `isjunk` and
`autojunk`. It provides sequence setters, longest-match and matching-block
queries, opcodes, and the three ratio methods. `get_close_matches`, `Match`,
`IS_CHARACTER_JUNK` and `IS_LINE_JUNK` also work.

Items of other types are rejected. Generator APIs are unavailable:
`get_grouped_opcodes`, `unified_diff`, `context_diff`, `ndiff`, `restore`,
`Differ.compare`, and `HtmlDiff` tables. The linediff example groups opcodes itself.

## Getopt

`getopt` and `gnu_getopt` support short and long options, unique long-option
prefixes, GNU option interleaving, a leading `+`, and `POSIXLY_CORRECT` through
`os.getenv`. `GetoptError` exposes `msg`, `opt` and the legacy `error` alias.

`longopts` must be `list[str]`; CPython also accepts one string. Messages are
untranslated. Error messages and parsing otherwise follow the upstream code.

## Heapq

Heap operations, including `_max` variants, and `nlargest`/`nsmallest` work.
The top-k functions accept lists and supported iterables: tuples, strings,
dicts, sets, `dict.items()`, and objects with `__iter__`, with or without
`__len__`. `key=` accepts supported functions, builtins and bound methods.
Ties preserve input order.

Lists are read in place. Other inputs are first materialized by a comprehension;
therefore a key/comparison that changes a dict or set being read does not raise
CPython's iterator-mutation `RuntimeError`. A `__len__` that raises `TypeError`
is handled as in CPython. Apart from the large-heap comparison order above,
the algorithm preserves comparison and key-call order for list inputs.

`merge` is a generator and does not compile. Pass `file.readlines()` rather than
an open file directly. Materialize a generator expression with a supported
consumer before passing it to a top-k function.

## Html

`escape`, `unescape` and the HTML4/HTML5 entity mappings follow CPython 3.13.16.
Numeric references produce Unicode text, including Latin-1 characters, and named
references use the upstream HTML5 table. Oversized references are replaced according
to HTML rules without requiring arbitrary-precision integers. Decimal conversion
keeps the default 4,300-digit limit; changing that limit with `sys` is unavailable.
Caller indexing, slicing and lengths retain Pystachy's UTF-8 byte semantics.

## Keyword

`kwlist`, `softkwlist`, `iskeyword` and `issoftkeyword` use CPython 3.13.16's
keyword sets. Predicates accept positional strings or `None`; other input types
fail compilation. Membership uses frozen snapshots, so changing the public lists
does not change the predicates.

## Collections

The shipped module provides `deque`, `defaultdict`, `OrderedDict` and `Counter`.
Each is a generic class whose item types (`deque[T]`, `Counter[T]`,
`defaultdict[K, V]`, `OrderedDict[K, V]`) come from supported constructor
arguments, an annotation (`q: deque[int] = deque()`,
`d: defaultdict[str, list[int]] = defaultdict(list)`) or an explicit constructor
(`Counter[str]()`). Parameters, returns and fields can name them. The compiled
types are fixed; a deque's items may be an explicitly supported union such as
`int | str`, and mapping keys are the supported dict key types. The package binds `abc` to
the builtin `collections.abc`, as CPython's binds it to `_collections_abc`, and its
`__doc__` is its own docstring.

`deque` supports both ends, optional `maxlen`, extension, rotation,
insertion/removal, indexing, containment/search, copies, comparisons, repetition
and `reversed()`. Iteration reads live items and rejects endpoint mutations, while
`reversed()` iterates over a snapshot; `maxlen` is writable. Rich comparisons use
snapshots when item comparison callbacks mutate a queue. Searches (`count`, `index`,
containment and `remove`) read live items and detect structural mutations with
CPython's operation-specific errors; same-size replacements are preserved.

The mappings hold dicts rather than derive from `dict`, so `isinstance(x, dict)`
is false. They support indexing, assignment, `del`, `in`, `len`, iteration,
`reversed()`, `keys()`, `values()`, `items()`, `get`, `pop`, `popitem`,
`setdefault`, `clear`, `update`, `copy` and equality with each other and with a
dict on the right; any other operand, such as `None`, is unequal, as CPython's
identity fallback finds. An empty display operand (`d == {}`) has no type: test
`not d`. Views are lists, as a dict's are here, and iteration is a snapshot
rather than CPython's iterator that raises when the mapping changes size.
Constructors and `update` take a dict, a list, tuple or set of pairs, or another
of these mappings (a `Counter` types only the keys of an `OrderedDict` or
`defaultdict`: the `int` values need an annotation); other iterable objects of
pairs need `list(...)` first, and a generator expression a list comprehension.
Keyword arguments are accepted by `update` and `subtract`, not by constructors.
`dict(m)` of a mapping is not supported: `{k: v for k, v in m.items()}` copies it.

- `defaultdict(factory)` accepts builtin classes such as `int`, `list`, `set`,
  `str`, `float` and `dict`, functions, lambdas and `None`. A factory types
  nothing unless it is a function with a return annotation, so the key and value
  types come from an annotation or explicit types (`defaultdict[str, int](int)`)
  where no mapping argument gives them; a factory that makes another mapping
  (`defaultdict(lambda: defaultdict(int))`) takes the value type from them. Only
  indexing calls the factory, keeping a value the factory itself stored for the
  key. `__missing__`, a writable `default_factory`, `copy`, `|` and `|=` follow
  the C type: `|` takes a dict or another of these mappings, raising CPython's
  `TypeError` for `None` and builtin values that are not, and `|=` also pairs.
  The repr names a builtin class given to the constructor as CPython does, and
  other factories, and a class assigned to `default_factory` later, as
  `<function>`.
- `OrderedDict` supports `move_to_end(key, last=True)`, `popitem(last=True)`,
  `fromkeys(iterable, value)` with a value that types the items, `|` and `|=` (as
  defaultdict's), and order-sensitive equality between OrderedDicts. Two dicts
  hold its items, the first ones in reverse order, so that operations at either
  end take amortized constant time, as with CPython's linked list. Moving a key
  reinserts the key object given.
- `Counter` counts with ints. It supports missing counts of zero, `update` and
  `subtract` from iterables and mappings, `most_common(n)`, `elements()`,
  `total()`, `+ - | &`, unary `+` and `-`, their in-place forms, and the 3.10
  comparisons, which raise CPython's `TypeError` for a `None` operand.
  `elements()` returns a list rather than an iterator, and an empty `Counter()`
  operand on the left of an operator needs its type.

A deque compares with deques: `==` with `None` is false and `<` raises CPython's
`TypeError`. Its reflected multiplication and comparisons with other containers,
pickling, `namedtuple`, `ChainMap` and the `User*` classes are unavailable. A `deque` is
not a `collections.abc.Sequence` to `isinstance`.

## Shlex

`split`, `quote`, `join` and the lexer support POSIX/compatibility modes, comments,
quotes, escapes, whitespace splitting, punctuation, token pushback and source
stacking. Input text is read through `StringIO`; Unicode characters are read whole.

Files are read eagerly. Pushed files are closed on push rather than on source
pop; constructor files remain the caller's responsibility. Iteration and `next()` read
one token at a time from a shared position. `punctuation_chars` is writable;
its constructor accepts bools or strings, while lists fail compilation. Lexer
subclasses and arbitrary stream types are outside the compiled surface.

## Io

`StringIO` supports construction with `initial_value` and `newline`, reading and
writing, `readlines`/`writelines`, iteration, `getvalue`, positioning and
truncation, closing and stream capability queries. It exposes `closed`,
`encoding`, `errors`, `line_buffering` and seek constants. `print(..., file=buf)`
works. Newline translation, NUL padding after seeking past the end, and closed
stream errors follow CPython's implementation.

- Sizes and positions count bytes rather than Unicode characters.
- Iteration and `next()` read one line at a time from the shared stream position.
- `with StringIO()` is unsupported; `with` handles files only.
- `newlines`, `detach`, `fileno` and pickling are unavailable.
- Invalid argument types such as `StringIO(5)` are compile-time errors.

## Csv

The module provides `reader`, `writer`, `DictReader`, `DictWriter`, `Dialect`,
the six `QUOTE_*` constants, `Error`, dialect registration and lookup, and
`field_size_limit`. Default dialect objects are `excel`, `excel_tab` and
`unix_dialect`, registered as `excel`, `excel-tab` and `unix`. `Sniffer` is absent.
Readers accept supported iterables of strings, including files and stdin;
writers accept objects with `write`. Format parameters follow CPython:
`delimiter`, `quotechar`, `escapechar`, `doublequote`, `skipinitialspace`,
`lineterminator`, `quoting` and `strict`.

Writer fields may be strings, integers, floats, booleans, `None`, or objects
converted with `str`. A tuple row may mix types; a list row must be homogeneous.
`writerow` returns the result of the output object's `write`.

- A reader and `next(reader)` parse one record at a time, update `line_num` as input
  is consumed, and retain their position after an early loop exit.
- Reader rows are `list[str]`. `QUOTE_NONNUMERIC` and `QUOTE_STRINGS` raise
  `NotImplementedError` at construction; `QUOTE_NOTNULL` raises it when a row
  would contain `None`. Writers support all six quoting styles.
- `DictReader` rows are `dict[str, str]`. Extra fields and missing fields with
  `restval=None` raise `NotImplementedError`. It reads data and the header at
  construction, so errors are immediate and `line_num` initially names the
  header. Later `fieldnames` assignments rename rows after the header.
  `fieldnames` is `list[str] | None`; `restkey` and `restval` are `str | None`.
- A `DictWriter`'s `restval` is `str | None`. Its error for extra keys lists
  them in dict order, rather than CPython's set order.
- Dialects are objects, rather than classes. Use registered names or keyword
  settings instead of dialect subclasses. Dialect fields are writable: writers
  snapshot settings at construction; readers use settings when each record starts.
  `dialect=` accepts a registered name, `Dialect`, or `None`.
- Uncaught errors name `csv.Error`, rather than `_csv.Error`. A missing `write`,
  a format parameter of a user class, an unsupported iterable row type, or a
  NamedTuple row fails compilation. Integers, floats, bools and `None` passed
  as rows instead raise `csv.Error`. For `QUOTE_NONNUMERIC`, user objects are
  nonnumeric even if they define numeric conversion methods.

Dialect characters may be non-ASCII. Parsing decodes characters where required,
and `field_size_limit` counts characters, as CPython does.

## Re

String patterns support CPython 3.13 syntax: character classes, repeats (greedy,
lazy and possessive), groups and backreferences, lookarounds, conditionals,
atomic groups, scoped flags, escapes and Unicode character classes/case folding.
The module and `Pattern` expose matching, searching, splitting, substitution,
escaping and cache purging. `Match` supports group queries (up to five groups
per `group` call), runtime-length `groups(default=None)` tuples, indexing,
dictionaries, positions, spans and expansion.

- Matches decode code points, but positions (`pos`, `endpos`, group spans and
  pattern-error positions) are byte indices. A byte that `ord()` reads as no
  character's part (a truncated, overlong or above-U+10FFFF sequence) is its own
  character, as `chr()` made it.
- `findall` with two or more groups still raises `NotImplementedError`; its
  ported result contract remains `list[str]`. `Match.regs` remains unsupported
  because its runtime-length tuple contains tuple elements.
- `split` returns `list[str]` and raises `NotImplementedError` if an unmatched
  capturing group would add `None`.
- `finditer` eagerly returns a list of matches.
- `\N{...}` is a pattern error; character-name lookup is unavailable.
- Flags are ints, `groupindex` is a dict, and `re.error` is the base of
  `PatternError` rather than the same class. Replacement callbacks must return
  strings. Bytes patterns, warnings, `DEBUG` output, `Scanner` and `__index__`
  group numbers are unavailable.

`purge` clears pattern, replacement-template and last-input decoding caches.
Active operations retain their decoded input, so callbacks can safely purge;
existing patterns and matches remain usable. ASCII character-class tables belong
to their pattern and preserve scoped case folding and Unicode fallback.

## Fnmatch

`fnmatch`, `fnmatchcase`, `filter` and `translate` accept strings. Translation
follows CPython's regular expressions, including Unicode ranges. Matching uses
`lib/re`'s code-point handling, and `_compile_pattern` uses a 32,768-entry typed
LRU cache with CPython-compatible statistics. Case normalization is POSIX's
identity operation. Bytes patterns are unsupported.

## Functools

`cache` and `lru_cache` wrap annotated `def` functions. The default `maxsize` is
128; `None` is unbounded, zero disables storage, and negative values become zero.
Bare `@lru_cache` works. Wrappers expose `cache_info`, `cache_clear`, `__wrapped__`,
`__name__` and `__qualname__`. `CacheInfo` contains `hits`, `misses`, `maxsize` and
`currsize`. Clearing resets entries and statistics.

Each wrapper specializes its argument and result types. Accepted key types are
`int`, `bool`, `str`, `str | None`, objects, and tuples of supported key types. An
object argument is keyed by identity, or by its class's `__hash__` and `__eq__`, which
a call may run more than once where CPython's hashes the key once. Defaults
and keyword arguments bind against the original signature, evaluate arguments
in source order, and retain defaults evaluated when the function was defined,
including closure defaults. Functions with nine parameters are supported.

Call spelling remains significant, as in CPython: `f(1)`, `f(1, 2)`, `f(1, b=2)`,
`f(a=1, b=2)` and `f(b=2, a=1)` use distinct entries. Full positional calls use
tuple keys; other forms also record positional count and ordered keyword names.
They share one LRU, capacity, statistics and clearing. Aliases and bound
`__call__` calls use the same keys as direct calls.

Misses count before execution; exceptions are not cached. Recursive insertion of
the same key keeps the existing cache entry, while the outer call returns what
it computed. Hits update recency; eviction removes the least-recently-used
entry. Cached results retain object identity, including falsy results and optional
`None` values.

Unsupported cases are unannotated parameters/results, a result annotated solely
`-> None`, float and NamedTuple keys, variadic functions, builtin/method/lambda targets,
and decorators on class-body methods. Required keyword-only parameters and
explicit keyword-only arguments are unsupported; a keyword-only default may be
omitted. `cache_parameters` is unavailable.

`typed=True` is accepted, but static parameter types already separate the calls
it would distinguish. Programs run on one thread; caches need no lock.
The module uses CPython's C wrapper when CPython imports it.

`reduce(function, iterable[, initial])` folds supported iterables once, including
files and `StringIO`. The callback and accumulator must retain the types inferred
for this call. Omitted initial values, explicit `None`, empty inputs and callback
exceptions follow CPython; integer results retain checked 64-bit arithmetic.

`cmp_to_key(comparator)` returns a key function for `sorted` and list sorting.
The comparator accepts two values of one supported type and returns an int.
Key objects expose writable `obj` and the five comparison methods. `hash()` of one
raises CPython's `TypeError: unhashable type: 'functools.KeyWrapper'`, also where it is
used as a dict key or set element. The factory is a function rather than CPython's
`KeyWrapper`, so factory attributes, reflection and pickling are unavailable.

`partial(func, *args, **keywords)` stores a function, bound method, builtin,
closure or callable object with positional and keyword arguments. A call passes
the stored positional arguments first, and its own keywords replace stored ones.
A partial of a partial is flattened, as in CPython: `func`, `args` (a tuple) and
`keywords` (printing as a dict) hold the merged values. A first argument that is
not callable raises CPython's `TypeError`. Each call is checked against the
function's signature where it is compiled, so a wrong call fails compilation
rather than raising `TypeError`. The attributes can be assigned, unlike C's
read-only ones. `repr()` gives the default `<functools.partial object at ...>`
rather than CPython's call form; pickling, `__dict__` and `partialmethod` are
unsupported.

`@wraps(wrapped)` on a def, and `update_wrapper(wrapper, wrapped)` of a function a def or
lambda makes in a function (or a decorated def), give the wrapper the wrapped function's
`__name__` and `__qualname__`, as CPython's do, with `assigned` naming either (a tuple or
list of str constants, or a module's name that one assignment binds to such a tuple, as
`WRAPPER_ASSIGNMENTS`). The compiler applies them, where CPython's code sets the attributes:
a wrapped function's names must be known as it compiles, so a wrapped `Callable` value makes
the wrapper's names a compile-time error to read, and a wrapped object without them (a
callable object, a `partial`) leaves the wrapper its own, as in CPython. `__wrapped__`,
`__doc__`, `__module__` and `__dict__` are not a function's attributes in Pystachy, and
`wraps(f)` as a value, not a decorator, is a compile-time error. `total_ordering` remains
unsupported: class decorators are not compiled.

## Textwrap

`TextWrapper` and `wrap`, `fill`, `shorten`, `dedent`, `indent` support upstream
options, mutable wrapper options and overridable class attributes. Regex work
uses `lib/re`.

Widths count bytes. Breaking a long non-ASCII word may divide its UTF-8 bytes
across lines. `unicode_whitespace_trans` must map ints to ints, with no string
or `None` replacements; custom tables are looked up byte by byte. Mutated and
custom tables retain their semantics when whitespace fast paths do not apply.
`TextWrapper` subclasses are unsupported.

## String

Constants, `capwords` and `Template` work. Templates support mapping inputs
(dicts or objects with `__getitem__`), keyword arguments or both; keywords take
precedence. `substitute`, `safe_substitute`, `is_valid` and `get_identifiers`,
plus the template and pattern attributes, are available.

Template subclasses are unsupported. Keyword values of different types, as in
`substitute(name="Ann", count=3)`, are looked up as values of their union type.
`Template.flags` is an int, invalid-placeholder columns count bytes, and
`capwords` capitalizes ASCII letters only.

`Formatter` supports `format`, `vformat`, `parse`, `get_field`, `get_value`,
`check_unused_args`, `format_field` and `convert_field`, and subclasses that
override them. `lib/_pystachy_string.py` implements the parsers of CPython's
`_string`, with its errors; `parse()` returns a list, so a malformed format string
raises before its first field is looked up. Automatic and manual numbering,
conversions, nested format specs and recursion limits follow CPython.
Positional arguments may have different types (as may keyword ones): a field's
value has their union type, which formats as its value does. When a call has
both, their types must agree, so `format("{0} {x}", 1, x="s")` is rejected.
`vformat` takes a tuple and a dict, or a `**kwargs` record; type an empty dict.

Field names with attributes or indexes (`{0.x}`, `{0[1]}`) raise `ValueError`, but
`Formatter().format()` of the base class with a constant template whose fields read
attributes, and positional arguments only, formats as `str.format()` of that template does,
which reads the attributes ([reflection](../docs/language/semantics.md#reflection)); a
loop over a constant list of such templates unrolls. `check_unused_args` receives the keys used as a list in first-use order
rather than a set. Overrides compile for every call's argument types in the
program; an override, like other functions, must return one type for each.
Field names count UTF-8 bytes, so only ASCII digits make positional ones.

## Statistics

Supported APIs are `fmean` (including weights), `geometric_mean`, `median`,
`median_low`, `median_high`, `median_grouped`, `quantiles`, `mode` and `multimode`
for the compatible sequence types. Weighted `fmean` uses the port of CPython's
`math.sumprod` algorithm; unsupported iterators are materialized first.

- `median` and `quantiles` require floats: integer/bool inputs can produce
  different return types in CPython. `median_low` and `median_high` retain the
  item type. `median` of strings is unsupported.
- `mode` and `multimode` cannot use float keys. String inputs iterate bytes.
- Integer products in weighted `fmean` can raise `OverflowError` beyond 64 bits;
  CPython's integers continue growing.
- The port's `sumprod` returns a float, including `11.0` for integer inputs and
  `0.0` for empty inputs, where CPython can return an integer.

Unsupported APIs are `mean`, `harmonic_mean`, variance/stdev and their population
variants, `covariance`, `correlation`, `linear_regression`, `kde`, `kde_random`,
and `NormalDist`. These depend on exact fractions, decimal/long integers,
iterators, properties or other features beyond the port's compiled paths. Only
CPython runs the module's import of `random`, which `kde_random` and
`NormalDist.samples` use.

## Random

`Random` objects and the module's functions, which share a hidden instance, give
CPython's values for int, bool and float seeds: `seed`, `random`, `getrandbits`,
`getstate`/`setstate`, `randrange`, `randint`, `choice`, `shuffle`, `sample`
(including `counts=`), `choices` (weights or cumulative weights) and the `uniform`,
`triangular`, `normalvariate`, `gauss`, `lognormvariate`, `expovariate`,
`vonmisesvariate`, `gammavariate`, `betavariate`, `paretovariate`, `weibullvariate`
and `binomialvariate` distributions. `_pyrandom` is the Mersenne Twister of
`_random.Random` in the subset, which CPython builds in, so no `_random.py` can
replace it. `binomialvariate` uses a port of CPython's `math.lgamma` algorithm,
as Pystachy's `math` has none.

- `seed()`, `seed(None)` and `Random()` use the time, process id and monotonic
  clock, CPython's fallback when it cannot read `os.urandom()`.
- A float seeds with its hash, as in CPython; a NaN's hash is 0 rather than
  CPython's object-dependent value.
- `getrandbits(k)` takes at most 63 bits and raises `OverflowError` for more,
  before drawing. `randrange` and `randint` raise `OverflowError` where the width,
  `b + 1` or the width plus the step leaves 64 bits (`randint(a, 2**63 - 1)`).
- Populations are lists, strings and runtime-length tuples; a `range` is not a
  value, so pass `list(range(n))`. Strings are sequences of bytes past ASCII.
  Weights and counts share one numeric type. `sample` raises `TypeError` for a
  `deque`, which `isinstance` does not find a `Sequence`, and takes a dict view,
  which is a list.
- Of the module functions, only `random` and `getrandbits` convert to a typed
  `Callable`; the others are unannotated upstream methods, which unannotated
  parameters or a lambda can take.
- `randrange` and `randint` take ints or bools, and `triangular` floats: with int
  bounds, its `low == high` case would return an int.

Seeds of `str`, `bytes` or `bytearray` (SHA-512 into a long integer), `randbytes`,
`SystemRandom` (absent from `__all__`), subclasses of `Random` (its
`__init_subclass__` chooses how they draw integers) and pickling are unsupported.
An integer passed as `choices`' weights is a compile error rather than CPython's
hint to pass `k=`.

## Urllib.parse

String APIs include `quote`, `quote_plus`, `unquote`, `unquote_plus`, `parse_qs`,
`parse_qsl`, `urlencode`, `urlsplit`, `urlparse`, `urlunsplit`, `urlunparse`,
`urljoin`, `urldefrag` and `unwrap`. Query parsing supports blank values, strict
parsing, maximum field count and custom separators. Encoding accepts mappings
or list/tuple pairs, `doseq`, and a supported `quote_via` function.

Supported codecs are UTF-8, Latin-1 and ASCII, including their codec aliases.
Error modes are `strict`, `ignore`, `replace`, `backslashreplace`,
`xmlcharrefreplace`, `surrogateescape` and `surrogatepass`, where CPython permits
them. Decoding rejects `xmlcharrefreplace` and `namereplace` with `TypeError`;
encoding with `namereplace` raises `NotImplementedError`. Unknown handlers retain
CPython's `LookupError`. Other codecs raise `NotImplementedError`.

`SplitResult`, `ParseResult` and `DefragResult` are NamedTuples with fields,
indexing, unpacking, tuple equality, repr, `_replace` and `geturl`. Invalid IPv6
and bracketed hosts and netloc characters whose NFKC form contains `/?#@:` are
validated. Quoting/unquoting also accepts `str | None`, raising the corresponding
CPython error for `None`.

- Strict codec failures raise `UnicodeError` with the upstream message, rather
  than its `UnicodeEncodeError`/`UnicodeDecodeError` subclasses.
- A Pystachy string can contain invalid UTF-8 bytes. These are quoted byte for
  byte; Latin-1/ASCII treat a byte that begins no character as its numeric value.
- `urlsplit` uses the upstream 128-entry typed LRU cache, including default and
  keyword calls, `cache_info` and `cache_clear`. `clear_cache` also clears the
  adapted string-quote tables. Byte APIs remain unavailable.
- Result properties `username`, `password`, `hostname`, `port`, and `encode`
  are unavailable. Bytes inputs/results, `quote_from_bytes` and
  `unquote_to_bytes` are unsupported.
- `urlencode` needs a mapping or sequence; `doseq` sequences must be homogeneous.
  Sets use Pystachy's iteration order. `allow_fragments` must be a bool.
- Deprecated splitting functions, `to_bytes` and `Quoter` are unsupported.


## Datetime

`timedelta`, `date`, `time`, `datetime`, `timezone`, `tzinfo` subclasses, `MINYEAR`,
`MAXYEAR` and `UTC` are supported. The module is CPython's `_pydatetime`; where CPython's
`_datetime` accelerator behaves differently, the port follows it: error messages, float
`timedelta` arguments (each unit added exactly, fractions rounded once), exact `timedelta`
products and quotients with floats, ISO 8601 parsing, aware `time` comparisons, `repr()` with
`fold` and the `strftime()` format scan.

Supported operations include construction with keywords and range checks; `+`, `-`, unary
operators, `abs()`, `*` and `/` by ints and floats, `//`, `%` and `divmod()` of timedeltas;
comparisons, sorting, `min()` and `max()`; `str()`, `repr()` and `format()`;
`total_seconds()`, `toordinal()`, `fromordinal()`, `weekday()`, `isoweekday()`,
`isocalendar()`, `fromisocalendar()`, `fromisoformat()`, `isoformat()` with `sep` and
`timespec`, `ctime()`, `replace()`, `combine()`, `date()`, `time()`, `timetz()`,
`timetuple()`, `utctimetuple()`, `utcoffset()`, `tzname()` and `dst()`. Aware datetimes
support `timestamp()`, `astimezone(tz)`, `fromtimestamp(t, tz)` and `now(tz)`.
`strftime()` gives CPython's result on Linux: glibc's C-locale directives with flags, widths
and `E`/`O` modifiers, and datetime's `%f`, `%z`, `%:z` and `%Z`. A `tzinfo` subclass
overrides `utcoffset()`, `dst()` and `tzname()`, whose `dt` is a `datetime` or `None`, and
can use the inherited `fromutc()`.

- Pystachy's `time` module has no `localtime()` or `mktime()`. `date.today()`,
  `date.fromtimestamp()`, `datetime.today()`, `now()` and `fromtimestamp()` without a time
  zone, `timestamp()` of a naive datetime, `astimezone()` of a naive datetime or without a
  time zone, `strftime("%s")`, and a `%Z` with flags or a width where `dst()` is not `None`,
  raise `NotImplementedError`.
- `strptime()`, the deprecated `utcnow()` and `utcfromtimestamp()`, pickling and
  `copy.replace()` are unsupported. `hash()` of these objects hashes the fields that
  `_getstate()` packs into bytes upstream (Pystachy has none), so they are dict keys and set
  elements, equal objects hashing alike; the values differ from CPython's.
- `timetuple()` returns a NamedTuple with `time.struct_time`'s nine fields and repr, without
  `tm_zone` and `tm_gmtoff`. `isocalendar()`'s result is a NamedTuple: index or unpack it, as
  `tuple()` of it is unsupported.
- Reflected operators are unsupported: write `timedelta * 2` and `date + timedelta`, not
  `2 * timedelta` or `timedelta + date`.
- `datetime.min` and `datetime.max` are typed `date` (a subclass's class attribute keeps its
  base's type). `fromisoformat()` and `fromtimestamp()` must be called through their class,
  not a `date` object.
- Integers are 64-bit: `total_seconds()`, division, `%` and `divmod()` raise `OverflowError`
  beyond about 106,751,991 days, as does a float count of microseconds of `2**63` or more.
- `timezone(timedelta(0))` is a new object equal to `timezone.utc`, and a `name` of `None`
  means no name. Subclasses of `timezone` are rejected.
- The Python fallback's replacement sentinels remain: an explicit `None` for a numeric
  field in `date.replace()`, `time.replace()` or `datetime.replace()` preserves that field;
  explicit `tzinfo=True` in `time.replace()`, `datetime.replace()` or `datetime.combine()`
  preserves the original time zone. CPython's C implementations reject those explicit
  values with `TypeError`; `tzinfo=None` still removes the time zone.
- Objects of subclasses of `date`, `time` and `datetime` print as their base class, and
  arithmetic and `replace()` return objects of the base class.
- Ordering a `date` with a `datetime` raises the `TypeError` of the reflected comparison.
- Strings are UTF-8 bytes: `fromisoformat()` rejects a non-ASCII separator, and its length
  checks count bytes, as `_datetime`'s parser does.

## Binascii

`binascii` is `_pystachy_binascii`, a port of CPython's C module (`Modules/binascii.c`) to the
subset. Pystachy loads it for `import binascii`, where CPython imports its C module; as for the
other modules that Debian's CPython builds in, a `binascii.py` on the module path is never
imported. All twelve functions are there,
with the C module's signatures, results and errors (`binascii.Error`, a `ValueError`, with its
messages): `hexlify` and `b2a_hex` with `sep` and `bytes_per_sep`, `unhexlify` and `a2b_hex`,
`b2a_base64` and `a2b_base64` (with `strict_mode`), `b2a_uu` and `a2b_uu` (with `backtick`),
`b2a_qp` and `a2b_qp` (with `quotetabs`, `istext` and `header`), `crc32` and `crc_hqx`.
`binascii.Incomplete` exists, as in CPython, where no function raises it.

- Binary data is `bytes`, as Pystachy has no `bytearray`, `memoryview` or `array`. The `a2b_*()`
  functions also take a `str` of ASCII characters, as CPython's do. Another type of argument
  is a compile-time error, where CPython raises `TypeError`.
- `hexlify(data, None)` and `b2a_hex(data, None, n)` separate nothing, as without a `sep`, where
  CPython raises `TypeError` ([deviation](../tests/deviations/lib_binascii_sep_none.py)).
- The functions are Python functions, whose reprs are `<function hexlify at ...>`, not
  `<built-in function hexlify>`. `a2b_base64.__doc__` is CPython's docstring without the
  indentation of its option's description, which CPython 3.13 removes from a Python function's
  docstring.

## Codecs

`codecs` is CPython 3.13.16's `Lib/codecs.py` with three marked edits, on `_pystachy_codecs`,
a subset port of the C module `_codecs` that Pystachy loads for `import _codecs`. The BOM
constants, `encode()`, `decode()`, `lookup_error()`, `register_error()`, `strict_errors()` and
the incremental classes (derived from with methods) work as in CPython, and so do the codec
functions of UTF-8, Latin-1, ASCII and charmap (`utf_8_encode()`, `utf_8_decode()` that is not
final, `charmap_build()`, `charmap_encode()`, `charmap_decode()`, ...) with every builtin error
handler but `namereplace`, raising CPython's `UnicodeDecodeError` and `UnicodeEncodeError` with
its messages.

- Encoding with `namereplace`, which needs the characters' names, raises `LookupError: unknown
  error handler name 'namereplace'`, as `str.encode()` does
  ([language reference](../docs/language/compatibility.md)), where CPython writes `\N{...}`.
- `codecs.lookup()`, which Pystachy has no codec registry for, raises `NotImplementedError`
  ([deviation](../tests/deviations/lib_codecs_lookup.py)); reading its result's attributes, as
  `getencoder()` and the other functions built on it do, is a compile-time error. `register()`
  and `unregister()` do nothing.
- The UTF-16, UTF-32, UTF-7 and escape codec functions raise `NotImplementedError`, and so do the
  error handler functions but `strict_errors()` (`ignore_errors()`, ...), which read attributes
  that Pystachy's `UnicodeError` does not have. A handler `register_error()` registers is one that
  `lookup_error()` gives; `str.encode()`, `bytes.decode()` and the charmap codec take only the
  builtin handlers' names.
- `charmap_build()` gives a dict of code points to bytes, where CPython's is an `EncodingMap`
  object (but a dict where the table does not start with U+0000 or leaves the BMP), and
  `charmap_decode()` takes a decoding table, a str, not a dict.
- A class attribute that binds a function of a subclass's codec (`_buffer_decode =
  codecs.utf_8_decode`, as the `encodings` modules bind them) over a method of its base is not
  supported: define the method with `def`.
- `codecs.strict_errors.__name__` and the other handlers' are unsupported: the handlers are
  `Callable` values.

The edits: the error handlers are bound without the `except LookupError` clause for builds
without them, which binds them to `None`; the four incremental classes' `errors` parameters
are annotated, so that the classes are no templates; and the `import encodings`, which never
runs, is left out.
