from typing import Any


def show(**kwargs: Any) -> int:
    return len(kwargs)


def tally(**kwargs: int) -> int:
    return sum(kwargs.values())


def count() -> int:
    return 3
