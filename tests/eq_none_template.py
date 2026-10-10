# a template's parameter defaulted to None, compared with == and !=: for a None argument the
# test is a constant, as `is None` is, so the branch that does not run is not compiled
class N:
    def __init__(self, v: int) -> None:
        self.v = v


class Q:
    def __init__(self, v: int) -> None:
        self.v = v

    def __eq__(self, o: "Q") -> bool:
        print("Q.__eq__")
        return o is not None and self.v == o.v


def find(xs, target=None):
    for i, x in enumerate(xs):
        if target == None or x == target:
            return i
    return -1


def until(xs, stop=None):
    out = []
    for x in xs:
        if x == stop or stop == x:
            break
        out.append(x)
    return out


def scale(x, by=None):
    if by == None:
        return x
    return x * by


def scale2(x, by=None):
    if by != None:
        return x * by
    return x


def show(o, alt=None):
    if o == None:
        return "none"
    if alt != None:
        return alt
    return "obj"


def pick(a, b=None, c=None):
    return a if b == None and None == c else b


print(find([4, 5, 6]), find([4, 5, 6], 6), find(["a", "b"], "b"), find([1.5, 2.5]), find([True], False))
print(until([1, 2, 3]), until([1, 2, 3], 2), until(["a"]), until(["a", "b"], "b"))
print(scale(3), scale(3, 2), scale("s"), scale("s", 3), scale2(2), scale2(2, 5), scale2(1.5), scale2([1], 2))
print(show(N(1)), show(Q(1)), show(N(2), "alt"), show(None))
print(pick(1), pick(1, 2), pick("a", None, "c"))
