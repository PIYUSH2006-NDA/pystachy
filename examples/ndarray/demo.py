"""demo: ndarray's views, broadcasting and reductions, and a lazy expression fused into one loop.

usage: python3 demo.py
       pystachy run demo.py
       pystachy build demo.py -o demo && ./demo

CPython and the compiled program print the same lines; check_numpy.py compares them with NumPy.
"""
from lazy import lazy
from ndarray import arange, array, array2, greater, matmul, mean, sum_axis, total

a = array2([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
b = array([10.0, 20.0, 30.0])
print("a + b       ", a + b)
print("a.T         ", a.T)
print("a * 2 - 1   ", a * 2.0 - 1)
print("a @ a.T     ", matmul(a, a.T))
print("a[1, 2]     ", a[1, 2], "a.row(1):", a.row(1))
print("sum axis 0  ", sum_axis(a, 0), "axis 1:", sum_axis(a, 1))
print("total, mean ", total(a), mean(a))
print("a > 2.5     ", greater(a, 2.5))
print("1 / [1 -1 0]", array([1.0, -1.0, 0.0]) / 0.0)
t = a.T
t[0, 1] = 40.0
print("t[0, 1] = 40 writes a[1, 0]:", a[1, 0])
try:
    print(a + array([1.0, 2.0]))
except ValueError as e:
    print("ValueError:", repr(str(e)))

x = arange(1000) / 7.0
y = arange(1000) * 0.5
d = lazy(x) - lazy(y)
print("sum((x - y) * (x - y)): fused", (d * d).sum(), "eager", total((x - y) * (x - y)))
print("x * y + 1 fused == eager:", (lazy(x) * lazy(y) + 1.0).evaluate().values() == (x * y + 1.0).values())
