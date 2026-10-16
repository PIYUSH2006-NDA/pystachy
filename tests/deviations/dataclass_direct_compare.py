# Documented deviation: a comparison method that @dataclass writes, called directly with None
# or an object of another class, compares or raises TypeError where CPython's returns
# NotImplemented (the operators decline it as CPython does). CPython prints
# NotImplemented NotImplemented
# NotImplemented
# False False
from dataclasses import dataclass


@dataclass(order=True)
class P:
    x: int


@dataclass
class D(P):
    pass


print(P(1).__eq__(D(1)), P(1).__eq__(None))
try:
    print(P(1).__lt__(None))
except TypeError as e:
    print("TypeError", e)
print(P(1) == D(1), P(1) == None)  # noqa: E711
