# Documented deviation: a key object (an instance of a class that defines __call__) that is None
# when sorted(), min(), max() or list.sort() runs, where the items are objects or have no order
# of their own (of a closed union here), is called, raising TypeError, where CPython takes
# key=None as no key and orders the items. CPython prints
# [1, 2, 3]
# [Item(1), Item(2)]
class Text:
    def __call__(self, x: int | str) -> str:
        return str(x)


class Item:
    def __init__(self, n: int) -> None:
        self.n = n

    def __lt__(self, other: "Item") -> bool:
        return self.n < other.n

    def __repr__(self) -> str:
        return f"Item({self.n})"


class ByNeg:
    def __call__(self, i: Item) -> int:
        return -i.n


class Holder:
    def __init__(self) -> None:
        self.key: Text | None = Text()


h = Holder()
xs: list[int | str] = [3, 1, 2]
print(sorted(xs, key=h.key))
h.key = None
try:
    print(sorted(xs, key=h.key))
except TypeError as e:
    print("TypeError:", e)


def by_item(by: ByNeg | None) -> None:
    try:
        print(sorted([Item(2), Item(1)], key=by))
    except TypeError as e:
        print("TypeError:", e)


by_item(ByNeg())
by_item(None)
