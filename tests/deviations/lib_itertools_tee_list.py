# itertools.tee(iterable, n) gives a list of the n iterators, where CPython gives a tuple: the
# length of a tuple is its type's here, and n is known only as the program runs
# (lib/compatibility.md). tee(iterable) gives a tuple of two, as in CPython; unpacking, indexing,
# len() and loops see the same iterators.
from itertools import tee

print(tee("abc", 0))
its = tee("abc", 3)
print(type(its).__name__, len(its), [list(t) for t in its])
a, b = tee("xy", 2)
print(list(a), list(b))
c, d = tee("xy")
print(list(c), list(d))
