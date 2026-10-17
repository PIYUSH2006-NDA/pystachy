# error: _zip_get() returns both int and str
# itertools.zip_longest()'s fillvalue is None or a value of each iterable's item type: a tuple's
# item has one type (lib/compatibility.md)
from itertools import zip_longest

print(list(zip_longest([1, 2], [3], fillvalue="-")))
