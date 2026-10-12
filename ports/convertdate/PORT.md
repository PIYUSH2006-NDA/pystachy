# convertdate 2.5.1, ported to Pystachy

[convertdate](https://pypi.org/project/convertdate/) converts dates between the Gregorian
calendar and others: the Julian, Hebrew, Islamic (arithmetical), Coptic, Indian civil,
Armenian, Positivist and Mayan (long count, haab and tzolk'in) calendars, ISO weeks, ordinal
dates and Julian day counts, and also the Persian, French Republican and Bahá'í calendars, which
it computes from equinoxes and sunsets with PyMeeus. Its `holidays` module gives US, Jewish,
Islamic and Mexican holidays and Easter in three churches. Most of its code comes from John
Walker's Fourmilab calendar converter, in float arithmetic over Julian day counts. It is rank
2,120 on PyPI in October 2026. workalendar (rank 4,079) requires it and computes its Islamic
holidays with `convertdate.islamic`; holidays (rank 637), the holiday library Prophet uses,
required it up to 0.23 (April 2023); dateparser (rank 504) uses it in its `calendars` extra, for
Jalali dates (`convertdate.persian`, which this port leaves out). The port is the package
`src/convertdate` of the sdist `convertdate-2.5.1.tar.gz` (SHA-256
`8ade438cced7eae579e622f3f54354e52609840f597f7b09a16d7789a15d4e0a`), MIT licensed (`LICENSE`,
the sdist's).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `f74977814036547b4971fb513771e96c0a10e3900d311e5972bcdac3d0a4d851` | 6 (8 lines) |
| `armenian.py` | `9656af80fa6147c8d1c185ce2aeed353ba19da75c3ddb324a34b58f034ffb9f6` | 2 |
| `coptic.py` | `708c59f6ded28f4203e13c673ab9eede2f37df8370c3133e05f3a2b7d27443a2` | none |
| `daycount.py` | `4a27c7e2fd2c0a95187364fd3b535ea622d1671bee08da55fbfbf7a3d1880b32` | none |
| `gregorian.py` | `5d64d4f49fc4136226de04f6e743989aaaad05d86ba90fb7a7d8d16417a343f4` | 3 |
| `hebrew.py` | `bb313d4fc99844a0dd86d4330cb155d59a606ca012acb4a1d02ef53047d7b3b9` | 7 |
| `holidays.py` | `a41e4a1e52bf094413fb3a95ff391be715a9a2c2bb6276ff97303aa357ec4e93` | 3 |
| `indian_civil.py` | `a552ddac630ff4414d1251c8e1b4b5dee1ac445bff6c50f28dea9da7f344d16e` | 2 |
| `islamic.py` | `07ed8f5cebab7eda274153f28f32fc572469444fcf71e28f2d4ef41303813871` | 1 |
| `iso.py` | `e0275328f1b3c3f59236b28d17cfc18a8336d2c0aff117bfbde1384d50c3ac9c` | 2 |
| `julian.py` | `7d80a2e7d892d2227f19b525e925c639b35eb0cefffdc411c667b9a38c2f1897` | 3 |
| `julianday.py` | `46eb3e618a0e5932acfe32b3861a95f9c354c19e9bd85d49943ae1c9902bbd0a` | 1 |
| `mayan.py` | `c27e20a1352832aec78172fb2d8b1c10b7be6e65868ddc6c70a9f9f97654e02d` | 1 |
| `ordinal.py` | `3d0edd000322c4bd5dea6227b51f7618955352117eb2fe047ca63914bd558008` | 1 |
| `positivist.py` | `60c3c533530bb29fcad3b7d0714bc06f5385fef59e342db0fb0eeadeb5c0fc1d` | 3 |
| `utils.py` | `c6bc8f4df101e7866a6b4dec242357c89e866e1ea7e5017243a3343791926c68` | 5 |
| `data/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) | none |
| `data/positivist.py` | `1008b71b7ce4d8f910dbb5ac075a100d6f7f9ff145a0b41496c49a1a8fb87df2` | none |
| `_calendar.py` | not convertdate's: the stand-in for `calendar` below | |

That is 40 edits in 14 files, most of them one line; every edit is marked `# Pystachy port:` in
the source, and `diff -ru convertdate-2.5.1/src/convertdate ports/convertdate` shows them all.
The package leaves out `bahai.py`, `french_republican.py`, `persian.py` and `dublin.py` (below)
and `data/french_republican_days.py`, which only `french_republican` reads; the rest of the
sdist is the tests (pytest), the README and the packaging.

## The edits, and the feature each one stands in for

**Native standard-library hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11)), 12
edits.** convertdate imports `calendar`, `datetime` and `itertools`, which Pystachy cannot
import yet: CPython's `calendar.py` imports `datetime`, `enum` (which needs `_weakref`), `locale`
and `itertools`.

1. `calendar`: the 7 modules that import it import `_calendar.py` instead (`from calendar import
   isleap` becomes `from ._calendar import isleap`, and `import calendar` in `utils` and
   `holidays` becomes `from . import _calendar as calendar`). `_calendar.py` lives in the
   package, so that it shadows nothing for other programs (a `calendar.py` on the path would,
   under CPython too). It holds CPython 3.13.16's `isleap`, `monthrange`, `_validate_month`,
   `mdays`, `weekday` and `IllegalMonthError` from `Lib/calendar.py`, and the proleptic
   Gregorian ordinal from `Lib/_pydatetime.py` (`_ymd2ord` and its helpers), with three
   changes:
   - `weekday()` counts the days with `_ymd2ord` instead of building a `datetime.date`, and
     returns an `int` where CPython returns a `calendar.Day`, an `IntEnum` equal to it;
     convertdate only computes with it (`weekday == SAT`, `(weekday - firstday) % 7`). It first
     checks its arguments as `datetime.date()` does, with the messages of CPython's C
     `_datetime`, so that a float year raises `TypeError: 'float' object cannot be interpreted
     as an integer` as in CPython: `holidays.thanksgiving(2024.0)`, `holidays.new_years(2023.0,
     True)`, `utils.nth_day_of_month(1, 0, 2, 2024.0)` and `gregorian.month_length(2024.0, 2)`
     (without the checks, they returned dates such as `(2024.0, 11, 28.0)`). Its result is
     annotated `-> int`, as a call with a float year always raises.
   - `FEBRUARY` is 2 instead of `calendar.Month.FEBRUARY`, an `IntEnum` equal to 2.
   - `IllegalMonthError` derives from `IndexError` alone. CPython 3.13's derives from
     `ValueError` and `IndexError`, and an exception class takes one base until M2
     ([#7](https://github.com/den-run-ai/pystachy/issues/7)). `except IndexError` and `except
     LookupError` catch a bad month as in CPython; `except ValueError` does not (below).
2. `datetime`: the 4 imports are commented out. Only the functions the port leaves out use
   them: `gregorian.format()` and `julian.format()` (`date.strftime`), `iso.from_gregorian()`
   (`date.isocalendar()`) and `julianday.to_datetime()`/`from_datetime()`.
3. `itertools`: `mayan`'s import is commented out; only `tzolkin_generator()`, a generator
   (M7), uses it.

**M1, cheap refinements ([#6](https://github.com/den-run-ai/pystachy/issues/6)), 2 edits.**
`hebrew` imports `warnings` for the `DeprecationWarning` that the deprecated `month_days()`
issues; the import and the `warnings.warn(...)` call are commented out. A `lib/warnings.py`
with `warn()` is item 6 of #6. A stand-in module would not do yet: passing
`DeprecationWarning` to it is rejected ("the builtin 'DeprecationWarning' cannot be used as a
value", M2). Called from a program's `__main__`, CPython prints `DeprecationWarning:
month_days is deprecated, please use month_length` to stderr (its default filters show the
warnings that `__main__` causes) and the port prints nothing; called from convertdate's own
`to_jd()` and `monthcalendar()`, CPython ignores the warning too.

**M3, functions as values ([#8](https://github.com/den-run-ai/pystachy/issues/8)), 2 edits.**
`holidays.easter()` calls `julian.to_gregorian(*_easter_julian(year))` for the orthodox and the
eastern church; the port unpacks the tuple into `jy, jm, jd` first. Star arguments in calls are
#8's `f(*args)`.

**M4, dynamic values ([#9](https://github.com/den-run-ai/pystachy/issues/9)), 9 edits.** Each
one is a variable or a list that holds values of two types in CPython, where Pystachy gives it
one type.

1. `armenian.from_jd()`, Sarkawag's method: `yeardays = 366 if years % 4 == 0 else 365`
   becomes `float(...)`, as `yeardays` is a float (the day count `dc` less ints) on the line
   before. It is used only through `trunc()` and subtractions, and `from_jd()` returns ints,
   so its results are unchanged.
2. `positivist.from_jd()`: `yearday = 365` becomes `365.0`, the type of the `else` branch's
   float; its results are ints, unchanged.
3. `utils.n_weeks()`: upstream binds `j = 7 * nthweek`, an int, and then adds the weekday
   (`j += previous_weekday(weekday, jd)`), which makes it a float when `jd` is a float. The port
   binds `j` once in each branch, `j = 7 * nthweek + previous_weekday(weekday, jd)`, so it has
   the value and the type CPython gives it: an int for an int `jd` (`n_weeks(0, 2460000, 1)` is
   `2460003`), a float for a float one. (The evaluation's first port wrote `float(7 *
   nthweek)`, which made it a float for an int `jd` too: the verifier caught it.)
4. `utils.monthcalendarhelper()`: `[None] * lpad + list(range(1, 1 + month_length)) + 7 *
   [None]` adds a list of ints to a list of `None`, which Pystachy rejects, as a list holds items
   of one type (annotating `days: list[int | None]` does not help: `list[int | None] +
   list[int]` is rejected too). The port builds the same list with one comprehension, `[d if 0 <
   d <= month_length else None for d in range(1 - lpad, 8 + month_length)]`: `lpad` times
   `None`, the days, and 7 times `None`.
5. `hebrew.to_jd_gregorianyear()`: `jd` is a float, then `None` (`jd = None` in the loop), so
   the port declares `jd: float | None = None` before the loop.
6. to 9. `julian.from_jd()`, `hebrew.from_jd()`, `islamic.from_jd()` and
   `indian_civil.from_jd()` rebind their parameter to a float (`jd += 0.5`, `jd = floor(jd) +
   0.5`), and a parameter keeps the type of its argument: an int Julian day, which upstream's
   own tests pass (`range(113957, 1574957, 365)`, `range(2159677, 2488395, 2000)`), was rejected
   (`expected int, got float`), and with it `julianday.to_julian()` of an int. `julian` takes
   `floor(jd + 0.5)` at once; the other three name the float `wjd` (the name
   `gregorian.from_jd()` gives it), 3 to 6 lines each. The values and their types are
   unchanged, for an int and a float Julian day.

**M7, the long tail ([#12](https://github.com/den-run-ai/pystachy/issues/12)), 6 edits.** The
error messages built with `str.format()` become f-strings, with the same text (both call
`format(x, "")`): `gregorian.legal_date()`, `julian.legal_date()`, `armenian._valid_date()`,
`positivist.legal_date()` and two in `utils.nth_day_of_month()`.

**Return types (no roadmap item: the compiler asks for them), 3 edits.** `hebrew.year_days()`
gets `-> float`, `month_days()` `-> int` and `to_jd()` `-> float`. Pystachy infers the result of
an unannotated function from its return statements, compiling it for the argument types of each
call, and these three call one another (`to_jd -> month_days -> month_length -> year_days ->
to_jd`) before any of their return statements gives the result a type. Whichever is compiled
first is rejected (`cannot infer what year_days() returns: it calls itself before a return
statement does; annotate its return type`); `month_length()` needs no annotation, as its
`return 29` comes first. The evaluation's first port annotated only `to_jd()`, which compiles a
program that calls `to_jd()`, `from_jd()` or a conversion first, but not one that calls
`year_days()` or `month_days()` first; the verifier found that, and with the three annotations,
each of them compiles when it is the first one called. The types are what CPython returns
(`year_days(5784)` is `383.0`).

**Modules left out of `__init__.py`, 6 edits (8 lines).** `bahai`, `french_republican` and
`persian` import [PyMeeus](https://pypi.org/project/PyMeeus/), an astronomy library under the
LGPL-3.0, whose classes take `*args, **kwargs` (M2, M3) and which imports `calendar` and
`datetime` (#11); it is not ported. `dublin` makes the bound methods of a `DayCount` object its
functions (`to_gregorian = _dublin.to_gregorian`): unannotated methods (M2,
[#7](https://github.com/den-run-ai/pystachy/issues/7)) and methods as values (M3,
[#8](https://github.com/den-run-ai/pystachy/issues/8)). The four are commented out of the
package's `from . import (...)`, and out of its `__all__`: `from convertdate import *` takes
the names it lists, and stopped at `bahai` with an `AttributeError`.

## What compiles as it is

`coptic.py`, `daycount.py` and `data/` are unmodified, and the rest compiles
around the edits: unannotated functions everywhere, each a template compiled for the types of
each call (a Julian day count may be an `int` or a `float`); `math.floor`, `ceil` and `trunc`
returning ints; ints and floats mixed in arithmetic and compared; tuples of three ints as
results, and their unpacking; `x in (4, 6, 9, 11)` and `x in [1940, 1941]`; the `None`
defaults `church=None`, `observed=None`, `eve=None` and `method=None`, with `church = church or
"western"`; `assert` with a message inside `try`/`except AssertionError`, and `raise ValueError
from err`; `raise IndexError(...)`, `raise NotImplementedError(...)` and `raise
DeprecationWarning(...)` (`holidays.columbus_day()`); module-level lists and tuples of
non-ASCII names (Hebrew, Armenian, transliterated Arabic); a dict with tuple keys whose `get()`
gives a `str` or `None` (`positivist.festival()`); `from . import (...)` of the 15 submodules
and `from .data import positivist as data`; and `holidays.py`'s `Holidays` class, `import time`
and `__main__` block, which nothing the port runs uses.

## What the port leaves out

Each of these is rejected at compile time in a program that calls it; the rest of the package
compiles and runs as under CPython.

- `bahai`, `french_republican`, `persian` and `dublin` (above). `daycount` imports, but
  creating a `DayCount` is rejected: its methods are unannotated (M2,
  [#7](https://github.com/den-run-ai/pystachy/issues/7)).
- Every calendar's `format()` and `armenian.tostring()`: `gregorian` and `julian` format with
  `date.strftime()` ([#11](https://github.com/den-run-ai/pystachy/issues/11)), the others with
  `str.format()` (M7, [#12](https://github.com/den-run-ai/pystachy/issues/12)).
- `iso.from_gregorian()` and `iso.from_jd()` (`date.isocalendar()`, #11; `from_jd()` also passes
  star arguments, M3), and `julianday.to_datetime()` and `from_datetime()` (#11).
- In `mayan`: `lc_to_haab_tzolkin()` (`str.format()` of star arguments), `translate_haab()` and
  `translate_tzolkin()` (`dict()` of a list of pairs, which `docs/language.md` lists among the
  builtins not supported), `next_haab()`, `next_tzolkin()` and `next_tzolkin_haab()` (sets and
  star arguments, M7 and M3, and `str.format()` in an error message), and the generators
  `tzolkin_generator()`, `longcount_generator()`, `haab_monthcalendar()` and
  `haab_monthcalendar_prospective()` (M7; the month calendar also defines a nested function,
  M3).
- `positivist.dayname()`: it indexes tuples (`MONTHS`, `data.DAY_NAMES`) with a variable, item 8
  of M1 ([#6](https://github.com/den-run-ai/pystachy/issues/6)).
- `holidays.Holidays`: `@property` and unannotated methods (M2), and a default year from
  `time.localtime()`, which Pystachy's `time` does not have.
- `eve=True` for `holidays.ramadan()`, `ashura()`, `eid_alfitr()` and `eid_aladha()`: upstream's
  `jd = jd = 1` (meant as `jd - 1`) rebinds the float `jd` to the int 1, which is rejected
  (`expected float, got int`, M4); CPython returns `gregorian.from_jd(1)`, `(-4713, 11, 25)`,
  whatever the year. Without `eve`, the four compile.
- A float where convertdate takes an int, in five places where CPython computes with it, as a
  value would have two types (M4, [#9](https://github.com/den-run-ai/pystachy/issues/9)):
  `holidays.easter(2024.0)` (the western church's date has the float year, the Julian churches'
  ints), a float month in `indian_civil.to_jd()`, `to_gregorian()` and `monthcalendar()`
  (`min(month - 2, 5)` is an int or a float), a float month or day in `positivist.festival()`
  (the dict's keys are pairs of ints), a float `b` in `utils.amod()` (`b if modded == 0 else
  modded`) and a float `n` in `utils.nth_day_of_month()` (`n = 5`). Where CPython raises
  `TypeError` for a float (a float month in `hebrew`, `gregorian.month_length()` or
  `utils.nth_day_of_month()`, or in the arguments of `utils.monthcalendarhelper()`), the port
  rejects it at compile time; a float year, which CPython takes up to `calendar.weekday()`,
  raises the same `TypeError` (above).

Two behaviours differ, because of the edits: `IllegalMonthError` is no `ValueError`, so
`gregorian.month_length(2023, 13)` inside `try`/`except ValueError` stops the program with
`convertdate._calendar.IllegalMonthError: bad month number 13; must be 1-12`, where CPython
catches it. Up to 3.12, CPython's `IllegalMonthError` was a `ValueError` alone (3.13 added
`IndexError`), and the `month_length()` of `hebrew`, `coptic` and `armenian` raise `ValueError`
for a month past their last, so `except ValueError` is the clause a program written for
convertdate is the more likely to have; exception classes of two bases (M2, #7) will give it
both again. And `month_days()` warns no more.

## Deviations it hits

- **`str` is UTF-8 bytes**
  ([docs/language.md](../../docs/language.md#deviations-from-cpython)). `hebrew.MONTHS_HEB`,
  `armenian.MONTHS_ARM`, the transliterated names of `islamic.MONTHS` and the Positivist day
  names are not ASCII. They print as in CPython, but `len(hebrew.MONTHS_HEB[6])` (`תשרי`) is 4
  in CPython and 8 here, `hebrew.MONTHS_HEB[6][:2]` is `תש` in CPython and `ת` here (two bytes),
  and `islamic.MONTHS[8].upper()` is `RAMAḌĀN` in CPython and `RAMAḍāN` here (case mapping knows
  only ASCII). convertdate itself slices only `lang[0:2]`, in the `format()` functions the port
  leaves out.
- **`int` is 64-bit.** Far beyond any calendar, Pystachy raises `OverflowError` where CPython
  computes with big ints: `gregorian.to_jd(3 * 10**16, 1, 1)` is `1.0957275000001722e+19` in
  CPython and `OverflowError: integer result does not fit in 64 bits` here (`365 * (year - 1)`
  passes 2**63 beyond the year 2.5e16), `gregorian.from_jd(1e19)` is `(27379070069880361, 1, 1)`
  in CPython and `OverflowError: float too large for a 64-bit int` here (`floor()` of the day
  count), and `hebrew.to_jd(10**14, 7, 1)` is `3.65246822209454e+16` in CPython and the first
  `OverflowError` here (`13753 * months` in `delay_1()` passes 2**63 beyond the year 5.4e13).
  By then the Julian day, a float, no longer counts whole days (beyond 2**53 days, the year
  2.5e13).

## Tests

`tests/port_convertdate_calendars.py` calls `hebrew.year_days()` before any other function of
`hebrew` (the verifier's case above), then takes 21 Gregorian dates to Julian days and to each
calendar and back: the Gregorian reform (1582-10-04 and 10-15), leap days and century years
(1900, 2000, 2100), the years 1, 0 and -500, Julian day 0 (-4713-11-24), 9999-12-31, the
Islamic, Coptic, Positivist and Mayan epochs and 2012-12-21 (13.0.0.0.0). It round-trips 430
consecutive days from 2023-09-01 (a Hebrew leap year with Adar I and II, the 13th months of the
Coptic and Armenian years, the Indian year's start) through eight calendars, printing the days
that begin a Hebrew, Islamic, Coptic, Indian or Armenian month, and every 997th day from the
year 1 to 2999 through seven, and Armenian (in both methods) and Positivist from their epochs
(0 mismatches). It prints month lengths, leap years and month calendars of seven calendars,
the Mayan haab and tzolk'in, ISO weeks (years of 52 and 53), ordinal dates, `julianday`, the
weekday helpers of `utils` with a float and an int Julian day (the verifier's `n_weeks()` case:
an int stays an int), int Julian days through `julian`, `hebrew`, `islamic` and `indian_civil`
(M4's edits 6 to 9) and `julianday.to_julian()`, and 14 error paths, among them a bad month
caught by `except IndexError` and `except LookupError` (the verifier's `IllegalMonthError` case).

`tests/port_convertdate_holidays.py` prints every holiday function for 10 years (1939 to 1941,
when US Thanksgiving moved, and 7 years from 1999 to 2100), with `observed=True`, `eve=True` and
the Canadian and Mexican variants; Easter in the three churches every third year from 1 to 2998;
observed holidays of years outside 1..9999, which `calendar.weekday` counts modulo 400;
`utils.nth_day_of_month()` with the last weekday (`n=0`) and 7 calls that raise `IndexError`;
a float year, which `new_years(2023.0)` keeps and with which `new_years(2023.0, True)`,
`thanksgiving(2024.0)`, `utils.nth_day_of_month()` and `gregorian.month_length()` raise
`TypeError` from `calendar.weekday()`; and the `ValueError`, `NotImplementedError` and
`DeprecationWarning` that `easter()`, `thanksgiving()` and `columbus_day()` raise.

`tests/port_convertdate_star.py` takes the package's modules with `from convertdate import *`
and calls a conversion of each calendar; the import stopped at `bahai` while `__all__` named
the four modules the port leaves out.

`tests/run.sh` compares what they print with CPython's, JIT and AOT. Run under CPython against
the unmodified upstream package (with PyMeeus 0.5.12 on the path, as its `__init__.py` imports
`bahai`, `french_republican` and `persian`, which the tests do not call), the first two print
exactly what they print against this port. Both are small: under `make verify`'s gc-stress stage
(the compiler collecting every 1,000 allocations, the program at every allocation), each takes 3
to 6 s for the JIT run and the AOT build and run together, and each AOT build 2 to 4 s.

## Speed

The headline workload: 73,000 consecutive days from 1900-01-01, each taken from its Julian day
to the Gregorian, Hebrew, Islamic, Julian, Coptic and Indian civil calendars, and back to a
Julian day from the Hebrew and the Islamic date (0 mismatches, and the same output in both).
Wall clock with process start-up, and the CPU time (user + system), median of 3 runs, on a
4-core x86-64 VM that was running other jobs (a load average of 4 to 5):

| | wall clock | CPU time |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.211 s | 0.210 s |
| CPython 3.13.16, unmodified convertdate 2.5.1 | 5.241 s | 5.200 s |

That is 24.8 times faster (24.8 in CPU time). Two more sets of runs, at load averages of 3 to 4,
gave 0.220 s and 5.176 s (23.5 times) and 0.213 s and 5.089 s (23.9 times); runs of the port
before M4's edits 6 to 9, at load averages of 4 to 9, gave 24 to 27 times, and the evaluation of
the port, on the same VM two days before, 0.212 s and 4.940 s (23 times).
convertdate has no C extension, so CPython runs it in the interpreter; about 0.1 s of CPython's
time is the import of convertdate and PyMeeus.
