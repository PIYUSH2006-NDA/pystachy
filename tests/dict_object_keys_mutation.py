# keys whose __eq__ or __repr__ empties the dict or set it is compared or printed in: printing,
# equality, lookups and the set operations go on with what is left (a lookup starts again, as
# CPython's does), and read nothing that the change freed


log: list[str] = []


class K:
    def __init__(self, v: int) -> None:
        self.v = v
        self.victims: list[dict["K", int]] = []
        self.svictims: list[set["K"]] = []

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, K):
            return False
        log.append(f"eq {self.v} {other.v}")
        for d in self.victims:
            d.clear()
        for s in self.svictims:
            s.clear()
        self.victims = []
        self.svictims = []
        return self.v == other.v

    def __repr__(self) -> str:
        for d in self.victims:
            d.clear()
        self.victims = []
        return f"K{self.v}"


def flush(label: str) -> None:
    print(label, log)
    log.clear()


a = K(1)
b = K(2)
d = {a: 1, b: 2}
flush("built")
a.victims = [d]
print(d, d)
x = {K(1): 1, K(2): 2}
y = {K(1): 1, K(2): 2}
flush("built")
for k in x:
    k.victims = [x]
print(x == y, x, y)
flush("==")
s = {K(1), K(2), K(3)}
t = {K(1), K(2), K(3)}
flush("built")
for k in t:
    k.svictims = [t]
r = s - t
print(r, len(t))
flush("-")
t = {K(1), K(2), K(3)}
for k in t:
    k.svictims = [t]
print(s & t, len(t))
flush("&")
t = {K(1), K(2), K(3)}
for k in t:
    k.svictims = [t]
print(len(s ^ t), len(t))
flush("^")
u = {K(1), K(2)}
w: dict[K, int] = {}
for k in u:
    w[K(k.v)] = 0
for k in w:
    k.svictims = [u]
flush("built")
print(u.difference(w), len(u))
flush("difference(d)")
v = {K(1), K(2), K(3)}
z = {K(1)}
for k in v:
    k.svictims = [v]
print(K(2) in v, len(v), z <= v, v.isdisjoint(z))
flush("in, <=, isdisjoint")
