"""Explicit union boxing cost; CPU time for construction and scanning excludes process startup.

Build once, then alternate `./union_values typed 1000000` and `boxed 1000000`.
Use PYSTACHY_GC=stats in a separate untimed run to report heap peak.
The boxed scan narrows explicitly so this also runs on the union-storage parent.
"""
import sys
from time import process_time_ns


def typed(n: int) -> None:
    start = process_time_ns()
    values: list[int] = []
    for i in range(n):
        values.append(i)
    built = process_time_ns()
    total = 0
    for value in values:
        total += value
    end = process_time_ns()
    print(total, built - start, end - built)


def boxed(n: int) -> None:
    start = process_time_ns()
    values: list[int | str] = []
    for i in range(n):
        values.append(i)
    built = process_time_ns()
    total = 0
    for value in values:
        if isinstance(value, int):
            total += value
    end = process_time_ns()
    print(total, built - start, end - built)


n = int(sys.argv[2])
assert n > 0 and n <= 10000000
if sys.argv[1] == "typed":
    typed(n)
else:
    assert sys.argv[1] == "boxed"
    boxed(n)
