# Repeated reads of a narrowed union key must retain the dictionary lookup fusion
# that the equivalent raw GEP/load instructions allowed before typed union reads.


def str_key(values: dict[str, int], key: int | str) -> int:
    if isinstance(key, str):
        if key in values:
            return values[key]
    return -1


def int_key(values: dict[int, int], key: int | str) -> int:
    if isinstance(key, int):
        if key in values:
            return values[key]
    return -1
