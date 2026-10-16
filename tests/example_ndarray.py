# examples/ndarray: a float64 array in the subset and lazy expressions over it, as CPython computes
# them: views, broadcasting, IEEE division by zero, reductions in NumPy's order, matrix products,
# fused evaluation and sums, and the errors, whose messages are NumPy's
from lazy import lazy
from ndarray import NDArray, arange, array, array2, dot, greater, matmul, mean, sum_axis, total, zeros


def floats(seed: int, n: int) -> list[float]:
    out: list[float] = []
    s = seed
    for _ in range(n):
        s = (s * 1103515245 + 12345) % 2147483648
        out.append((s / 2147483648.0 - 0.5) * 100.0)
    return out


def show(what: str, a: NDArray) -> None:
    print(what, a.shape, a.values())


a = array2([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
b = array([10.0, 20.0, 30.0])
col = array2([[100.0], [200.0]])
cube = NDArray(floats(1, 24), [2, 3, 4], [12, 4, 1], 0)
show("a + b", a + b)
show("a - col", a - col)
show("a * a", a * a)
show("a / b", a / b)
show("a * 2.5", a * 2.5)
show("a - 1", a - 1)
show("-a", -a)
show("a.T", a.T)
show("a.T * a.T", a.T * a.T)
show("-a.T", -(a.T))
show("cube + a.row(0) as (3,1)", cube + a.row(0).reshape([3, 1]))
show("cube.T + 1", cube.T + 1.0)
show("cube.row(1)", cube.row(1))
show("cube.row(-1).row(2)", cube.row(-1).row(2))
show("a.reshape([3, 2])", a.reshape([3, 2]))
show("a.T.reshape([6])", a.T.reshape([6]))
print(a.contiguous(), a.T.contiguous(), a.ndim, a.size, len(a), a[1, 2], a[-1, -3], b[2], b[-3])
show("zeros", zeros([2, 2]))
show("arange", arange(5))
special = array([1.0, -1.0, 0.0, -0.0, float("inf"), float("-inf"), float("nan"), 2.5])
show("special / 0.0", special / 0.0)
show("special / -0.0", special / -0.0)
show("special / special", special / special)
show("special * special", special * special)
t = a.T
t[2, 1] = 60.0
print("t[2, 1] = 60:", a[1, 2], repr(a))

m = NDArray(floats(2, 35), [5, 7], [7, 1], 0)
for x in [m, m.T, cube.row(0)]:
    print("total", repr(total(x)), "mean", repr(mean(x)))
    show("sum axis 0", sum_axis(x, 0))
    show("sum axis 1", sum_axis(x, 1))
    show("sum axis -1", sum_axis(x, -1))
for n in [0, 1, 7, 8, 9, 127, 128, 129, 1000]:
    xs = floats(n + 3, n)
    print("total", n, repr(total(array(xs))), repr(mean(array(xs))) if n else "-")
print(repr(total(array([-0.0]))), repr(total(array([-0.0, -0.0]))), repr(mean(zeros([0]))))
u = array(floats(4, 50))
v = array(floats(5, 50))
print("dot", repr(dot(u, v)), repr(total(u * v)))
p = NDArray(floats(6, 12), [3, 4], [4, 1], 0)
q = NDArray(floats(7, 20), [4, 5], [5, 1], 0)
show("p @ q", p @ q)
show("matmul(q.T, p.T)", matmul(q.T, p.T))
print(greater(a, 3.0), greater(a.T, 3.0))

x = array(floats(8, 300))
y = array(floats(9, 300))
d = lazy(x) - lazy(y)
in_order = 0.0
for w in ((x - y) * (x - y)).values():
    in_order += w
print("lazy sum", repr((d * d).sum()), repr(in_order), repr(total((x - y) * (x - y))))
print("lazy evaluate", (lazy(x) * lazy(y) + 1.0).evaluate().values() == (x * y + 1.0).values())
print("lazy divide", ((lazy(x) - 2) / lazy(y)).evaluate().values() == ((x - 2) / y).values())
show("lazy of a row of a transpose", (lazy(a.T.row(1)) * 2.0).evaluate())
later = lazy(b) + lazy(b)
b.data[0] = 1.0
show("lazy reads the array when evaluated", later.evaluate())

for k in range(17):
    try:
        if k == 0:
            print(a + array([1.0, 2.0]))
        elif k == 1:
            print(a * col.T)
        elif k == 2:
            print(a.reshape([4]))
        elif k == 3:
            print(a[2, 0])
        elif k == 4:
            print(a[0, -4])
        elif k == 5:
            print(b[3])
        elif k == 6:
            print(b[0, 0])
        elif k == 7:
            print(a[0])
        elif k == 8:
            print(matmul(a, a))
        elif k == 9:
            print(dot(b, array([1.0])))
        elif k == 10:
            print(sum_axis(a, 2))
        elif k == 11:
            print(sum_axis(b, 0))
        elif k == 12:
            print(a.row(2))
        elif k == 13:
            print(lazy(a))
        elif k == 14:
            print(lazy(b) + lazy(array([1.0])))
        elif k == 15:
            print(array2([[1.0], [2.0, 3.0]]))
        else:
            print(len(NDArray([1.0], [], [], 0)))
    except (ValueError, IndexError, TypeError) as e:
        print(type(e).__name__, repr(str(e)))
