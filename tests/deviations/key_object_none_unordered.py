# Documented deviation: a key object (an instance of a class that defines __call__) that is None
# when sorted(), min(), max() or list.sort() runs, where the items have no order of their own (of
# a closed union here), is called, raising TypeError, where CPython takes key=None as no key and
# orders the items. CPython prints
# [1, 2, 3]
class Text:
    def __call__(self, x: int | str) -> str:
        return str(x)


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
