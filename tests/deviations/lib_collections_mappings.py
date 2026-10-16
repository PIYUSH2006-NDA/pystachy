# Documented deviations of lib/collections' Counter, defaultdict and OrderedDict (Pystachy's
# own) from CPython's.
from collections import Counter, OrderedDict, defaultdict

# They hold a dict rather than derive from it: CPython prints True three times.
c = Counter("abca")
d: defaultdict[str, int] = defaultdict(int)
od: OrderedDict[str, int] = OrderedDict()
print(isinstance(c, dict), isinstance(d, dict), isinstance(od, dict))

# keys(), values() and items() are lists, as a dict's are here (CPython: dict_keys([...]), ...),
# and elements() is a list (CPython: <itertools.chain object at 0x...>).
print(c.keys(), c.values(), c.items(), c.elements())

# A loop gets the keys the mapping has when it starts: CPython raises RuntimeError: dictionary
# changed size during iteration (OrderedDict mutated during iteration) at the second key.
for k in c:
    if k == "a":
        c["z"] = 1
print(c)

# A factory that is not a builtin class given to the constructor has no repr here: CPython
# prints defaultdict(<function <lambda> at 0x...>, {'x': 0}), then defaultdict(<class 'int'>,
# {'x': 0}) for a builtin class assigned to default_factory later.
lam: defaultdict[str, int] = defaultdict(lambda: 0)
lam["x"]
print(lam)
lam.default_factory = int
print(lam)
