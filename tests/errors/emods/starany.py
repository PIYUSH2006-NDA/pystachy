from typing import Any


def report(msg: str, **kwargs: Any) -> str:
    return msg


def collect(*args: Any) -> int:
    return len(args)
