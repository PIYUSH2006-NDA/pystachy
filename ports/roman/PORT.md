# roman 5.2, ported to Pystachy

[roman](https://pypi.org/project/roman/) converts the integers 0 to 4999 to Roman numerals and
back: `toRoman(1987)` is `"MCMLXXXVII"`, and `fromRoman("mcmlxxxvii")` is 1987. It checks a
numeral with a regular expression and reports errors through a small exception hierarchy
(`RomanError`, and below it `OutOfRangeError`, `NotIntegerError` and
`InvalidRomanNumeralError`). Mark Pilgrim wrote it for *Dive Into Python* in 2001, and the
Zope Foundation maintains it. It is rank 3,715 on PyPI in October 2026. Its best-known users are
documentation tools: docutils shipped a copy of it, `docutils/utils/roman.py`, until 0.22
replaced it with its own code; Debian's `python3-docutils` drops that copy and depends on
`python3-roman` instead; and Sphinx's LaTeX writer (7.4, 8.1) falls back to
`from roman import toRoman` when `docutils.utils.roman` is missing, to name the LaTeX counters
of nested enumerated lists (`enumi`, `enumii`, ...). deps.dev lists 65 packages on PyPI that
depend on roman 5.2 directly. This is its one module from the sdist
`roman-5.2.tar.gz` (SHA-256
`275fe9f46290f7d0ffaea1c33251b92b8e463ace23660508ceef522e7587cb6f`), under the Zope Public
License 2.1 (`LICENSE`).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `7d8962ca4ed71a67e0d07d0f6e81deb0f0b177565375d5ff39be1b1dc50e16f5` | 4 regions, and the notice of change |

`py.typed`, the empty marker for type checkers, is left out, and so is the rest of the sdist:
packaging (`setup.py`, `setup.cfg`, `pyproject.toml`, `tox.ini`), the README, the change log and
`tests.py`, whose cases `tests/port_roman_convert.py` runs. Every edit is marked
`# Pystachy port:` in the source, and `diff -u` against the sdist's `src/roman/__init__.py`
shows them all. Under its license header, the file also states that it was changed and when, as
clause 5 of the ZPL asks of a modified file.

## The edits, and the feature each one stands in for

**Native standard-library hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11), M6).**
The module imports `argparse` and `re` at its top, and Pystachy has neither:
`module 'argparse' is not supported: it is not a builtin module (...) and there is no argparse.py
on the module path`, and then the same for `re`.

1. The imports: `import re` is dropped, and `import argparse` moves into `parse_args()`, its
   only user, which parses the arguments of the `roman` command (4 below).
2. `romanNumeralPattern = re.compile(...)` becomes `_romanNumeralPattern_search(s)`, a function
   of 21 lines that answers what `romanNumeralPattern.search(s)` answered for the pattern
   `^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$` (written in `re.VERBOSE` form
   upstream). It keeps `$`'s match before one final newline, so `fromRoman("X\n")` is 10 and
   `fromRoman("\n")` is 0, as upstream. It does not backtrack, and does not need to: where two
   alternatives of a group both match (`CM`, and `C` by `D?C{0,3}`), the shorter leaves a letter
   that no later part of the pattern matches (the `M`), so only the first can lead to a match.
   Under CPython, it agrees with upstream's compiled pattern on all 2,396,745 strings of up to
   seven characters drawn from the seven numeral letters and the newline.
3. `fromRoman` calls it: `if not _romanNumeralPattern_search(s):`.
4. `parse_args()` opens with `import argparse`, and its return annotation is quoted,
   `-> "argparse.Namespace"`: CPython evaluates the annotation when the `def` runs, and
   `argparse` is no longer a global then. Pystachy checks this as CPython would (unquoted, it
   reports `name 'argparse' is not defined (CPython evaluates this annotation when the def
   statement runs: quote it, ...)`).

