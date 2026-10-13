# a def whose *args or **kwargs annotation Pystachy can't type (Any), as pyfiglet's print_figlet():
# left out, as a def with such a plain parameter is, so an error only where the program calls it
from typing import Any


def report(msg: str, **kwargs: Any) -> str:
    return msg + str(len(kwargs))


def collect(*args: Any) -> int:
    return len(args)


def double(x: int, **kwargs: int) -> int:
    return x * 2 + len(kwargs)
