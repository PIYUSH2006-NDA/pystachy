# error: lib_datetime_hash.py:6: error: unsupported call hash(datetime.date)
# hash() of objects is not supported, so dates, times and timedeltas cannot be hashed (nor be
# dict keys or set elements).
from datetime import date

print(hash(date(2024, 2, 29)))
