# Documented deviation: a key object (an instance of a class that defines __call__) that is
# None when sorted(), min(), max() or list.sort() runs is called, raising TypeError, where
# CPython takes key=None as no key. CPython prints
# [(1, 'b'), (2, 'a')]
from operator import itemgetter


class Holder:
    def __init__(self) -> None:
        self.key = itemgetter(1)


h = Holder()
h.key = None
try:
    print(sorted([(2, "a"), (1, "b")], key=h.key))
except TypeError as e:
    print("TypeError:", e)
