# error: dictionary update sequence element #0 has length 3; 2 is required (dict() of a list[tuple[int,int,int]])
# (CPython's ValueError, at compile time: every item of the list has that length)
print(dict([(1, 2, 3)]))
