# snowballstemmer 3.1.1, ported to Pystachy

[snowballstemmer](https://pypi.org/project/snowballstemmer/) holds the Snowball stemmers in pure
Python: they reduce the forms of a word to one stem for a search index (*connection*,
*connected* and *connecting* to *connect*). Sphinx stems the words of its HTML search index with
it, and pydocstyle uses it too (rank 652 on PyPI in October 2026). Its 36 stemmers are classes
that the Snowball compiler generates from the algorithms' descriptions. This port has the two
English ones, `EnglishStemmer` (Snowball's "english", the Porter2 algorithm) and
`PorterStemmer` (Martin Porter's original algorithm), and the modules they need, from the sdist
`snowballstemmer-3.1.1.tar.gz` (SHA-256
`e07bbc54a0d798fe6010a12398422e62a8bfbba95c394fd0956ef58cb4d3e260`), BSD-3-Clause licensed
(`LICENSE`, the sdist's `COPYING`).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `b7deb373e5cfeb67267dde276350bebfc4b35221949145806090706cec3f681a` | 2 |
| `among.py` | `4b8b17bf3f97d46a1a536c288defe193147b15bd8edb01bbd3f64c57b8b5e2af` | 2 lines |
| `basestemmer.py` | `e60fd08f93826b9c428f038ace77500a68ba594d504cd64b1501a6fab2becbc1` | 26: 22 signatures, the fields, an import, 2 branches |
| `english_stemmer.py` | `350d71588d33ce8e2dd5084efa48c50cbaec90bec9ac3f7e97623fd640856dea` | 22, mechanical: the base class and a copy of its body, 15 return types, 4 groupings, 1 tuple |
| `porter_stemmer.py` | `b7e27d0486805a9ce69be3362dc3f995b988c4d607de438df189c21e4482b8b0` | 19, mechanical: the base class and a copy of its body, 12 return types, 2 groupings, 3 tuples |

The other 34 stemmer modules are left out (below). Every edit is marked `# Pystachy port:` in the
source, and `diff -ru` against the sdist's `src/snowballstemmer` shows them all (and an "Only in"
line for each module left out).

## The edits, and the feature each one stands in for

Inheritance and unannotated methods (M2, [#7](https://github.com/den-run-ai/pystachy/issues/7)):

1. Each generated stemmer derives from `BaseStemmer`, which holds the word, the cursor and the
   operations the generated code calls (`in_grouping`, `find_among_b`, `slice_from`, ...).
   `english_stemmer.py` and `porter_stemmer.py` drop the base class and hold a copy of
   `BaseStemmer`'s class body instead (the flattening below). They still import
   `BaseStemmer`, which nothing then uses.
2. 22 of `BaseStemmer`'s 24 methods are annotated (`in_grouping(self, s: list[str]) -> bool`,
   `find_among(self, v: list[Among]) -> int`, `slice_to(self) -> str`, ...), with
   `from .among import Among` for the annotation, and so is `Among.__init__`: a method's
   parameters must be annotated, and a method without a return annotation returns `None`.
3. The generated methods (`__r_Step_1a(self)` and the others, and `_stem(self)`) get
   `-> bool`, 15 in english and 12 in porter, for the same reason.
4. `BaseStemmer` declares the six fields that `set_current()` assigns (`current: str`,
   `cursor: int`, ...): Pystachy takes fields from the class body, or from `self.x = ...` in
   `__init__` itself, and `__init__` only calls `set_current()`.

Functions as values (M3, [#8](https://github.com/den-run-ai/pystachy/issues/8)):

5. `Among` loses its `method=` parameter and field, and `find_among` and `find_among_b` the
   branches that call `w.method(self)`: a method of the stemmer stored in a table. Only the
   finnish, hindi and polish stemmers pass one.

Classes as values and unions (M2 [#7](https://github.com/den-run-ai/pystachy/issues/7), M4
[#9](https://github.com/den-run-ai/pystachy/issues/9)):

6. `__init__.py` drops `_languages`, which maps names to classes, and `stemmer(lang)`, which
   returns an object of whichever class `lang` names; `algorithms()` returns
   `['english', 'porter']`. Make the stemmer itself: `EnglishStemmer().stemWords(words)`. The
   package also imports the two ported modules only. A stemmer module that is not flattened is
   rejected where it is imported ("class inheritance is not supported": CPython runs the class
   body, which calls `Among(...)`, at import), and so are the finnish, hindi and polish ones
   flattened, whose tables pass a method (`Among("han", 11, -1, __r_A)`: "class attribute
   '__r_A' of 'FinnishStemmer' used in a class-body default is not supported").

Tuples indexed by a variable (M1, [#6](https://github.com/den-run-ai/pystachy/issues/6)):

7. The `as_N` tuples of replacement strings, indexed by `among_var - 1`, are lists: one in
   english, three in porter (whose `as_3` also has 13 items, more than the 9 of a tuple).

Sets (M7, [#12](https://github.com/den-run-ai/pystachy/issues/12)):

8. The groupings, sets of one-character strings such as `g_v = {"a", "e", "i", "o", "u", "y"}`,
   are lists of the same strings, and `BaseStemmer`'s grouping tests take a `list[str]`; the
   one grouping Snowball writes as a string, english's `g_aeo = "aeo"`, is the list of its
   characters, since a parameter has one type. `x in g` is then the set's test for any string
   `x`. A string `"aeiouy"` would give the same stems for these groupings, which are all ASCII
   letters, and run faster (Speed, below), but `in` of a string is a substring test, the set's
   test only for one ASCII character: an evaluation that flattened the Italian stemmer with
   string groupings got `citt` and a stray byte for `città`, where lists give `città`, valid
   UTF-8 if not CPython's `citt`.

### The flattening

Edits 1, 3, 7 and 8 of the two generated modules are mechanical, as the Snowball compiler writes
every module from one template, and can be redone for a new release or another language:

1. Copy the module from the sdist.
2. `class XStemmer(BaseStemmer):` becomes `class XStemmer:`, and after the class docstring comes
   a copy of the class body of the ported `basestemmer.py` (every line after
   `class BaseStemmer:`) between the comments `BEGIN copy of BaseStemmer` and
   `END copy of BaseStemmer`, with `"BaseStemmer"` (the annotation of `copy_from`'s parameter)
   renamed to the class's name.
3. Each `def __r_NAME(self):` and `def _stem(self):` gets `-> bool`.
4. Each grouping `g_NAME = {"a", "b"}` becomes `g_NAME = ["a", "b"]`, and `g_NAME = "ab"`
   becomes `["a", "b"]`.
5. Each `as_NAME = (...)` becomes `as_NAME = [...]`.

Each changed line gets its `# Pystachy port:` comment. This checks that a module's copy is
`basestemmer.py`'s (it prints nothing):

```sh
cd ports/snowballstemmer
sed '1,/^class BaseStemmer:/d' basestemmer.py > /tmp/body
sed -n '/BEGIN copy of BaseStemmer/,/END copy of BaseStemmer/{//!p;}' english_stemmer.py |
  sed 's/"EnglishStemmer"/"BaseStemmer"/' | diff - /tmp/body
```

Applied to all 36 modules, these steps alone give 33 that compile; finnish, hindi and polish
need the `method=` callbacks (#8) besides.

## What compiles as it is

The generated code's idioms: Snowball's gotos, `raise lab0()` out of a `try` block whose
`except lab0: pass` is the label, with `lab0` to `lab2` module-level `BaseException` subclasses;
`while True:` loops left by `break` and `continue` from inside those `try` blocks; name-mangled
private methods (`self.__r_Step_1a()`); class-body tables of `Among(...)` objects read as class
attributes (`EnglishStemmer.a_2`); and class-body defaults such as `B_Y_found = False` and
`I_p1 = 0` as fields, which the methods assign. `BaseStemmer`'s string work compiles as it is:
slices and concatenation in `replace_s`, `startswith` and `endswith` with a start and an end,
`ord()` differences in the binary searches of `find_among` and `find_among_b`, `>>`, `min()`,
`assert`, and the list comprehension of `stemWords`. So does the optional import of PyStemmer, a
C extension (`try: import Stemmer` / `except ImportError:`): Pystachy finds no `Stemmer` module and
takes the pure-Python branch, as CPython does without PyStemmer. The package imports no module of
the standard library, so it needs none of the native stdlib hubs
([#11](https://github.com/den-run-ai/pystachy/issues/11)).

## What the port leaves out

- The other 34 stemmers, from arabic to yiddish, and `stemmer(lang)` (edit 6). Flattened, 33
  of them compile, but they do not stem words with non-ASCII letters as CPython does: their
  groupings hold such letters, which the one byte of the word a grouping test takes never
  equals, and their rules count bytes where CPython counts letters (the deviation below).
  Flattened as above, the Italian stemmer leaves `città` as it is and stems `perché` to
  `perchè`, where CPython gives `citt` and `perc`, and the French one stems `élégantes` to
  `élégant` for `éleg`. They would need strings indexed by code point, which no roadmap item
  has.
- `Among`'s `method=` callbacks (edit 5).
- PyStemmer: Pystachy compiles no C extensions.

## Deviations it hits

- `str` is a byte string holding UTF-8 ([docs/language.md](../../docs/language.md)): Snowball's
  cursor moves one character at a time in CPython and one byte at a time in Pystachy, so a word
  with non-ASCII letters can stem differently where a rule counts letters or looks at the one
  before the cursor. Words of ASCII letters stem as in CPython. In Porter2, `éies` stems to
  `éie` in CPython and `éi` in Pystachy (step 1a keeps `ie` after one letter, and `é` is two
  bytes), `éy` to `éy` and `éi` (step 1c turns `y` into `i` after a non-vowel that is not the
  first letter), `aéing` to `aée` and `aé`, and `eïed` to `eïe` and `eï`. With `€ies` and `ñy`,
  these were 6 of the 50 non-ASCII words that the evaluation and its verifier tried, all in
  Porter2; the others, and all 50 in Porter, stem as in CPython (`naïvely` to `naïv`, `cafés`
  to `café`, `résumés` to `résumé`), and every stem was valid UTF-8.
- 64-bit `int`: not hit; the integers are positions in the word.

## Tests

`tests/port_snowballstemmer_stem.py` stems 345 English words, chosen for the suffixes each step
of the two algorithms removes or rewrites, and holds each one's Porter2 and Porter stems (as the
upstream package stems them under CPython): it prints any word that stems otherwise, and then
the stems of the edge cases the evaluation and its verifier tried: the empty word and short
words, apostrophes, `y` and `Y`, Porter2's exception lists and the prefixes it gives a region of
their own, capitals, digits and spaces, a word of 3,003 letters, `stemWords` of `[]` and `[""]`,
the cursor API (`set_current`, `slice_to`, `slice_from`, `insert`, `copy_from`), six non-ASCII
words that stem as in CPython, and 300 pseudo-random words; and `tests/run.sh` compares what it
prints with CPython's, JIT and AOT. It leaves out the names `algorithms()` returns (36
upstream: it prints whether `english` and `porter` are among them) and the non-ASCII words of
the deviation above. Run under CPython against the unmodified upstream package, it prints
exactly what it prints against this port. The evaluation's and its verifier's longer drivers,
run against this port, print what CPython prints against the upstream package too: 106 words
(21 of them not in the test), a word of 30,003 letters and 30,000 pseudo-random words.

The test runs in 0.46 s JIT, and its AOT build takes 3.1 s (the executable then runs in
0.01 s). Collecting at every allocation (`PYSTACHY_GC_STRESS_PROGRAM=1`, compiled with
`PYSTACHY_GC_STRESS=1000`), it runs in 1.2 s JIT and in 3.8 s AOT, build included. These are
wall-clock medians of 3, taken while other jobs kept this 4-core VM's load average near 13, so
they are upper bounds.

## Speed

The evaluation's workload: 1,000 words (40 roots with 25 suffixes each) stemmed 200 times by
both stemmers, 400,000 stems, which prints a checksum and the first 12 stems (CPython prints the
same). Built AOT against this port it takes 0.54 s, and CPython 3.13 takes 6.62 s on the
unmodified upstream package: 12.2 times as long. These are user and system CPU time, median of
3, on this 4-core x86-64 VM, which other jobs kept busy at the time (load average near 14): wall
clock, the runs took 0.76 s and 8.98 s. CPU time is the fairer measure here: the string
groupings that edit 8 turns down take 0.41 s of it, and the evaluation measured 0.426 s wall
clock for them on a quiet VM, against 6.565 s for CPython (15.4 times). So the list groupings
cost about a third more than strings would, the price of exact grouping tests.
`snowballstemmer.stemmer()` returns PyStemmer's stemmers, a C extension, when that is installed;
it is not installed here (`import Stemmer` fails), and the workload makes the pure-Python classes
itself in any case.
