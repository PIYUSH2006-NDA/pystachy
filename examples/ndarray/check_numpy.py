"""check_numpy: ndarray and lazy, run by CPython, against NumPy on the same data.

usage: python3 check_numpy.py

Elementwise arithmetic, broadcasting, views, total(), mean(), sum_axis() and lazy evaluate() must
give NumPy's float64 results to the last bit, signed zeros, infinities and nans included; lazy sum()
must be the items added in order, and within 1e-12 relative of np.sum's pairwise result.
dot() must be np.sum(a * b) exactly and np.dot within 1e-12 relative, and matmul() within 1e-12
relative of a @ b: BLAS adds in other orders. The errors of broadcasting, reshape, indexing and
matmul must have NumPy's messages. The script stops at the first difference with exit status 1.
It needs NumPy, which a compiled program cannot import, so it runs under CPython only.
"""
import math
import sys

import numpy as np

from lazy import lazy
from ndarray import NDArray, array, array2, dot, matmul, mean, sum_axis, total

checks = [0, 0]  # exact, within tolerance


def fail(what: str) -> None:
    print("DIFFERS:", what)
    sys.exit(1)


def same(x: float, y: float) -> bool:
    # the same float64, a nan for a nan and -0.0 for -0.0
    if x != x or y != y:
        return x != x and y != y
    return x == y and math.copysign(1.0, x) == math.copysign(1.0, y)


def exact(what: str, mine: NDArray, theirs: np.ndarray) -> None:
    if mine.shape != list(theirs.shape):
        fail(f"{what}: shape {mine.shape} against {list(theirs.shape)}")
    for i, (x, y) in enumerate(zip(mine.values(), theirs.ravel().tolist())):
        if not same(x, y):
            fail(f"{what}: item {i} is {x!r}, NumPy's {y!r}")
    checks[0] += 1


def exact_float(what: str, x: float, y: float) -> None:
    if not same(x, float(y)):
        fail(f"{what}: {x!r}, NumPy's {float(y)!r}")
    checks[0] += 1


def close(what: str, xs: list[float], ys: list[float]) -> None:
    scale = max([abs(y) for y in ys] + [1e-300])
    for i, (x, y) in enumerate(zip(xs, ys)):
        if abs(x - y) > 1e-12 * scale:
            fail(f"{what}: item {i} is {x!r}, NumPy's {y!r}")
    checks[1] += 1


def raises(what: str, mine, theirs) -> None:
    # mine and theirs are calls that raise; their messages must be the same
    msgs = []
    for f in [mine, theirs]:
        try:
            f()
            fail(f"{what}: no error")
        except (ValueError, IndexError) as e:
            msgs.append(str(e))
    if msgs[0] != msgs[1]:
        fail(f"{what}: {msgs[0]!r}, NumPy's {msgs[1]!r}")
    checks[0] += 1


