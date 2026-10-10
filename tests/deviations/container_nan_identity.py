# Unboxed floats still have no identity: direct containers must inspect their
# scalar values, even when their own pointers are equal. Nested containers have
# pointer identity, including optional containers; an optional scalar box does not.
nan = float("nan")
leaf = [nan]
mapping = {0: nan}
pair = (nan,)
print(nan == nan, leaf == leaf, mapping == mapping, pair == pair)
print([leaf] == [leaf], [mapping] == [mapping], [pair] == [pair])


def optional_float(value: float | None) -> None:
    values = [value]
    print(value == value, values == values, value in values, values.count(value))


optional_float(nan)
optional_float(None)
