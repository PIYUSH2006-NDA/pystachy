# ordered-set's OrderedSet: the edge cases the port met (see ports/ordered_set/PORT.md): the
# empty set, awkward strings, indices at both ends of the 64-bit range, pop(i), which leaves
# the indices of the items after i as they were (upstream 4.1.0 does so too), duplicates in
# the lists the set algebra takes, equality, iteration, and 3,000 tokens deduplicated
from ordered_set import OrderedSet

empty = OrderedSet()
print("empty:", repr(empty), str(empty), len(empty), bool(empty), not empty, "" in empty, list(empty))
try:
    empty.pop()
except KeyError as exc:
    print("KeyError:", exc, repr(exc))
try:
    empty.index("")
except KeyError as exc:
    print("KeyError:", exc)
try:
    print(empty[0])
except IndexError as exc:
    print("IndexError:", exc)
empty.discard("x")
empty.clear()
print("empty:", empty.union([]), empty.intersection(["a"]), empty.difference([]), empty.symmetric_difference([]))
print("empty:", empty.issubset([]), empty.issuperset([]), empty == OrderedSet([]), empty.copy() is not empty, empty.map)

# strings with quotes, escapes, 2-, 3- and 4-byte UTF-8, non-printables and the empty string
odd = ["it's", 'say "hi"', "tab\there", "nl\n", "\x00", "\x7f", "é", "€", "😀", "​", "\\", "Ω≈ç", ""]
s = OrderedSet(odd + odd)
print(repr(s))
print(len(s), [s.index(w) for w in odd], [w in s for w in odd], s[8], s[-1] == "", s[-5])
for k in ["ünï", "😀😀", "'", '"', "e", " "]:
    try:
        s.index(k)
    except KeyError as exc:
        print("KeyError:", exc, repr(exc))
print(str(s) == repr(s), f"{s!r}" == repr(s), f"{s}" == repr(s))

# indices out of range, at both ends of the 64-bit range too
a = OrderedSet(["x", "y", "z"])
for idx in [3, -4, 9223372036854775807, -9223372036854775807, -9223372036854775807 - 1]:
    try:
        print(a[idx])
    except IndexError as exc:
        print("IndexError:", exc)
    try:
        a.pop(idx)
    except IndexError as exc:
        print("IndexError pop:", exc)
print(a, [a.index(w) for w in a], a[-3], a[2], a.get_loc("z"), a.get_indexer("x"))

# what add, append and update return
print("add:", a.add("w"), a.add("x"), a.append("w"), a.append("v"), a)
print("update:", a.update([]), a.update(["x"]), a.update(["u", "x"]), a.update(["z", "z"]), a.update(["t", "t"]), a)

# pop(i) does not reindex the items after i, so their indices go stale: discard() then
# deletes another item, and pop() fails on the item map no longer holds
c = OrderedSet(["p", "q", "r", "s", "t"])
print("pop(1):", c.pop(1), c.index("r"), c.index("t"), c.map)
c.discard("s")
print("discard:", c, c.map, "s" in c, list(c))
try:
    print(c.index("t"), c[c.index("t")])
except IndexError as exc:
    print("IndexError:", exc)
try:
    c.pop()
except KeyError as exc:
    print("KeyError:", exc)
print("after:", c, c.map, len(c))
print("pop:", c.pop(0), c.pop(-1), len(c), dict(c.map))

# discard() reindexes the items after the one it removes
d = OrderedSet(["a", "b", "c", "d", "e"])
d.discard("b")
d.discard("e")
d.discard("zz")
print("discard:", d, [d.index(w) for w in d], d.map)

# duplicates in the lists the set algebra takes (issubset's and issuperset's quick test
# compares lengths)
d = OrderedSet(["a", "b", "c"])
print(d.issubset(["a", "a", "b", "c"]), d.issubset(["a", "b"]), d.issuperset(["a", "a", "a", "a"]), d.issuperset(["c", "a"]))
print(d.symmetric_difference(["c", "c", "d", "d"]), d.union(["c", "e", "e"]), d.intersection(["c", "c", "a"]), d.difference(["a", "a"]), d.__and__(["b", "b"]))
e = d.copy()
e.difference_update(["a", "a", "z"])
print(e, e.map)
e = d.copy()
e.intersection_update(["c", "b", "b"])
print(e, e.map)
e = d.copy()
e.symmetric_difference_update(["d", "a", "d", "b"])
print(e, e.map, len(e))
print(d, d.map)

# equality, also with None and inside lists
x = OrderedSet(["x", "y"])
y = OrderedSet(["y", "x"])
n: OrderedSet | None = None
print(x == y, x != y, x == x.copy(), x != x.copy(), x == n, x != n)
group = [x, y, OrderedSet(["x", "y"])]
print(OrderedSet(["y", "x"]) in group, group.index(OrderedSet(["x", "y"])), group.count(x), OrderedSet() in group)

# iteration
w = OrderedSet(["pear", "fig", "apple", "fig", "kiwi"])
total = 0
for item in w:
    total += len(item)
out: list[str] = []
out.extend(w)
print([i for i in w], list(enumerate(w)), sorted(w), min(w), max(w), ", ".join(w), list(zip(w, out)))
print(total, out, any(t == "fig" for t in w), all(len(t) > 2 for t in w), [t for t in w if t in x], w.index(w[3]))

# 3,000 tokens deduplicated, index() of each, and 143 discards, each reindexing the rest
keys: list[str] = []
r = 1
for i in range(3000):
    r = (r * 1103515245 + 12345) % 2147483648
    keys.append("k%d" % (r % 1000))
big = OrderedSet(keys)
total = 0
for k in keys:
    total += big.index(k)
for j in range(0, 1000, 7):
    big.discard("k%d" % j)
total2 = 0
for k in keys:
    if k in big:
        total2 += big.index(k)
print("dedupe:", len(big), total, total2, big[0], big[len(big) - 1], big.index(big[500]), big.map[big[-1]])
