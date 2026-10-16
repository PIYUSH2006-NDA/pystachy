# ndarray: a float64 array in typed Python

A small NumPy-style array written in the typed subset, to measure how far Pystachy gets with array
code. [`ndarray.py`](ndarray.py) has views (transposes, rows and reshapes share their data),
NumPy's broadcasting, arithmetic with arrays and numbers, reductions in NumPy's order and a matrix
product. [`lazy.py`](lazy.py) builds elementwise expressions whose evaluation compiles to one loop,
without temporary arrays. Both are plain Python: CPython runs them too, which lets
[`check_numpy.py`](check_numpy.py) compare them with NumPy.

## Run

From this directory, with the built `pystachy` command on `PATH`:

```sh
python3 demo.py
pystachy run demo.py
pystachy build demo.py -o demo
./demo
```

```
a + b        array([11.0, 22.0, 33.0, 14.0, 25.0, 36.0], shape=(2,3))
a.T          array([1.0, 4.0, 2.0, 5.0, 3.0, 6.0], shape=(3,2))
a * 2 - 1    array([1.0, 3.0, 5.0, 7.0, 9.0, 11.0], shape=(2,3))
a @ a.T      array([14.0, 32.0, 32.0, 77.0], shape=(2,2))
a[1, 2]      6.0 a.row(1): array([4.0, 5.0, 6.0], shape=(3,))
sum axis 0   array([5.0, 7.0, 9.0], shape=(3,)) axis 1: array([6.0, 15.0], shape=(2,))
total, mean  21.0 3.5
a > 2.5      [False, False, True, True, True, True]
1 / [1 -1 0] array([inf, -inf, nan], shape=(3,))
t[0, 1] = 40 writes a[1, 0]: 40.0
ValueError: 'operands could not be broadcast together with shapes (2,3) (2,) '
sum((x - y) * (x - y)): fused 42453252.55102041 eager 42453252.551020406
x * y + 1 fused == eager: True
```

CPython, the JIT and the executable print the same. `repr()` lists the items in C order and the
shape; it is not NumPy's format.

## Agreement with NumPy

```sh
python3 check_numpy.py
```

```
88 checks equal NumPy's to the last bit, 5 within 1e-12 (numpy 2.5.3)
```

- **Bit for bit:** elementwise arithmetic, broadcasting, views and `lazy`'s `evaluate()` give
  NumPy's float64 results, signed zeros, infinities and NaNs included. Division by zero gives
  NumPy's `inf` and `nan`, not Python's `ZeroDivisionError`.
- **Reductions in NumPy's order:** `total()`, `mean()` and `sum_axis()` add as NumPy does, so they
  match bit for bit. NumPy adds pairwise along the axis that is contiguous in memory, and item after
  item across the other.
- **BLAS order:** `dot()` is `np.sum(a * b)` exactly. `np.dot` and `@` call BLAS, which adds in other
  orders, so `dot()` and `matmul()` agree with them within 1e-12 relative.
- **In order:** `lazy`'s `sum()` adds the items in order, as a hand-written loop does; it agrees with
  `np.sum`'s pairwise result within 1e-12 relative (see below).
- **Errors:** broadcasting, `reshape`, indexing and `matmul` raise with NumPy's messages.

## Recorded benchmark

```sh
python3 -I bench.py pystachy
```

A single run on a shared 4-vCPU x86-64 VM (Xeon, 2.8 GHz), compiler at
[`2379159`](https://github.com/den-run-ai/pystachy/commit/2379159), LLVM 18.1.3,
CPython 3.13.16 and NumPy 2.5.3. NumPy is single-threaded (`OPENBLAS_NUM_THREADS=1`), as Pystachy
is. Times are the best of five inside each process, in milliseconds, so the JIT's exclude its
compilation. `a` and `b` have 4,000,000 items.

| Workload | AOT | JIT | NumPy |
|---|---:|---:|---:|
| `a + b` | 42.3 | 55.3 | 9.3 |
| `a * 1.5` | 42.7 | 48.6 | 4.9 |
| `a * b + a` | 88.5 | 98.1 | 22.2 |
| `a * b + a`, lazy | 37.7 | 43.4 | — |
| `sum(a)` | 4.9 | 7.8 | 2.7 |
| `sum((a - b) * (a - b))` | 133.0 | 186.3 | 40.4 |
| `sum((a - b) * (a - b))`, lazy | **6.5** | 24.1 | — |
| `m + row`, 1000×1000 | 5.4 | 16.1 | 1.0 |
| `m.T + m`, 1000×1000 | 7.5 | 22.0 | 1.8 |
| `p @ q`, 256×256 | 15.7 | 58.3 | 0.7 |

- **Fusion wins.** The lazy `sum((a - b) * (a - b))` makes no array: one loop at about 1.6 ns per
  item, 6.2 times faster than NumPy's eager expression. NumPy allocates and fills two temporary
  arrays for it.
- **New arrays are the cost.** An operation that makes an array takes 3 to 9 times NumPy's time.
  The loops themselves run at C's speed, but numeric lists are scanned by the collector
  ([#210](https://github.com/den-run-ai/pystachy/issues/210)) and each result takes fresh memory,
  where NumPy reuses freed buffers. The lazy `a * b + a` still makes its result.
- **The JIT inlines less** than the executable's whole-program `-O2`
  ([#209](https://github.com/den-run-ai/pystachy/issues/209)).
- **Matrix products need BLAS.** The compiled loop reaches about 2 GFLOP/s, NumPy's OpenBLAS 49.
- **Pairwise order costs extra.** A fused sum in NumPy's pairwise order ran 5.0 ns per item, in each
  of the three forms tried, against 1.6 for this one, so `lazy` adds in order. The follow-up issue
  below has the causes found in the optimized IR.

## What the subset cannot express yet

| NumPy | Here | Why |
|---|---|---|
| `a[1:3]`, `a[:, j]` | `a.row(i)` | No slice objects ([#501](https://github.com/den-run-ai/pystachy/issues/501)) |
| `2.0 * a`, `1 - a` | `a * 2.0` | No reflected operators ([#113](https://github.com/den-run-ai/pystachy/issues/113)) |
| `a > x`, a boolean mask | `greater(a, x)`, a `list[bool]` | Comparison methods must return `bool` |
| `a[i]`, a row of a 2-D array | `a.row(i)` | `__getitem__` returns one type for each key type |
| `a[i] = v` of a 1-D array | — | `__setitem__` cannot be a template, so it takes only `tuple[int, int]` |
| `lazy(a) * b`, `b` an array | `lazy(a) * lazy(b)` | Compile time cannot decide `isinstance(b, NDArray)`: an object may be `None` |
| float32, int8 and other dtypes | float64 only | No narrower scalars or packed numeric buffers |

Native numeric buffers, optional BLAS and NumKong kernels and NumPy interoperability are tracked
in [#582](https://github.com/den-run-ai/pystachy/issues/582), with measurements.
