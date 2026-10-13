# Memoized dynamic programming, the way functools.cache is meant for: the fewest scalar
# multiplications that multiply a chain of matrices (CLRS 15.2), top down. Each call of cost() is
# keyed by its two ints; a miss loops over every split of its chain, and nearly every call it
# makes there is a hit
from functools import cache

N = 220
DIMS: list[int] = []
seed = 20261013
for i in range(N + 1):
    seed = (seed * 1103515245 + 12345) % 2147483648
    DIMS.append(5 + (seed >> 8) % 96)


@cache
def cost(i: int, j: int) -> int:
    # the fewest scalar multiplications that multiply matrices i..j, matrix k being DIMS[k] x DIMS[k + 1]
    if i == j:
        return 0
    best = -1
    for k in range(i, j):
        c = cost(i, k) + cost(k + 1, j) + DIMS[i] * DIMS[k + 1] * DIMS[j + 1]
        if best < 0 or c < best:
            best = c
    return best


print(cost(0, N - 1))
print(cost.cache_info())
