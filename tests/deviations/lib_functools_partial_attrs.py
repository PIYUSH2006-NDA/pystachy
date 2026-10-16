# Documented deviation: a partial's func, args and keywords are fields that can be assigned,
# where CPython's C partial makes them read-only attributes. CPython prints
# AttributeError: readonly attribute
# 3
from functools import partial


def add(a: int, b: int) -> int:
    return a + b


p = partial(add, 1)
try:
    p.args = (5,)
    print("assigned")
except AttributeError as e:
    print("AttributeError:", e)
print(p(2))
