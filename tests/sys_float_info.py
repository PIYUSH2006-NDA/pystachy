# sys.float_info's attributes: CPython's on IEEE 754 doubles, read anywhere a value can be
import math
import sys
import sys as s
from sys import float_info
from sys import float_info as fi


class Geodesic:
    maxit2: int = 20 + sys.float_info.mant_dig + 10
    tiny: float = math.sqrt(sys.float_info.min)
    tol0: float = sys.float_info.epsilon


def twice(x: float = sys.float_info.epsilon) -> float:
    return x * 2


EPS = sys.float_info.epsilon
print(sys.float_info.max, sys.float_info.min, sys.float_info.epsilon)
print(sys.float_info.dig, sys.float_info.mant_dig, sys.float_info.radix, sys.float_info.rounds)
print(sys.float_info.max_exp, sys.float_info.min_exp, sys.float_info.max_10_exp, sys.float_info.min_10_exp)
print(s.float_info.max, float_info.epsilon, fi.min, fi.min_10_exp)
print(Geodesic.maxit2, Geodesic.tiny, Geodesic.tol0, twice(), twice(1.0), EPS)
print(-sys.float_info.max, sys.float_info.max * 2, sys.float_info.min / 2, sys.float_info.min * EPS)
print(1.0 + EPS > 1.0, 1.0 + EPS / 2 == 1.0, sys.float_info.max + 1.0 == sys.float_info.max)
print(sys.float_info.max == (2 - EPS) * 2.0 ** (sys.float_info.max_exp - 1))
print(sys.float_info.min == 2.0 ** (sys.float_info.min_exp - 1), EPS == 2.0 ** (1 - sys.float_info.mant_dig))
print(sys.float_info.radix ** sys.float_info.mant_dig, -sys.float_info.min_exp, math.ulp(1.0) == EPS)
print(math.frexp(sys.float_info.max), math.frexp(sys.float_info.min), math.isinf(sys.float_info.max * 10))
print(f"{sys.float_info.max:.3e} {sys.float_info.epsilon!r} {sys.float_info.dig:>4} {sys.float_info.min:g}")
print(repr(sys.float_info.min), str(sys.float_info.mant_dig), sys.float_info.max.is_integer(), sys.float_info.min.is_integer())
x = sys.float_info.max
x += x
n = sys.float_info.dig
n *= 2
print(x, n)
try:
    print(int(sys.float_info.max * 2))
except OverflowError as e:
    print("OverflowError:", e)
try:
    print(math.ldexp(1.0, sys.float_info.max_exp))
except OverflowError as e:
    print("OverflowError:", e)
print(sys.float_info.max ** 2)
