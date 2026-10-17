# Documented deviation (#490): the StopIteration that next(), send() or throw() raises as a
# generator returns a value has no value: str(e) is "" and repr(e) "StopIteration()", where
# CPython's StopIteration(value) shows it (and CPython's uncaught one ends with
# "StopIteration: value"). A yield from gives the value (r = yield from g()), and a generator that
# has already finished raises a StopIteration without one in CPython too. The attribute e.value
# is rejected with the other exception attributes.
from collections.abc import Generator


def answer() -> Generator[int, None, int]:
    yield 1
    return 42


g = answer()
print(next(g))
try:
    next(g)
except StopIteration as e:
    print(repr(e), str(e) == "")
try:
    next(g)
except StopIteration as e:
    print("again", repr(e))