def nd(x: np.ndarray) -> NDArray:
    # the same float64 values as a C-order NDArray
    c = np.ascontiguousarray(x, dtype=np.float64)
    st = [s // 8 for s in c.strides]
    return NDArray(c.ravel().tolist(), list(c.shape), st, 0)


rng = np.random.default_rng(2026)
a = rng.standard_normal((3, 4))
b = rng.standard_normal((3, 4))
row = rng.standard_normal(4)
col = rng.standard_normal((3, 1))
cube = rng.standard_normal((2, 3, 4))
A, B, R, C, K = nd(a), nd(b), nd(row), nd(col), nd(cube)

for name, f, g in [("+", lambda x, y: x + y, np.add), ("-", lambda x, y: x - y, np.subtract),
                   ("*", lambda x, y: x * y, np.multiply), ("/", lambda x, y: x / y, np.divide)]:
    exact(f"a {name} b", f(A, B), g(a, b))
    exact(f"a {name} row", f(A, R), g(a, row))
    exact(f"a {name} col", f(A, C), g(a, col))
    exact(f"cube {name} a", f(K, A), g(cube, a))
    exact(f"col {name} cube", f(C, K), g(col, cube))
    exact(f"a.T {name} b.T", f(A.T, B.T), g(a.T, b.T))
    exact(f"a {name} 2.5", f(A, 2.5), g(a, 2.5))
    exact(f"a {name} 3", f(A, 3), g(a, 3))
exact("-a", -A, -a)
exact("-a.T", -(A.T), -(a.T))
exact("a.T", A.T, a.T)
exact("a.T.reshape(2, 6)", A.T.reshape([2, 6]), a.T.reshape(2, 6))
exact("cube.reshape(4, 6).T", K.reshape([4, 6]).T, cube.reshape(4, 6).T)
exact("cube[1]", K.row(1), cube[1])
exact("cube[-1][2]", K.row(-1).row(2), cube[-1][2])
special = np.array([1.0, -1.0, 0.0, -0.0, np.inf, -np.inf, np.nan, 2.5])
S = nd(special)
with np.errstate(divide="ignore", invalid="ignore"):
    for z in [0.0, -0.0]:
        exact(f"special / {z!r}", S / z, special / z)
    exact("special / special", S / S, special / special)
    exact("special * special", S * S, special * special)
    exact("special - special", S - S, special - special)

for n in [0, 1, 7, 8, 9, 127, 128, 129, 1000, 4097, 100003]:
    x = rng.standard_normal(n) * 1000.0
    X = nd(x)
    exact_float(f"total, {n} items", total(X), np.sum(x))
    if n > 0:
        exact_float(f"mean, {n} items", mean(X), np.mean(x))
exact_float("total of [-0.0]", total(array([-0.0])), np.sum(np.array([-0.0])))
big = rng.standard_normal((300, 70))
G = nd(big)
exact_float("total of a transpose", total(G.T), np.sum(big.T))
exact_float("total of a 3-D transpose", total(nd(cube).T), np.sum(cube.T))
exact_float("total of a strided row", total(G.T.row(5)), np.sum(big.T[5]))
exact_float("mean of a transpose", mean(G.T), np.mean(big.T))
m = rng.standard_normal((50, 37))
M = nd(m)
for axis in [0, 1, -1]:
    exact(f"sum axis {axis}", sum_axis(M, axis), np.sum(m, axis=axis))
    exact(f"sum axis {axis} of the transpose", sum_axis(M.T, axis), np.sum(m.T, axis=axis))

x = rng.standard_normal(10007)
y = rng.standard_normal(10007)
X, Y = nd(x), nd(y)
d = lazy(X) - lazy(Y)
in_order = 0.0
for v in ((x - y) * (x - y)).tolist():
    in_order += v
exact_float("lazy sum((x - y) * (x - y)), in order", (d * d).sum(), in_order)
close("lazy sum((x - y) * (x - y)) against np.sum", [(d * d).sum()], [float(np.sum((x - y) * (x - y)))])
exact("lazy x * y + 1", (lazy(X) * lazy(Y) + 1.0).evaluate(), x * y + 1.0)
exact("lazy (x - 2) / y", ((lazy(X) - 2) / lazy(Y)).evaluate(), (x - 2) / y)
exact_float("dot is np.sum(x * y)", dot(X, Y), np.sum(x * y))
close("dot against np.dot", [dot(X, Y)], [float(np.dot(x, y))])
p = rng.standard_normal((17, 23))
q = rng.standard_normal((23, 9))
P, Q = nd(p), nd(q)
close("matmul", matmul(P, Q).values(), (p @ q).ravel().tolist())
close("matmul of transposes", matmul(Q.T, P.T).values(), (q.T @ p.T).ravel().tolist())
close("@", (P @ Q).values(), (p @ q).ravel().tolist())

two = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
T = array2(two.tolist())
raises("broadcast", lambda: T + array([1.0, 2.0]), lambda: two + np.array([1.0, 2.0]))
raises("broadcast (3,1)", lambda: T + nd(col), lambda: two + col)
raises("reshape", lambda: T.reshape([4]), lambda: two.reshape(4))
raises("index", lambda: T[2, 0], lambda: two[2, 0])
raises("negative index", lambda: T[0, -4], lambda: two[0, -4])
raises("1-D index", lambda: array([1.0])[3], lambda: np.array([1.0])[3])
raises("too many indices", lambda: array([1.0])[0, 0], lambda: np.array([1.0])[0, 0])
raises("matmul", lambda: matmul(T, T), lambda: two @ two)
print(f"{checks[0]} checks equal NumPy's to the last bit, {checks[1]} within 1e-12 (numpy {np.__version__})")
