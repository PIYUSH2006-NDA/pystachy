# A generator that an itertools iterator reads is not closed when the iterator is dropped, as a
# generator the program drops is not (tests/deviations/gen_finalization.py): CPython closes it as
# the iterator's last reference goes, here as the loop ends (lib/compatibility.md)
from itertools import islice
from collections.abc import Iterator


def resource() -> Iterator[int]:
    print("acquire")
    try:
        yield 1
        yield 2
        yield 3
    finally:
        print("release")


for x in islice(resource(), 2):
    print("got", x)
print("after the loop")
