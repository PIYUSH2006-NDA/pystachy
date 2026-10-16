# Documented deviation (#490): a suspended generator that the program drops without finishing
# it is never closed, so its finally blocks (and with blocks) do not run; CPython closes it as
# soon as its last reference goes (here at del: "release a" before "after del"). A generator that
# a for loop made and still owns is closed as CPython closes it, where the loop is left.
from collections.abc import Iterator


def resource(name: str) -> Iterator[int]:
    print("acquire", name)
    try:
        yield 1
        yield 2
    finally:
        print("release", name)


g = resource("a")
for v in g:
    print("got", v)
    break
del g
print("after del")


def first_only() -> int:
    for v in resource("b"):
        return v
    return 0


print(first_only())
print("end")
