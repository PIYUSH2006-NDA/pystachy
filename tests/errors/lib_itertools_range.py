# error: range() is only supported in a for loop
# range() is not a value in Pystachy (lib/compatibility.md): itertools' functions take
# list(range(n)) or iter(range(n))
from itertools import combinations

print(list(combinations(range(4), 2)))
