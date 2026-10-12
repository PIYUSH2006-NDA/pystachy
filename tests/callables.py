# Callable[[A, B], R] annotations: a function value (a def, a builtin, a lambda, a closure) becomes
# a Callable where one is expected, so one variable, field, list or dict holds different functions
import math
from collections.abc import Callable as AbcCallable
from dataclasses import dataclass
from typing import Callable, Optional


def double(x: int) -> int:
    return x * 2


def triple(x):
    return x * 3


def shout(s: str) -> None:
    print(s.upper())


def apply_all(fs: list[Callable[[int], int]], x: int) -> list[int]:
    return [f(x) for f in fs]


def adder(n: int) -> Callable[[int], int]:
    return lambda x: x + n


def compose(f: Callable[[int], int], g: Callable[[int], int]) -> Callable[[int], int]:
    return lambda x: f(g(x))


class Parser:
    def __init__(self, fn: Callable[[str, int], int]) -> None:
        self.fn = fn

    def __call__(self, s: str, i: int) -> int:
        return self.fn(s, i)

    def then(self, other: "Parser") -> "Parser":
        def both(s: str, i: int) -> int:
            j = self(s, i)
            return other(s, j) if j >= 0 else -1
        return Parser(both)


def lit(c: str) -> Parser:
    return Parser(lambda s, i: i + 1 if i < len(s) and s[i] == c else -1)


@dataclass
class Op:
    name: str
    run: Callable[[float, float], float]


class Scale:
    def __init__(self, k: int) -> None:
        self.k = k

    def scaler(self) -> Callable[[int], int]:
        return lambda x: x * self.k


def table() -> dict[str, Callable[[float], float]]:
    return {"sqrt": math.sqrt, "neg": lambda v: -v, "half": lambda v: v / 2}


def maybe(f: Optional[Callable[[int], int]], x: int) -> int:
    return x if f is None else f(x)


def run_template(f, x):
    return f(x)


def raising(x: int) -> int:
    if x < 0:
        raise ValueError(f"negative {x}")
    return x


fs: list[Callable[[int], int]] = [double, triple, lambda v: v - 1, abs, adder(10)]
print(apply_all(fs, 5), apply_all([double], -7), compose(double, adder(1))(5), compose(adder(1), double)(5))
p = lit("a").then(lit("b")).then(lit("c"))
print(p("abc", 0), p("abx", 0), lit("x")("x", 0), lit("x")("y", 0))
ops = [Op("add", lambda a, b: a + b), Op("pow", math.pow), Op("max", max)]
print([(o.name, o.run(2.0, 3.0)) for o in ops])
print(Scale(4).scaler()(5), [(k, f(16.0)) for k, f in sorted(table().items(), key=lambda kv: kv[0])])
print(maybe(None, 3), maybe(double, 3), maybe(lambda v: v * v, 3), run_template(adder(5), 1))
g: Callable[[int], int] = double
print(g(4), g == double, g == triple)
g = triple
print(g(4), g == double)
h: AbcCallable[[str], None] = shout
h("quiet")
h = print
h("printed")
noargs: Callable[[], str] = lambda: "none"
print(noargs(), (double, triple)[1](2))
safe: Callable[[int], int] = raising
for v in [3, -2]:
    try:
        print(safe(v))
    except ValueError as e:
        print("caught", e)
same = adder(1)
c1: Callable[[int], int] = same
c2: Callable[[int], int] = same
c3: Callable[[int], int] = adder(1)
print(c1 == c2, c1 is c2, c1 == c3, c1 != c3)
