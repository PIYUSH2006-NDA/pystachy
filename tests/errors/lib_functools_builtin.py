# error: lru_cache() of a <built-in function len> is not supported: it caches a def's results
from functools import lru_cache

size = lru_cache(maxsize=2)(len)
print(size("abc"))
