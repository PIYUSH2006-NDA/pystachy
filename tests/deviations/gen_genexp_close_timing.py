# Documented deviation (#490): where an exception leaves a consumer's generator expression, the
# generator that its loop owns is closed before the handler runs (Pystachy closes it as the
# exception leaves the loop); CPython closes it once the handler has finished, because the
# exception's traceback holds the generator expression's frame, and so the generator, until then.
from collections.abc import Iterator


def numbers() -> Iterator[int]:
    try:
        yield 1
        yield 2
    finally:
        print("numbers closed")


def check(x: int) -> bool:
    if x == 2:
        raise ValueError("bad item")
    return False


try:
    print(any(check(x) for x in numbers()))
except ValueError as e:
    print("caught", e)
print("end")
