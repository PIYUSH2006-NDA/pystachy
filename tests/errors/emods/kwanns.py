from typing import Any


def show(**kwargs: Any) -> int:
    return len(kwargs)


def count() -> int:
    return 3
