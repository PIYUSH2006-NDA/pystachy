"""sys.float_info's attributes read in an imported module, which also binds float_info itself."""
import math
import sys
from sys import float_info as fi

TINY = math.sqrt(sys.float_info.min)


class Tol:
    tol0: float = fi.epsilon
    maxit2: int = 20 + sys.float_info.mant_dig + 10

    def scaled(self, k: int = sys.float_info.radix) -> float:
        return self.tol0 * k
