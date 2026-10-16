# Documented deviation: d.update(o) goes on with what is left of o where an __eq__ that the merge
# calls empties o, where CPython raises RuntimeError: dict mutated during update (here CPython
# prints "RuntimeError dict mutated during update" and "2 0"); so do dict(o) and o.copy() of an o
# with many deleted keys, which merge o into a new dict (CPython: "RuntimeError dict mutated
# during update" twice, then "0 0").
class X:
    def __init__(self, v: int) -> None:
        self.v = v

    def __hash__(self) -> int:
        return 0

    def __eq__(self, o: object) -> bool:
        if armed:
            other.clear()
        return False


armed = False
other: dict[X, int] = {}
for i in range(3):
    other[X(i)] = i
d = {X(-1): 0}
armed = True
try:
    d.update(other)
except RuntimeError as e:
    print("RuntimeError", e)
print(len(d), len(other))
armed = False
ks = [X(i) for i in range(6)]
for k in ks:
    other[k] = k.v
for k in ks[:3]:
    del other[k]
armed = True
try:
    c = dict(other)
    print(len(c))
except RuntimeError as e:
    print("RuntimeError", e)
armed = False
for k in ks:
    other[k] = k.v
for k in ks[:3]:
    del other[k]
armed = True
try:
    c = other.copy()
    print(len(c))
except RuntimeError as e:
    print("RuntimeError", e)
print(len(other))
