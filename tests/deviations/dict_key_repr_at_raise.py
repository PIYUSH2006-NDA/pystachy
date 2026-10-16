# Documented deviation: the KeyError of a lookup of an object key that a dict or set does not hold
# computes the key's repr() as it is raised (as an exception computes its arguments' repr() as it
# is made, see exc_arg_repr_raises.py), so the key's __repr__ runs, and its print shows, where
# CPython calls it only when the KeyError is printed: here CPython prints "missing" and "done".
class Key:
    def __repr__(self) -> str:
        print("repr ran")
        return "Key()"


d: dict[Key, int] = {}
s: set[Key] = set()
try:
    print(d[Key()])
except KeyError:
    print("missing")
try:
    s.remove(Key())
except KeyError:
    print("missing")
print("done")
