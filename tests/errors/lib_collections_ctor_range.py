# error: tests/errors/lib_collections_ctor_range.py:4: error: range() is only supported in a for loop, after 'in', or as the argument of list(), tuple(), bytes(), sorted(), sum(), min(), max(), any(), all(), math.fsum(), math.prod() or str.join()
# range is not a first-class compiled iterable; materialize it with list()
from collections import deque
print(deque(range(3)))
