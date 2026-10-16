# init_hasattr: __init__ that makes a field only where hasattr(self, "f") is false keeps it on a
# second call, as a dict's storage made by dict.__new__ (lib/collections). The field has an "is
# assigned" flag for hasattr, but flow finds it assigned wherever it is read: init_hasattr.calls
# pins that the methods reading it raise no AttributeError (each read of a flagged field would)
class Tally:
    def __init__(self, xs: list[str]) -> None:
        if not hasattr(self, "counts"):
            self.counts: dict[str, int] = {}
        for x in xs:
            self.counts[x] = self.counts.get(x, 0) + 1

    def get(self, x: str) -> int:
        return self.counts.get(x, 0)


t = Tally(["a", "b", "a"])
t.__init__(["a"])
print(t.get("a"), t.get("b"))
