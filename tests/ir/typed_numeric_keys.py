# Pure typed numeric operations retain repeated-key equivalence for dictfuse.


def cast_key(values: dict[int, int], flag: bool) -> int:
    if int(flag) in values:
        return values[int(flag)]
    return -1


def compare_key(values: dict[int, int], a: int, b: int) -> int:
    if int(a < b) in values:
        return values[int(a < b)]
    return -1


def other_comparison(values: dict[int, int], a: int, b: int) -> int:
    if int(a < b) in values:
        return values[int(a > b)]
    return -1
