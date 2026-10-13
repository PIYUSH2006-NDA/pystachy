# error: lru_cache() of a lambda is not supported: Pystachy types the cache's keys with the parameters' annotations, which a lambda's cannot have
from functools import cache

sq = cache(lambda x: x * x)
print(sq(3))
