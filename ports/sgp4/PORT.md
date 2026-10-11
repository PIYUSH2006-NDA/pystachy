# sgp4 2.27, ported to Pystachy

[sgp4](https://pypi.org/project/sgp4/) computes where an Earth satellite is and how fast it moves
from a two-line element set (TLE), the format in which NORAD and CelesTrak publish the orbits of
tracked objects. It propagates the orbit with SGP4, and with SDP4's deep-space terms for orbits
of 225 minutes or more (resonant 12-hour and 24-hour orbits among them), to a position and a
velocity in the TEME frame. It is Brandon Rhodes's translation of David Vallado's C++ code, and
the propagator under Skyfield's `EarthSatellite` (Skyfield is rank 5,395 on PyPI). sgp4 is rank
4,439 on PyPI in October 2026. Its wheels carry Vallado's C++ code itself, as the extension
`sgp4.vallado_cpp`; where that extension is missing (it is optional when the sdist is
installed), `sgp4.api` falls back to the pure-Python modules ported here, and
`sgp4.api.accelerated` is `False`. The port is these modules of the sdist `sgp4-2.27.tar.gz`
(SHA-256 `06d37247c6985739b707b8b39b6b83e06e8af783b2531e31965501ba983985f9`), MIT licensed
(`LICENSE`).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `8f01018363382658c82ae05408e8fb00e077c02be3b6a857478205f887da6b0e` | none |
| `alpha5.py` | `98b6a004d971f25f837a0efa1f073e6bc6a36314fd1448b3078473db9ab4267a` | none |
| `api.py` | `e61f7a4b1ddd026a0cfd147ef18cf2eaf1aee9e05eae9098677cbd811f519bf3` | none |
| `earth_gravity.py` | `70057a3a1ed33c96b8c191c28c4012b4d2fdbd55b5775ec9bdaaabf78f418879` | 2 |
| `ext.py` | `31240fe331e03d3427adf8afc113838a6a09ab769d5c484b8c13c7cbf1fc6287` | 2 |
| `functions.py` | `8947e790097ae705f35244a3233a8b0ec61b214873618a241488686993b79e40` | 1 |
| `io.py` | `8adb8030c909d0bce36c2ea22dd96fbe8eaff19415afb3da22872df62ff8302e` | 7 |
| `model.py` | `8725b573ea25f33497022dcab447a139d3ee3eb71e0894da52658877ce6cc324` | 10 |
| `propagation.py` | `fa851ca7d8710eb54d684de61bc84cc8a3687241518e4ee4cfe8249e0fb33a92` | 6 |

The other modules of the sdist are left out (below). The table counts the edits listed below
once for each file they change, and each message of edits 17 and 18. Every edit is marked
`# Pystachy port:` in the source, on each region it changes (38 places), and `diff -ru` against
the sdist's `sgp4/` shows them all. The largest is one block of 125 annotated fields; the 2,069
lines of SGP4 and SDP4 in `propagation.py` need 6 edits of a line or two each.

## The edits, and the feature each one stands in for

**M1, tuples indexed by a variable ([#6](https://github.com/den-run-ai/pystachy/issues/6), item
8).** A tuple index must be an integer constant (`tuple index must be an integer constant`).

1. `model.py`: `gravity_constants = wgs72old, wgs72, wgs84` is a list, which
   `Satrec.twoline2rv()` and `Satrec.sgp4init()` index with `whichconst` (`WGS72OLD`, `WGS72` or
   `WGS84`, the ints 0 to 2).
2. `ext.py`, `rv2coe()`: `for i in range(0, 3): ebar[i] = (c1*r[i] - rdotv*v[i])/mu` is unrolled
   into three lines, as `r` and `v` are the tuples that `sgp4()` returns.

**M2, full classes ([#7](https://github.com/den-run-ai/pystachy/issues/7)).**

3. `model.py`: `Satrec.__slots__`, a tuple of 126 names (`cannot infer the type of class
   attribute '__slots__'`), becomes 125 annotated fields, one per slot but `epoch` (edit 21):
   6 `str`, 7 `int`, `error_message: str | None` and 111 `float`. Pystachy types a field from the
   class body or `__init__`, and Satrec's `__init__` only sets `revnum`: the module functions
   `io.twoline2rv()` and `propagation.sgp4init()` assign the others, through their `satrec`
   parameter.
4. `model.py`: the class attribute `array = None` is left out (`cannot infer the type of class
   attribute 'array'`). Only `sgp4_array()` uses it, to keep NumPy's `array` once imported.
5. `model.py`: the properties `no` and `satnum` are left out (`method no() has a decorator`):
   `sat.no` is `sat.no_kozai`, and `sat.satnum` is `from_alpha5(sat.satnum_str)`.
6. `model.py`: so are the legacy class `Satellite`'s copies of them, `no = Satrec.no` and
   `satnum = Satrec.satnum`, a class body that reads another class's attributes.
7. `model.py`: the parameters of `twoline2rv()`, `sgp4init()`, `sgp4()` and `sgp4_tsince()` are
   annotated (`parameter 'line1' of method twoline2rv() has no type annotation`), and the results
   of `twoline2rv()` (`'Satrec'`), `sgp4()` and `sgp4_tsince()` (`tuple[int, tuple[float, float,
   float], tuple[float, float, float]]`): a method without a return annotation returns `None`.
8. `model.py`: `sgp4_array()`, which takes NumPy arrays and builds its results with
   `numpy.array`, is commented out: unannotated, it makes the class unsupported (edit 7), and
   annotated, it would be compiled, with its `from numpy import array` and `self.array`.

**M3, star arguments ([#8](https://github.com/den-run-ai/pystachy/issues/8)).**

9. `earth_gravity.py`: `EarthGravity(*getgravconst('wgs72'))`, for each of the three models,
   passes the eight items one by one from `_g = getgravconst('wgs72')`.

**M4, dynamic values ([#9](https://github.com/den-run-ai/pystachy/issues/9)).** Each is a
variable, a field or a list that holds values of two types in CPython.

10. `model.py`: `whichconst = gravity_constants[whichconst]` rebinds an int to an `EarthGravity`,
    in `twoline2rv()` and `sgp4init()`: the port names the model `gravity`.
11. `io.py` and `model.py`: `io.twoline2rv()` stores the TLE's text, `line[62]` and `line[63:68]`,
    in `satrec.ephtype` and `satrec.revnum`, and `Satrec.twoline2rv()` converts both to ints as
    soon as it returns. The port keeps the text in two locals and makes the same conversions,
    with the same expressions, at the end of `io.twoline2rv()`: after `sgp4init()`, as upstream,
    so that a field that is not a number raises the same `ValueError` at the same point.
12. `io.py`: the legacy default `if satrec is None: satrec = Satellite()` is left out: `satrec`
    would be a `Satrec` or a `Satellite`, whose unannotated `propagate()` does not compile (M2).
    `Satrec.twoline2rv()` always passes its `Satrec`.
13. `functions.py`, `days2mdhms()`: the float `minute` of `divmod(second, 60.0)` is named
    `minute_f`, as `minute = int(minute)` rebinds it to an int.
14. `propagation.py`, `sgp4init()`: `if isinstance(satn, int): satn = to_alpha5(satn)` becomes
    `satn_str = to_alpha5(satn) if isinstance(satn, int) else satn` (an int from
    `Satrec.sgp4init()`, a str from `io.twoline2rv()`).
15. `ext.py`, `rv2coe()`: `hbar`, `nbar` and `ebar` start as `[0.0, 0.0, 0.0]`, not
    `[None, None, None]` (`cannot infer the type of a list of None`); `cross()` and the code
    below fill them before any read. `typeorbit = [None, None, None]`, which the code rebinds to
    a str before reading it, is not bound.

**M7, `bytes` and `str.format` ([#12](https://github.com/den-run-ai/pystachy/issues/12)).**

16. `io.py`: `longstr1.encode('ascii')` and `longstr2.encode('ascii')` in a `try` that catches
    `UnicodeEncodeError` (`'str' has no method 'encode'`) become
    `if not (longstr1.isascii() and longstr2.isascii()):`.
17. `io.py`: `error_message.format(1, LINE1, line)`, and the same for line 2, is
    `error_message.replace('{0}', '1').replace('{1}', LINE1).replace('{2}', line)`. It is the
    same text, also for a line with braces: each `replace()` scans only the template, as the
    line goes in last.
18. `propagation.py`: the 5 messages of `sgp4()`'s errors, `'mean motion {0:f} is less than
    zero'.format(nm)` and the like, are f-strings with the same format spec,
    `f'mean motion {nm:f} is less than zero'`.

**Native standard-library hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11)).**
`collections`, `re` and `datetime` are not Pystachy modules.

19. `earth_gravity.py`: `EarthGravity = namedtuple('EarthGravity', 'tumin mu radiusearthkm xke
    j2 j3 j4 j3oj2')` is the same tuple as a `typing.NamedTuple` class with eight float fields
    (the same fields, indexing and `repr()`).
20. `io.py`: `import re` is commented out with the two regular expressions it compiles,
    `INT_RE` and `FLOAT_RE`, which nothing uses.
21. `io.py` and `model.py`: `from datetime import datetime` is commented out with the block of
    `io.twoline2rv()` that sets the legacy `satrec.epoch` to a `datetime`, and so is
    `Satrec.twoline2rv()`'s `del self.epoch`, which deletes it as soon as `io.twoline2rv()`
    returns: a `Satrec` never has it, upstream or here. The block catches the `ValueError` of
    a date such as day 366 of a common year and tries again with `invjday()`'s date, which
    raised for none of 1.2 million epochs that a TLE can give (every two-digit year, days 0 to
    999.99999999), so leaving it out changes nothing else.

## What compiles as it is

- `api.py`, with its accelerator `try`: Pystachy does not find `sgp4.vallado_cpp`, which
  `from .wrapper import Satrec, SatrecArray` imports (`wrapper.py` is left out), so it runs the
  `except ImportError:` branch, as CPython does without the extension: `accelerated` is `False`,
  and `Satrec`, `WGS72OLD`, `WGS72` and `WGS84` are `model.py`'s.
- `propagation.py`, but for its 6 edits: its unannotated functions are templates, among them
  `_dscom()`, which takes 38 parameters and returns a tuple of 81 items, `_dsinit()` (72
  parameters, 31 items), `_dspace()`, `_dpper()`, `_initl()`, `sgp4init()` and `sgp4()`; both
  operation modes (`'i'`, improved, and `'a'`, AFSPC); the error results `false = (_nan, _nan,
  _nan)` and `return false, false`; `_gstime = gstime`, an alias of a function; and the fields of
  a `Satrec` read and written through a parameter.
- `alpha5.py` (Alpha-5 satellite numbers: `'%05d'`, `'%c%04d'`, `ord()`, `divmod()`, and
  `n -= c > 'I'`, an int minus a bool), `functions.py` but for edit 13 (`jday()`, and `is_leap`, a
  bool, multiplied in `_day_of_year_to_month_day()`), `ext.py` but for `rv2coe()`'s two edits
  (`invjday()`, `jday()`, `mag()`, `cross()`, `dot()`, `angle()`, `newtonnu()`), and
  `__init__.py`.
- In `io.py` and `model.py`: the fixed-column parsing of a TLE, with CPython's `ValueError`s from
  `int()` and `float()`; `repr()` of lines with non-ASCII characters in the error message;
  `@classmethod` with `cls()`; `divmod()` and `round()` of floats; `%=` on a field.

## What the port leaves out

- The other modules of the sdist: `wrapper.py` (the C++ extension's classes, above),
  `conveniences.py` (`datetime` helpers), `exporter.py` (TLE and OMM export, through
  `conveniences.py`), `omm.py` (`csv`, `xml.etree` and `datetime`), `tests.py` and `wulfgar.py`
  (`unittest`), the C++ sources in `extension/`, and the verification data `SGP4-VER.TLE` and
  `tcppver.out` (the tests embed what they use of them).
- In the ported modules: `Satrec.sgp4_array()` and the class `SatrecArray` (NumPy: `SatrecArray`
  is left as it is, and does not compile); the properties `no` and `satnum`; and sgp4 1.x's API,
  `io.twoline2rv(line1, line2, wgs72)` without a `satrec`, which returns a `Satellite`, and
  `Satellite.propagate()` (the class is left as it is but for edit 6, and does not compile).
- `io.compute_checksum()`, `fix_checksum()` and `verify_checksum()` are left as they are, and do
  not compile: `compute_checksum()` sums ints and bools (`int(c) if c.isdigit() else c == '-'`,
  `expected int, got bool`, M4), and `verify_checksum()` takes `*lines` and calls `str.format()`
  (M7). `twoline2rv()` does not check the checksums.
- `__slots__`'s lock-down: under CPython, the port's `Satrec` takes an attribute that is not one
  of its fields (`sat.no_kozia = 0.06`), where upstream's raises `AttributeError`; Pystachy
  rejects it at compile time (`'sgp4.model.Satrec' object has no attribute 'no_kozia'`).

## Deviations it hits

- **`int` is 64-bit** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  `days2mdhms()` converts the minutes, and `invjday()` the years, from a float to an `int`: far
  enough from any date, Pystachy raises `OverflowError: float too large for a 64-bit int` where
  CPython goes on with a big int. `days2mdhms(2000, 1e16)` is
  `(327868852459017, 12, 0, 0, 0.0)` in CPython, and `invjday(1e22)` is
  `(27378507871321007979, 0, 30, 0, 0, -8.64e-07)`. A TLE's epoch is less than 1,000 days into
  its year; the tests go up to `days2mdhms(2024, 366.99999999999)`, `invjday(1e9)` and times of
  `1e15` minutes and `2**62` days from the epoch (floats, which give error 1 or NaN), and agree
  with CPython there.
- **`str` is UTF-8 bytes** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  `twoline2rv()` rejects a line with any non-ASCII character before it measures or indexes it,
  so it reads the same columns as CPython, and its message, which shows the lines with `repr()`,
  is CPython's (the tests try `é` and a no-break space). Where non-ASCII text does reach the code,
  it differs: `from_alpha5('É0001')` is 1440001 in CPython, whose Alpha-5 decoding takes any
  letter, and Pystachy, whose `s[0]` is the first byte of `É`, raises `ValueError: invalid literal
  for int() with base 10: 'É0001'`. Alpha-5 numbers use only `A` to `Z`.

## Tests

`tests/port_sgp4_verify.py` runs sgp4's official verification as its own test suite does
(`test_satrec_against_tcppver_using_julian_dates` in the sdist's `tests.py`), on 5 of the 33
satellites of `SGP4-VER.TLE`, 16 of the 700 lines that Vallado's C++ SGP4 wrote to
`tcppver.out`, which it embeds, and 2 of the 7 errors that `tests.py` expects: 00005 (SGP4),
08195 (SDP4, a Molniya orbit in 12-hour resonance), 28626 (SDP4, geosynchronous), 28872 (SGP4
with a low perigee, which decays: error 6 at 55 minutes) and 33334 (error 3 at its epoch). It prints each line it computes with
`Satrec.twoline2rv()`, `Satrec.sgp4(jd, fr)`, `invjday()` and `rv2coe()`, and compares it with
the official one as the suite does: positions and velocities to 2e-7, the other fields as text.
`tests/port_sgp4_api.py` runs the cases of an evaluation of the port and of an independent check
of it: the fields of the ISS's TLE, `sgp4(jd, fr)` and `sgp4_tsince()`, the three gravity
models, times far from the epoch (error 1, NaN), a satellite that decays (`SGP4_ERRORS`),
`Satrec.sgp4init()` in both operation modes, Alpha-5 numbers up to 339999 and the
`ValueError` beyond, malformed TLEs with their complete messages (braces in a line, short and
empty lines, mismatched satellite numbers, non-ASCII characters, a revnum or an ephtype that is
not a number), `jday()`, `days2mdhms()` and `invjday()` at the edges, and `rv2coe()` on
degenerate orbits; it ends with a `ValueError` that nothing catches. `tests/run.sh` compares what
they print with CPython's, JIT and AOT. Run under CPython against the unmodified upstream package,
both print exactly what they print against this port.

Outside the tests, the evaluation's program for the whole verification regenerates all 700 lines
of `tcppver.out` from `SGP4-VER.TLE` with this port: 0 mismatches, the errors `[1, 1, 6, 6, 4,
3, 6]` that `tests.py` expects, and the same 700 lines as CPython, JIT and AOT. The tests are
small: under `make verify`'s gc-stress stage (the compiler collecting every 1,000 allocations,
the program at every allocation), each takes 3.7 to 7.2 s for the JIT run and the AOT build and
run together, and its AOT build 2.0 to 3.4 s (2.6 to 4.7 s under gc-stress), on a 4-core VM at a
load of 11 to 18.

## Speed

The headline workload, the evaluation's: the ISS (SGP4) and a Molniya orbit (08195, SDP4)
propagated every second for 3 days with `Satrec.sgp4(jd, fr)`, 518,400 propagations, summing
the positions (the same sum in both). Wall clock with process start-up, and the CPU time (user
+ system), median of 3 runs, on a 4-core x86-64 VM that was running other jobs (a load average
of 10 to 13):

| | wall clock | CPU time |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.533 s | 0.356 s |
| CPython 3.13.16, unmodified sgp4 2.27 (pure Python) | 4.388 s | 3.062 s |

That is 8.2 times faster (8.6 in CPU time); a second set of runs gave 0.489 s and 3.513 s (7.2
times; CPU time 0.355 s and 3.022 s, 8.5 times), and the evaluation of the port, on the same VM
two days before, 0.352 s and 3.033 s (8.6 times). CPython runs sgp4's pure-Python modules here,
as it does where the C++ extension is missing; with the extension of sgp4's wheels
(`accelerated` is `True`), CPython propagates with Vallado's compiled C++ code instead, which
this does not compare.
