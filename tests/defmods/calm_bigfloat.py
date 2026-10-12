# The same for int() of a float (tests/deftime_class_raises.py)
from typing import Iterable


class BigFloat:
    big = int(1e100)
    xs: Iterable[int]
