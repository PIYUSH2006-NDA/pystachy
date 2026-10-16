# error: slicing a tuple of variable length (tuple[int, ...]) is not supported
# (only a tuple of fixed shape and a NamedTuple are sliced, by integer literals)
def tail(v: tuple[int, ...]) -> tuple[int, ...]:
    return v[1:]


print(tail((1, 2, 3)))
