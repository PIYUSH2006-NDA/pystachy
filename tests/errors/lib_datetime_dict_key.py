# error: lib_datetime_dict_key.py:5: error: dict keys must be int or str, or tuples of int, bool, str and str | None items, not date
# Objects are not dict keys: key a dict by d.toordinal() or d.isoformat() instead.
from datetime import date

counts = {date(2024, 2, 29): 1}
print(counts)
