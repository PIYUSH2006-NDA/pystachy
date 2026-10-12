"""A module's object called through its class's __call__, also by its own methods (self(...))."""


class Hamming:
    def __call__(self, a: str, b: str) -> int:
        n = 0
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                n += 1
        return n + abs(len(a) - len(b))

    def similarity(self, a: str, b: str) -> int:
        return max(len(a), len(b)) - self(a, b)


hamming = Hamming()
missing: Hamming | None = None
