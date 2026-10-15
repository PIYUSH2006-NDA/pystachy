# str.format() and str.format_map() of a literal format: automatic and manual numbering,
# keywords, attribute and item lookups, conversions, specs with nested fields, escaped braces,
# *args and **kwargs of several kinds, the order in which arguments are evaluated and fields
# formatted, and use in functions, methods, closures, templates and at module level
from typing import NamedTuple


class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.tags = ["a", "b"]
        self.meta = {"name": "pt", "1": "one"}

    def __format__(self, spec: str) -> str:
        print("  Point.__format__", repr(spec))
        return f"<{self.x},{self.y}|{spec}>"

    def __str__(self) -> str:
        print("  Point.__str__")
        return f"P{self.x}"

    def __repr__(self) -> str:
        print("  Point.__repr__")
        return f"Point({self.x}, {self.y})"


class Pair(NamedTuple):
    a: int
    b: str


def arg(v: str) -> str:
    print("  arg", v)
    return v


def width(n: int) -> int:
    print("  width", n)
    return n


# numbering, keywords and escapes
print("{} and {}".format(1, "x"))
print("{1}{0}{1}".format("a", "b"))
print("{00}|{1}".format("zero", "one"))
print("{x}-{y:>4}-{x}".format(x=1, y="ab"))
print("{0}, {name}, {1}".format(1.5, True, name=None))
print("{}{name}{}".format("a", "b", name="-"))
print("x{{y}}z{{}}".format())
print("{{{}}}".format(42))
print("}}{{".format())
print("no fields".format(1, 2, k=3))
print("".format())
print("{0:}|{0!s:}|{0!r:}".format(7))
print("{!r}".format("it's"))

# specs, including nested fields, which take arguments in order too
print("{:{w}.{p}f}".format(3.14159, w=10, p=3))
print("{0:{1}}|{2:>{1}}".format("ab", 5, "c"))
print("{:{}{}}|".format(1, ">", 6))
print("{:x} {:#o} {:,} {:_b} {:+.2e} {:%}".format(255, 8, 1234567, 10, 12345.678, 0.25))
print("{:*^11}|{:<6}|{:06.2f}".format("mid", True, -2.5))
print("{0:{fill}{align}{w}}".format("v", fill="-", align="^", w=7))
print("{:{}}".format(1.5, width(7)))

# attribute and item lookups: an item's key is an int where it is digits, else a str
p = Point(3, 4)
print("{0.x} {0.y} {1.x}".format(p, Point(9, 9)))
print("{.y} {.x}".format(p, p))
print("{0[1]} {0[0]} {1[0]}".format([10, 20], ["first"]))
print("{[1]}{[0]}".format("ab", "cd"))
print("{d[k]} {d[-1]} {0[name]}".format({"name": "n"}, d={"k": "5", "-1": "str key"}))
print("{0[1]}".format({1: "int one"}))
print("{0.tags[1]} {0.meta[name]}".format(p))
print("{t[0]}{t[1]}".format(t=(1, "x")))
print("{0[2]}{0[0]}".format("abc"))
print("{p.a}:{p.b} {p[0]}".format(p=Pair(1, "b")))

# conversions, and objects' __format__, __str__ and __repr__
print("{0} {0:spec} {0!s} {0!r} {0!s:>4} {0!r:.5}".format(p))
print("{!a} {!r} {!s:^5}|".format("é", "ü", "ö"))
print("{0!a:>8}|".format("ñ"))

# non-ASCII text around and in fields
print("ä{}ö{name}ü".format("€", name="名前"))
print("{名}".format(**{"名": "value"}))
print("{:é^7}".format("x"))

# arguments are evaluated first, in order, then the fields formatted left to right
print("{1}{0}{2:{3}}".format(arg("a"), arg("b"), Point(1, 2), arg(">3")))
print("{0:{w}}{1!r}".format(Point(5, 6), Point(7, 8), w=width(4)))

# *args: a tuple's items, a NamedTuple's fields, a list's items (as the last)
t = (1, "two", 3.0)
print("{} {} {}".format(*t))
print("{2}{1}{0}".format(*t))
print("{}+{}".format(*Pair(5, "five")))
print("{}/{}/{}".format(0, *(1, 2)))
xs = ["a", "b", "c"]
print("{}-{}".format(*xs))
print("{0}{3}".format("x", *xs))
print("{}:{}:{}".format(*[n * 2 for n in range(3)]))
vt: tuple[int, ...] = tuple([4, 5])
print("{1}.{0}".format(*vt))
print("{} {}".format(*"ab".split("b")))

# **kwargs: a dict display, a dict[str, T] (copied as the call made it), a function's **kwargs
print("{a}{b}".format(**{"a": 1, "b": 2}))
print("{a}{b}".format(b=1, **{"a": 0, "a": 2}))
d = {"a": 1, "b": 2}
print("{a}+{b}={c}".format(c=3, **d))
print("{a}".format(**d))


def kw(**kwargs: int) -> str:
    return "{x}:{y}".format(**kwargs)


print(kw(x=1, y=2))
print("{a}{b}".format_map(d))
print("{name[a]}-{name[b]}".format_map({"name": {"a": "nested", "b": "x"}}))
print("plain".format_map(d))
print(str.format("{}!{x}", 5, x=6))
print(str.format_map("{a}", d))

# in a function, a method, a closure and a template
def label(n: int, unit: str) -> str:
    return "{n:>3} {unit}{s}".format(n=n, unit=unit, s="" if n == 1 else "s")


class Money:
    def __init__(self, cents: int) -> None:
        self.cents = cents

    def __str__(self) -> str:
        return "${}.{:02d}".format(self.cents // 100, self.cents % 100)

    def show(self, name: str) -> str:
        return "{0}: {1!s}".format(name, self)


def counter(prefix: str):
    n = [0]

    def nxt() -> str:
        n[0] += 1
        return "{}#{}".format(prefix, n[0])

    return nxt


def show[T](v: T) -> str:
    return "[{!r:>6}]".format(v)


print(label(1, "item"), label(12, "item"))
print(str(Money(1234)), Money(5).show("price"))
c = counter("id")
print(c(), c())
print(show(1), show("ab"), show(2.5))
print([("{:02d}".format(i)) for i in range(3)])
print(", ".join("{}={}".format(k, v) for k, v in sorted(d.items())))
s = "{}"
print(s, "{}".format(s))

# keywords are evaluated after the positional arguments, also where written before a *
t2 = ("p", "q")
print("{k}{}{}{}".format(arg("a"), k=arg("k"), *t2))
print("{k}{j}{}".format(*t2, k=arg("k"), **{"j": arg("j")}))
print(list(map("{:>3}|".format, [1, 22])), list(map("{}{}".format, "ab", [1, 2])))
