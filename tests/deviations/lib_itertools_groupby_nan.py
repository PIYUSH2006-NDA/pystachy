# A float has no identity here (tests/deviations/container_nan_identity.py): groupby() of the
# same NaN object twice makes a group of each, where CPython finds the object equal to itself
# and makes one group of both; a NaN made anew for each item makes a group of each in both
from itertools import groupby

nan = float("nan")
print([len(list(g)) for k, g in groupby([nan, nan, 1.0])])
print([len(list(g)) for k, g in groupby([1, 2, 3], key=lambda v: nan)])
