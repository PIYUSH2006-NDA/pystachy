# An itertools iterator that its own input resumes, while the iterator is reading that input,
# raises ValueError: generator already executing, as a generator does (itertools' iterators are
# generators: lib/compatibility.md), and goes on as before; CPython's C pairwise() reads on from
# inside its input and skips the pairs in between (test_pairwise_reenter). The other iterators
# raise the same ValueError (CPython's groupby(), zip_longest() and others go on); tee() raises
# CPython's RuntimeError.
from itertools import pairwise
from collections.abc import Iterator


class Source:
    def __init__(self) -> None:
        self.n = 0
        self.pw: Iterator[tuple[int, int]] | None = None

    def __iter__(self):
        return self

    def __next__(self) -> int:
        self.n += 1
        if self.n == 3 and self.pw is not None:
            try:
                print("inner", next(self.pw))
            except ValueError as e:
                print("ValueError:", e)
        if self.n > 6:
            raise StopIteration
        return self.n


s = Source()
p = pairwise(s)
s.pw = p
print(list(p))
