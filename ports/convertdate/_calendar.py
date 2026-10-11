# Pystachy port: this file is not convertdate's. It stands in for the part of CPython's calendar
# module that convertdate uses (isleap, monthrange, weekday), as Pystachy cannot import
# CPython's calendar.py yet: it imports datetime, enum, locale and itertools (native stdlib hubs,
# #11). The code is CPython 3.13.16's, from Lib/calendar.py and Lib/_pydatetime.py, with these
# changes:
# - IllegalMonthError derives from IndexError alone, where CPython 3.13's derives from ValueError
#   and IndexError: an exception class takes one base until M2 (#7). So except IndexError and
#   except LookupError catch a bad month as in CPython, and except ValueError does not. IndexError
#   is what utils.nth_day_of_month raises for its other bad arguments. Its methods are annotated.
# - FEBRUARY is 2, not calendar.Month.FEBRUARY, an IntEnum equal to 2.
# - weekday() counts the days with _pydatetime's _ymd2ord (below) instead of building a
#   datetime.date (#11), and returns an int where CPython returns a calendar.Day, an IntEnum equal
#   to it (convertdate only computes with it).

# Lib/calendar.py

class IllegalMonthError(IndexError):
    def __init__(self, month: int) -> None:
        self.month = month
    def __str__(self) -> str:
        return "bad month number %r; must be 1-12" % self.month


FEBRUARY = 2

# Number of days per month (except for February in leap years)
mdays = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def isleap(year):
    """Return True for leap years, False for non-leap years."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def weekday(year, month, day):
    """Return weekday (0-6 ~ Mon-Sun) for year, month (1-12), day (1-31)."""
    if not MINYEAR <= year <= MAXYEAR:
        year = 2000 + year % 400
    return (_ymd2ord(year, month, day) + 6) % 7


def _validate_month(month):
    if not 1 <= month <= 12:
        raise IllegalMonthError(month)

def monthrange(year, month):
    """Return weekday of first day of month (0-6 ~ Mon-Sun)
       and number of days (28-31) for year, month."""
    _validate_month(month)
    day1 = weekday(year, month, 1)
    ndays = mdays[month] + (month == FEBRUARY and isleap(year))
    return day1, ndays


# Lib/_pydatetime.py

MINYEAR = 1
MAXYEAR = 9999

# -1 is a placeholder for indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

_DAYS_BEFORE_MONTH = [-1]  # -1 is a placeholder for indexing purposes.
dbm = 0
for dim in _DAYS_IN_MONTH[1:]:
    _DAYS_BEFORE_MONTH.append(dbm)
    dbm += dim
del dbm, dim

def _is_leap(year):
    "year -> 1 if leap year, else 0."
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def _days_before_year(year):
    "year -> number of days before January 1st of year."
    y = year - 1
    return y*365 + y//4 - y//100 + y//400

def _days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]

def _days_before_month(year, month):
    "year, month -> number of days in year preceding first day of month."
    assert 1 <= month <= 12, 'month must be in 1..12'
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))

def _ymd2ord(year, month, day):
    "year, month, day -> ordinal, considering 01-Jan-0001 as day 1."
    assert 1 <= month <= 12, 'month must be in 1..12'
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, ('day must be in 1..%d' % dim)
    return (_days_before_year(year) +
            _days_before_month(year, month) +
            day)
