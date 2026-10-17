# itertools loops (lib/_pystachy_itertools.py, generators): product() of three ranges, the pairs
# of combinations() of a list, run lengths of groupby() over a string, and chain() of lists
from itertools import chain, combinations, groupby, product

hits = 0
for a, b, c in product(range(120), range(120), range(120)):
    if a + b + c == 180:
        hits += 1
print("product", hits)

xs = [(i * 7919) % 1009 for i in range(2500)]
ordered = 0
for x, y in combinations(xs, 2):
    if x < y:
        ordered += 1
print("combinations", ordered)

parts: list[str] = []
seed = 12345
for i in range(400000):
    seed = (seed * 1103515245 + 12345) % 2147483648
    parts.append("ab"[(seed >> 16) % 2] * (1 + (seed >> 8) % 3))
text = "".join(parts)
runs = 0
longest = 0
for key, group in groupby(text):
    size = 0
    for ch in group:
        size += 1
    runs += 1
    longest = max(longest, size)
print("groupby", len(text), runs, longest)

total = 0
for round in range(100):
    for v in chain(xs, xs[::-1], range(2000)):
        total += v ^ round
print("chain", total)
