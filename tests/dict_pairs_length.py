# dict() of tuples of another length than 2 (#524): an empty list (of a variable, zip(), a
# comprehension) makes an empty dict, of the type the context wants; one with an item raises
# CPython's ValueError where it runs, which an except clause catches, after the output before it.
xs: list[tuple[int, int, int]] = []
print(dict(xs), len(dict(xs)), dict(xs) == {})
e: dict[str, int] = dict(xs)
e["b"] = 2
print(e)
ones: list[tuple[str]] = []
no: list[int] = []
print(dict(ones), dict(zip(no, no, no)), dict(zip("ab", no)))
print(dict([(x, x, x) for x in range(0)]), dict([(x,) for x in ""]))
for k in dict(xs):
    print(k)
try:
    xs.append((1, 2, 3))
    print(dict(xs))
except ValueError as ex:
    print("ValueError:", ex)
try:
    print(dict(zip("ab", "cd", "ef")))
except ValueError as ex:
    print("ValueError:", ex)
try:
    print(dict([(x,) for x in "abc"]))
except ValueError as ex:
    print("ValueError:", ex)
try:
    print(dict(((1, 2, 3, 4),)))
except ValueError as ex:
    print("ValueError:", ex)
print("before")
print(dict([(1, 2, 3)]))
