# math.gcd() and math.lcm() of other than two arguments take them as CPython does, the first two,
# then that result and the third, ...; ints are 64-bit, so a result or a result on the way that
# does not fit raises OverflowError where CPython returns a big int (docs/language.md)
import math
import sys

lo = -sys.maxsize - 1
print(math.gcd(lo, 6, 4), math.lcm(2 ** 31, 2 ** 31 + 1, 0))
try:
    print(math.gcd(lo))
except OverflowError as e:
    print("OverflowError:", e)
try:
    print(math.gcd(lo, 0, 6))
except OverflowError as e:
    print("OverflowError:", e)
print(math.lcm(2 ** 62, 3, 0))
