# itertools' iterators are generators here (lib/compatibility.md), so the generator protocol of
# #572 works on them: send(None) steps like next(), close() finishes them and throw() raises in
# them. CPython's iterators are objects of the C types, which have no such methods: each call is
# an AttributeError there.
from itertools import chain, count, islice

c = count()
print(next(c), c.send(None))
g = chain([1, 2], [3])
print(next(g))
g.close()
print(next(g, -1))
it = islice("abc", 2)
try:
    it.throw(KeyError("k"))
except KeyError as e:
    print("KeyError", e)
