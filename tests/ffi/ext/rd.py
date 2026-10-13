# input() and sys.stdin in an extension module are the host's: a replaced sys.stdin is read
import sys
from ffi import export


@export
def ask(prompt: str) -> str:
    return input(prompt)


@export
def line() -> str:
    return sys.stdin.readline()


@export
def rest() -> str:
    return sys.stdin.read()


@export
def shout(s: str) -> None:
    print(s.upper(), flush=True)
