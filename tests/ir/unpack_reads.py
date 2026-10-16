# Unpacking a list reads its items with inline loads once its length check (pys_unpack_check,
# or pys_unpack_ex_check around a starred target) has passed: unpack_reads.calls pins that no
# pys_list_get follows, in a loop too, also where a target's store may change the list and
# every item is read first. A str's items are pys_str_get calls.


def pairs(loops: int, xs: list[int]) -> int:
    a = b = 0
    for _ in range(loops):
        a, b = xs
    return a - b


def ends(xs: list[float]) -> float:
    first, *mid, last = xs
    return first + last + len(mid)


def swap(xs: list[str]) -> None:
    xs[1], xs[0] = xs


def chars(s: str) -> str:
    c, d = s
    return d + c


ws = ["p", "q"]
swap(ws)
print(pairs(3, [5, 3]), ends([1.0, 2.0, 3.0]), ws, chars("ab"))
