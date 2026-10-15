# error: got list[int]
# No arbitrary member is chosen when two container layouts fit the empty result.
def empty(n):
    return []


result: list[str] | list[float] = empty(1)
print(result)
