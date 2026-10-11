# jdcal at the edges of its arithmetic: Julian dates far from the epoch, years of 10**12 and
# 2**52, -0.0, NaN and infinity (which reach int() as NaN), int arguments where floats are
# expected, and is_leap on negative and huge years
from jdcal import gcal2jd
from jdcal import ipart
from jdcal import is_leap
from jdcal import jcal2jd
from jdcal import jd2gcal
from jdcal import jd2jcal

# extreme but representable Julian dates: the year stays inside 64 bits up to about 3e18 days
for a, b in [(1e15, 0.5), (-1e15, -0.25), (5e15, 1e-9), (2400000.5, -0.5), (-0.0, -0.0),
             (0.49999999999, 0.0), (2451544.5, 0.4999999999999999), (-2400000.5, 2400000.5),
             (2451545.0, 1e-300), (1e18, 0.0)]:
    print(a, b, jd2gcal(a, b), jd2jcal(a, b))

# large years: gcal2jd computes in floats, jcal2jd from 367 * year (an int; PORT.md)
for y in [10**9, -10**9, 10**12, 2**52, -2**52, 25 * 10**15]:
    print(y, gcal2jd(y, 6, 30), jcal2jd(y, 6, 30))

# int arguments: math.modf takes them as CPython's does
print(jd2gcal(2400000, 51544), jd2jcal(2400000, 51544), jd2gcal(0, -1))

# NaN and infinity: the arithmetic turns both into NaN, and int() raises
for v in [float("nan"), float("inf"), -float("inf")]:
    try:
        print(jd2gcal(v, 0.0))
    except ValueError as e:
        print("jd2gcal:", repr(v), "ValueError:", e)
    try:
        print(jd2jcal(0.0, v))
    except ValueError as e:
        print("jd2jcal:", repr(v), "ValueError:", e)

# is_leap on negative and huge years, and on floats; ipart of their thirds
for y in [-400, -100, -4, -1, 0, 4, 100, 400, 2**53, 2**62, -2**62]:
    print(y, bool(is_leap(y)), ipart(y / 3.0))
print(bool(is_leap(2000.0)), bool(is_leap(1900.0)), bool(is_leap(2024.0)), bool(is_leap(2023.5)))
