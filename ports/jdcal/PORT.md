# jdcal 1.4.1, ported to Pystachy

[jdcal](https://pypi.org/project/jdcal/) converts dates of the proleptic Gregorian and Julian
calendars to Julian dates and back, in pure float arithmetic. It keeps a Julian date as two
floats whose sum is the date (by default `MJD_0`, 2400000.5, and the Modified Julian Date), so
that the fraction of the day keeps its precision; its algorithms come from Jeffrey W.
Percival's TPM C library. It is rank 2,158 on PyPI in October 2026. Its users included
openpyxl, the Excel library (rank 105), which required it up to 3.0.6 (January 2021):
`openpyxl.utils.datetime` converted Excel's serial dates with `gcal2jd`, `jd2gcal` and `MJD_0`.
The port is the one module of the sdist `jdcal-1.4.1.tar.gz` (SHA-256
`472872e096eb8df219c23f2689fc336668bdb43d194094b5cc1707e1640acfc8`), under a 2-clause BSD
license (`LICENSE`, the sdist's `LICENSE.txt`).

| file | upstream file and SHA-256 | edits |
|---|---|---|
| `__init__.py` | `jdcal.py`, `a6c5e84e873d794bf0d38c2a32ac3e75653c89823458db7314255c6f40c11871` | 2 lines |

jdcal is a single module, `jdcal.py`, which the port keeps whole as `ports/jdcal/__init__.py`:
the port gets a directory of its own for the module, its license and this file, as the other
ports have, and `import jdcal` finds the package with `ports` on the path, under Pystachy and
CPython alike. The rest of the sdist is `test_jdcal.py` (pytest), the README and packaging
(`setup.py`, `setup.cfg`, `MANIFEST.in`, the egg-info). Every edit is marked
`# Pystachy port:` in the source, and `diff jdcal-1.4.1/jdcal.py ports/jdcal/__init__.py`
shows them all.

## The edits, and the feature each one stands in for

**M4, dynamic values ([#9](https://github.com/den-run-ai/pystachy/issues/9)).** Both edits are
of a variable or a result that holds values of two types in CPython, where Pystachy gives each
one type.

1. `jcal2jd`: `jd = 367 * year` becomes `jd = float(367 * year)`. `jd` is an `int` there and a
   `float` one line later, after `jd -= ipart(...)` (`ipart` returns a float): M4's "a variable
   rebound to another type". Unmodified, the module is rejected at the `-=` (`expected int,
   got float`). The value is the same: CPython converts the int to a float at the subtraction,
   the port a line earlier, and both round the same int to the nearest float. (The tests check
   years up to 2.5e16; beyond 2.51e16, `367 * year` does not fit in 64 bits, as the deviations
   below say.) An annotation would not do: `jd: float = 367 * year` is rejected (`expected
   float, got int`), as Pystachy does not turn an `int` into a `float` implicitly.
2. `is_leap`: `return not x and (y or not z)` becomes `return not x and (bool(y) or not z)`.
   `x`, `y` and `z` are `math.fmod` results, floats, and `y or not z` gives `y` itself when it
   is not zero, else a bool, so upstream's `is_leap` returns `False`, `True` or a float:
   `is_leap(2024)` is `24.0` and `is_leap(2004)` is `4.0` (`expected float, got bool`
   unmodified: a union of `bool` and `float`). With `bool(y)` it returns a bool with the same
   truth value, `True` for 2024. This changes what `is_leap` returns, not its truth: code that
   tests it (`if is_leap(y):`, as upstream's own tests do) behaves as upstream, and code that
   prints it or compares it with `==` does not.

The four conversions need only edit 1 (they do not call `is_leap`); `gcal2jd`, `jd2gcal` and
`jd2jcal` compile unmodified. `docs/stdlib.md` lists jdcal at "4 edits, or `math.modf` in the
runtime and 1 edit": `math.modf`, one of the runtime gaps of M1's item 7
([#6](https://github.com/den-run-ai/pystachy/issues/6)), is in the runtime now, and this port is
that 1 edit, plus 1 for `is_leap`.

## What compiles as it is

Every function of jdcal is unannotated, so each one is a template, compiled once for each set
of argument types a program calls it with. As they are: `math.modf` (indexed, and unpacked into
two names) and `math.fmod`, on ints and floats; `from math import modf` inside a function;
`from __future__ import division` and `print_function`; the module docstring, `__version__` and
the constants; chained comparisons (`-0.5 < f < 0.5`) and the `if`/`elif` chain that moves the
day to noon; ints and floats mixed in arithmetic (an int day added to a float); `int()` of a
float, with CPython's `ValueError` for NaN; and tuples of floats and of three ints and a float
as results. `jd2gcal` and `jd2jcal` take ints as well as floats.

## What the port leaves out

Nothing of the module's code. Two kinds of call that CPython accepts are rejected at compile
time:

- float and str dates. `gcal2jd` and `jcal2jd` begin with `year = int(year)`, and the same for
  `month` and `day`, which rebinds the parameter to an int: with an int argument that keeps its
  type, but with a float or a string it does not. `gcal2jd(1996, 4, 3.5)`, which upstream's
  `test_gcal2jd_is_for_mid_night_of_given_day` uses, is rejected with `expected float, got int`
  at `day = int(day)`, and `jcal2jd("2000", "1", "1")` with `expected str, got int` (M4,
  [#9](https://github.com/den-run-ai/pystachy/issues/9)). The docstrings ask for ints; a caller
  passes `int(3.5)`.
- `jd2gcal(*gcal2jd(2000, 1, 1))`, the docstrings' idiom: `star arguments are not supported`
  (the `f(*args)` form of M3, [#8](https://github.com/den-run-ai/pystachy/issues/8)).
  `g = gcal2jd(2000, 1, 1)` and `jd2gcal(g[0], g[1])` do the same.

## Deviations it hits

- **`int` is 64-bit** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  `jd2gcal` and `jd2jcal` return the year as an `int`, and from a Julian date beyond about
  3.4e21 days (a year past 2**63) Pystachy raises `OverflowError: float too large for a 64-bit
  int` where CPython returns a big int: `jd2gcal(1e300, 0.0)` gives a year of 298 digits in
  CPython. `jcal2jd` multiplies `367 * year` in ints, so beyond |year| = 2.51e16 it raises
  `OverflowError: integer result does not fit in 64 bits`: `jcal2jd(26 * 10**15, 1, 1)` is
  `(2400000.5, 9.496499999999322e+18)` in CPython. `gcal2jd` computes in floats and takes any
  64-bit year. Such dates are far beyond any calendar; the tests go up to Julian dates of 1e18
  days and years of 2.5e16, and agree with CPython there.
- **`str` is UTF-8 bytes**: jdcal handles no text, so this deviation does not arise.

## Tests

`tests/port_jdcal_convert.py` runs the cases of jdcal's own test suite (`test_jdcal.py` in the
sdist, run under pytest there) and the examples of its docstrings as a program: `ipart` (and
its `-0.0`), `is_leap` tested for truth, 14 dates from the year -4699 (4700 BC) to 9999 in
both calendars and back through both inverse functions, 11 out-of-range months and days that
carry over (day 0, month 13, negative months and days), round trips, the fraction of the day
(including `jd2gcal(2451545.0, -0.5)`, whose fraction is 1.0 in both), Excel serial dates as
openpyxl computed them, and the suite's random round trip, 1,000 dates drawn by a linear
congruential generator instead of `random`. It leaves out the comparison with ERFA's `cal2jd`,
which needs astropy and numpy, and passes `int(3.5)` where the suite passes 3.5 (above).
`tests/port_jdcal_extremes.py` runs the edge cases an independent check of the port added:
Julian dates up to 1e18 days and down to -1e15, `-0.0`, fractions next to 0.5 and of 1e-300,
years of ±10**9, 10**12, ±2**52 and 2.5e16 in both calendars, int arguments to `jd2gcal` and
`jd2jcal`, NaN and both infinities (`ValueError: cannot convert float NaN to integer`), and
`is_leap` of negative years, ±2**62 and floats. `tests/run.sh` compares what they print with
CPython's, JIT and AOT. Run under CPython against the unmodified upstream module, both print
exactly what they print against this port. Both are small: under `make verify`'s gc-stress
stage (the compiler collecting every 1,000 allocations, the program at every allocation), each
takes 0.8 to 1.6 s for the JIT run and the AOT build and run together, and each AOT build
0.6 to 1.2 s.

## Speed

The headline workload: 2,688,000 round trips through all four functions, every day 1 to 28 of
every month of the years -4000 to 3999 taken from the Gregorian calendar to a Julian date and
back, then to the Julian calendar and back to a Julian date (0 mismatches, and the same output
in both). Wall clock with process start-up, and the CPU time (user + system), median of 3
runs, on a 4-core x86-64 VM that was running other jobs (a load average of 8 to 11):

| | wall clock | CPU time |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.628 s | 0.499 s |
| CPython 3.13.16, unmodified jdcal 1.4.1 | 12.042 s | 9.618 s |

That is 19.2 times faster (19.3 in CPU time); a second set of runs gave 0.590 s and 12.205 s
(20.7 times; CPU time 0.497 s and 9.516 s, 19.1 times), and the evaluation of the port, on
the same VM two days before, 0.587 s and 9.353 s (16 times). jdcal has no C extension, so
CPython runs it in the interpreter; programs that need speed under CPython use ERFA's C
functions (`eraCal2jd` and `eraJd2cal`, through pyerfa or astropy), which this does not
compare.