A native `re` that handles this pattern (counted repeats, alternation, `?`, the anchors and
`re.VERBOSE`) would undo 2 and 3 and the `re` half of 1; a native `argparse`, the rest.

## What compiles as it is

`toRoman` and `fromRoman`, and everything they use: the four exception classes, each a
`pass` body deriving from `Exception` or from `RomanError`, raised with a message and caught by
their base class; the module-level table `romanNumeralMap`, a tuple of `(str, int)` pairs
walked by `for numeral, integer in romanNumeralMap`; `isinstance(n, int)` on the `int`
parameter (decided at compile time); the chained comparison `-1 < n < 5000`; `result += numeral`
in a loop; slices `s[index:index + len(numeral)]`; `s.upper()`; `'Invalid Roman numeral: %s' %
s`; the `bool` parameter `special_case` with its default, given by position or keyword; and the
module strings `__author__` and `__copyright__`. The `if __name__ == "__main__":` block is
dropped in an imported module, as CPython skips it.

## What the port leaves out

- The command-line interface, `parse_args()` and `main()` (the sdist's `roman` command). They
  stay in the source, and CPython runs them from the port as from upstream, but they need
  `argparse`: a program that calls `roman.main()` is rejected at compile time with
  `roman.parse_args() is not supported: return annotation: unsupported type annotation`.
  Pystachy compiles a function of an imported module only where a program uses it, so the rest
  of the module is not affected.
- `roman.romanNumeralPattern`, the compiled pattern: `module 'roman' has no attribute
  'romanNumeralPattern'`. Its stand-in returns a `bool`, where `search()` returned a match
  object or `None`.
- Arguments of other types than the annotated ones (`n: int`, `s: str`, `special_case: bool`).
  `toRoman(1.5)` and `toRoman("1")` are compile-time errors (`expected int, got float`), where
  CPython raises `NotIntegerError("decimals cannot be converted")`; and `toRoman(True)` is
  rejected too (`expected int, got bool`), where CPython returns `'I'`. So are
  `fromRoman(None)` (`expected str, got None`), which CPython reports as
  `InvalidRomanNumeralError("Input cannot be blank")`, and `fromRoman("X", 1)` (`expected bool,
  got int`), which CPython answers with 10. A variable that holds an `int` or another type needs
  dynamic values, M4 ([#9](https://github.com/den-run-ai/pystachy/issues/9)). `NotIntegerError`
  itself is there, and a program can raise and catch it.
- `romanNumeralMap` as a whole value. A program can index it, take its `len()`, iterate over it,
  test `in` and make a `list()` or `sorted()` of it, but it holds 13 pairs, and a tuple of more
  than 9 items ([docs/language.md](../../docs/language.md#types)) cannot be printed or compared
  (`tuples are limited to 9 elements`). `dict(roman.romanNumeralMap)` and slices of it are
  compile-time errors too (`unsupported call dict(...)`, `... cannot be sliced`), as they are
  for any tuple here. CPython does all of these.

## Deviations it hits

- **`str` is UTF-8 bytes, and its case mapping knows only ASCII**
  ([docs/language.md](../../docs/language.md#deviations-from-cpython)). `fromRoman` upper-cases
  its argument (`s = s.upper()`), so lower-case numerals are accepted. Numerals are ASCII, and
  every ASCII string gives what it gives in CPython; non-ASCII strings differ in two ways:
  - CPython upper-cases `ı` (U+0131, the dotless i) to `I`, the only character outside ASCII
    whose upper case is a numeral letter: `fromRoman("ı")` is 1 and `fromRoman("xı")` is 11.
    Here both raise `InvalidRomanNumeralError` (`Invalid Roman numeral: ı`, `... Xı`).
  - The message of `InvalidRomanNumeralError` holds the upper-cased string: for `fromRoman("é")`
    CPython says `Invalid Roman numeral: É` and Pystachy `Invalid Roman numeral: é` (also
    `ß` for CPython's `SS`, and `ⅻ`, U+217B, for CPython's `Ⅻ`). Characters without a case, such
    as `Ⅻ` (U+216B) and `中`, give the same message in both; the tests use them.

  The stand-in for the pattern indexes bytes, but that does not show: no byte of a character
  outside ASCII is a numeral letter or a newline, so such a string fails to match in both.
- **`int` is 64-bit.** `toRoman` accepts 0 to 4999 and raises `OutOfRangeError` for every other
  `int`, here as in CPython; the tests use 2**63 - 1, -(2**63 - 1) and -2**63. A bigger int
  cannot be made: `toRoman(int("100000000000000000000"))` raises `OverflowError` (`int() result
  does not fit in 64 bits`) in `int()`, where CPython raises `OutOfRangeError`.

## Tests

`tests/port_roman_convert.py` runs the cases of roman's own test suite (`src/tests.py` in the
sdist) as a program: the 20 pairs of its `TEST_MAP` both ways and in lower case, and its errors
(100000 out of range, `''` and `'Q12'` invalid, `'n'` with `special_case=False`). Then it runs
the range's edges (-1, 5000, 2**63 - 1, -(2**63 - 1), -2**63), `N` and `n` and `'N\n'` with
`special_case` given by position and by keyword, the exception hierarchy (`isinstance()`,
`type(e).__name__`, a `NotIntegerError` raised by the program), every number from 1 to 4999
there and back, in upper and lower case, other call forms (`import roman as rm`,
`toRoman as to_roman`, every argument by keyword and in either order), `__author__`,
`__copyright__` and the uses of `romanNumeralMap` that compile, and last an `OutOfRangeError`
that escapes, whose report must match CPython's last line of stderr.
`tests/port_roman_validate.py` runs the validation that edit 2 replaces: 59 strings at the
pattern's edges (a group's alternative followed by the letter another one would leave, as in
`CMCM`, `CDC`, `XCX` and `IXI`; too many letters of a kind; `$` before a final newline and not
before two, before `\r\n` or before another line break such as `\r`, `\x0b`, `\x85` and
`\u2028`; a leading newline, spaces, a tab, NUL, `%` signs, 50 M's, and four strings with
characters outside ASCII that have no case), then every string of one to four numeral letters,
2,800 strings of which 347 are valid, with a checksum of their values. They leave out what the
edits remove (the command line, which upstream's tests drive through `sys.argv` and `StringIO`)
and `toRoman('1')`, which Pystachy rejects at compile time.

`tests/run.sh` compares what they print with CPython's, JIT and AOT. Run under CPython against
the unmodified upstream package, both print exactly what they print against this port. Both
are small: under `make verify`'s gc-stress stage (the compiler collecting every 1,000
allocations, the program at every allocation), the JIT run and the AOT build and run take about
2-3 s together for each of them, on a 4-core VM that was running other jobs; each AOT build
takes 0.7-1.5 s.

## Speed

The headline workload: 200 round trips `fromRoman(toRoman(n))` for every `n` from 1 to 4999,
about a million conversions each way (checksum 2499500000 in all three). Median of 5 runs, with
process start-up, on a 4-core x86-64 VM that was running other jobs (load average 5-7):

| | wall clock | CPU time |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.631 s | 0.621 s |
| CPython 3.13.16, unmodified roman 5.2 | 2.353 s | 2.350 s |
| CPython 3.13.16, this port | 2.948 s | 2.940 s |

That is 3.7 times faster. Two more sets of 5 runs gave the same in CPU time (0.629 s against
2.331 s and 2.319 s), and an earlier measurement, median of 3, gave 0.646 s against 2.181 s of
wall-clock time (3.4 times). roman has no C extension, but CPython checks each numeral in its C
regex engine: under CPython the port, whose check is the Python function of edit 2, is slower
than upstream, so the executable runs the code of this port 4.7 times faster than CPython does.
