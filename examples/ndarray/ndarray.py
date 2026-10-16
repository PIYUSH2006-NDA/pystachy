"""ndarray: a float64 n-dimensional array in typed Python, after NumPy's ndarray.

usage: from ndarray import NDArray, array, array2, arange, zeros, total, sum_axis, matmul

An NDArray is a flat list[float] with a shape, element strides and an offset, so a transpose, a row
and a reshape of contiguous data are views of the same list, as NumPy's are. Arithmetic with
another array or a number broadcasts as NumPy does and makes a new contiguous array; division by
zero gives NumPy's inf and nan. total(), mean() and sum_axis() add in NumPy's order, its pairwise
summation for a contiguous axis, so they give np.sum's results to the last bit.

The subset has no slice objects, reflected operators or comparison methods that return arrays:
a[1:3], 2.0 * a and a > x are written a.row(i), a * 2.0 and greater(a, x) here. a[i, j] = v
needs a 2-D array (__setitem__ cannot be a template). See README.md.
"""
import math


def _prod(xs: list[int]) -> int:
    n = 1
    for x in xs:
        n *= x
    return n


def _cstrides(shape: list[int]) -> list[int]:
    # the element strides of a C-order (row-major) array of this shape
    st = [0] * len(shape)
    acc = 1
    k = len(shape) - 1
    while k >= 0:
        st[k] = acc
        acc *= shape[k]
        k -= 1
    return st


def _shape_str(shape: list[int]) -> str:
    # a shape as NumPy's messages write it: (3,) or (2,3)
    if len(shape) == 1:
        return f"({shape[0]},)"
    return "(" + ",".join([str(d) for d in shape]) + ")"


def _index(i: int, n: int, axis: int) -> int:
    # i along an axis of n items, from either end, with NumPy's IndexError
    if i < -n or i >= n:
        raise IndexError(f"index {i} is out of bounds for axis {axis} with size {n}")
    return i + n if i < 0 else i


class NDArray:
    def __init__(self, data: list[float], shape: list[int], strides: list[int], offset: int) -> None:
        self.data = data
        self.shape = shape
        self.strides = strides
        self.offset = offset

    @property
    def ndim(self) -> int:
        return len(self.shape)

    @property
    def size(self) -> int:
        return _prod(self.shape)

    def contiguous(self) -> bool:
        return self.strides == _cstrides(self.shape)

    @property
    def T(self) -> "NDArray":
        # the transpose: a view with the axes reversed
        return NDArray(self.data, self.shape[::-1], self.strides[::-1], self.offset)

    def reshape(self, shape: list[int]) -> "NDArray":
        # a view of contiguous data, otherwise of a contiguous copy, as NumPy copies only when it must
        if _prod(shape) != self.size:
            raise ValueError(f"cannot reshape array of size {self.size} into shape {_shape_str(shape)}")
        src = ascontiguous(self)
        return NDArray(src.data, list(shape), _cstrides(shape), src.offset)

    def row(self, i: int) -> "NDArray":
        # a[i]: a view of one index along the first axis
        i = _index(i, self.shape[0], 0)
        return NDArray(self.data, self.shape[1:], self.strides[1:], self.offset + i * self.strides[0])

    def _pos(self, i: int, j: int) -> int:
        # the data index of a[i, j]
        if self.ndim != 2:
            raise IndexError(f"too many indices for array: array is {self.ndim}-dimensional, but 2 were indexed")
        return self.offset + _index(i, self.shape[0], 0) * self.strides[0] + _index(j, self.shape[1], 1) * self.strides[1]

    def __getitem__(self, key):
        # a template: a[i] of a 1-D array, a[i, j] of a 2-D one (a row of a 2-D array is a.row(i))
        if isinstance(key, int):
            if self.ndim != 1:
                raise IndexError(f"a[i] of a {self.ndim}-dimensional array is a view: use a.row(i)")
            return self.data[self.offset + _index(key, self.shape[0], 0) * self.strides[0]]
        return self.data[self._pos(key[0], key[1])]

    def __setitem__(self, key: tuple[int, int], v: float) -> None:
        # a[i, j] = v, also through a view: the data is shared
        self.data[self._pos(key[0], key[1])] = v

    def __len__(self) -> int:
        if self.ndim == 0:
            raise TypeError("len() of unsized object")
        return self.shape[0]

    def __add__(self, other):
        return _binary(self, _as_array(other), _add)

    def __sub__(self, other):
        return _binary(self, _as_array(other), _sub)

    def __mul__(self, other):
        return _binary(self, _as_array(other), _mul)

    def __truediv__(self, other):
        return _binary(self, _as_array(other), true_divide)

    def __neg__(self) -> "NDArray":
        return _unary(self, _neg)

    def __matmul__(self, other: "NDArray") -> "NDArray":
        return matmul(self, other)

    def values(self) -> list[float]:
        # the items in C order, as a.ravel().tolist() gives them
        c = ascontiguous(self)
        return c.data[c.offset : c.offset + c.size]

    def __repr__(self) -> str:
        # not NumPy's repr: the items in C order, then the shape
        return f"array({self.values()}, shape={_shape_str(self.shape)})"


def _add(x: float, y: float) -> float:
    return x + y


def _sub(x: float, y: float) -> float:
    return x - y


def _mul(x: float, y: float) -> float:
    return x * y


def _neg(x: float) -> float:
    return -x


def _same(x: float) -> float:
    return x


def true_divide(x: float, y: float) -> float:
    # x / y as NumPy divides float64s: inf, -inf or nan for a zero y (NumPy also warns), where
    # Python's float division raises ZeroDivisionError
    if y == 0.0:
        if x == 0.0 or x != x:
            return math.nan
        return math.copysign(math.inf, x) * math.copysign(1.0, y)
    return x / y


def _as_array(v):
    # a template: a float or an int becomes a 0-d array, an NDArray stays as it is. (A test of
    # isinstance(v, NDArray) first would not be decided at compile time: an object may be None.)
    if isinstance(v, float) or isinstance(v, int):
        return NDArray([float(v)], [], [], 0)
    return v


def array(xs: list[float]) -> NDArray:
    return NDArray(list(xs), [len(xs)], [1], 0)


def array2(rows: list[list[float]]) -> NDArray:
    n = len(rows[0]) if rows else 0
    data: list[float] = []
    for r in rows:
        if len(r) != n:
            raise ValueError(f"rows of different lengths: {len(r)} and {n}")
        data.extend(r)
    return NDArray(data, [len(rows), n], [n, 1], 0)


def zeros(shape: list[int]) -> NDArray:
    return NDArray([0.0] * _prod(shape), list(shape), _cstrides(shape), 0)


def arange(n: int) -> NDArray:
    return NDArray([float(i) for i in range(n)], [n], [1], 0)


def ascontiguous(a: NDArray) -> NDArray:
    # a itself if it is C-contiguous, otherwise a contiguous copy
    if a.contiguous():
        return a
    return _unary(a, _same)


def _broadcast_shapes(a: list[int], b: list[int]) -> list[int]:
    # NumPy's broadcasting: shapes align at their last axes, and an axis of 1 repeats
    n = max(len(a), len(b))
    out: list[int] = []
    for k in range(n):
        ka = len(a) - n + k
        kb = len(b) - n + k
        da = a[ka] if ka >= 0 else 1
        db = b[kb] if kb >= 0 else 1
        if da == db or db == 1:
            out.append(da)
        elif da == 1:
            out.append(db)
        else:
            raise ValueError(f"operands could not be broadcast together with shapes {_shape_str(a)} {_shape_str(b)} ")
    return out


def _bstrides(a: NDArray, shape: list[int]) -> list[int]:
    # a's element strides against a broadcast shape: 0 along the axes where a repeats
    n = len(shape)
    st = [0] * n
    for k in range(n):
        j = len(a.shape) - n + k
        if j >= 0 and a.shape[j] != 1:
            st[k] = a.strides[j]
    return st


def _unary(a: NDArray, op) -> NDArray:
    # a template on op, as _binary is
    shape = list(a.shape)
    if a.contiguous():
        d = a.data
        o = a.offset
        return NDArray([op(d[o + i]) for i in range(a.size)], shape, _cstrides(shape), 0)
    return _binary(a, NDArray([0.0], [], [], 0), _first(op))


def _first(op):
    def f(x: float, y: float) -> float:
        return op(x)

    return f


def _binary(a: NDArray, b: NDArray, op) -> NDArray:
    # a template on op: each operation gets its own specialization, in which op() is a direct call
    # that LLVM inlines into the loop
    shape = _broadcast_shapes(a.shape, b.shape)
    n = _prod(shape)
    ad = a.data
    bd = b.data
    ao = a.offset
    bo = b.offset
    if a.shape == shape and a.contiguous():
        if b.shape == shape and b.contiguous():
            return NDArray([op(ad[ao + i], bd[bo + i]) for i in range(n)], shape, _cstrides(shape), 0)
        if b.size == 1:
            y = bd[bo]
            return NDArray([op(ad[ao + i], y) for i in range(n)], shape, _cstrides(shape), 0)
    nd = len(shape)
    out: list[float] = []
    if n == 0:
        return NDArray(out, shape, _cstrides(shape), 0)
    if nd == 0:
        out.append(op(ad[ao], bd[bo]))
        return NDArray(out, shape, [], 0)
    # the last axis is the inner loop; the others advance like an odometer
    sa = _bstrides(a, shape)
    sb = _bstrides(b, shape)
    inner = shape[nd - 1]
    ia = sa[nd - 1]
    ib = sb[nd - 1]
    idx = [0] * nd
    pa = ao
    pb = bo
    for _ in range(n // inner):
        for j in range(inner):
            out.append(op(ad[pa + j * ia], bd[pb + j * ib]))
        k = nd - 2
        while k >= 0:
            idx[k] += 1
            pa += sa[k]
            pb += sb[k]
            if idx[k] < shape[k]:
                break
            pa -= sa[k] * shape[k]
            pb -= sb[k] * shape[k]
            idx[k] = 0
            k -= 1
    return NDArray(out, shape, _cstrides(shape), 0)


def pairwise(d: list[float], lo: int, n: int) -> float:
    # NumPy's pairwise summation of d[lo:lo + n] (numpy/_core/src/umath/loops_utils.h.src): eight
    # accumulators over blocks of up to 128 items, halves of larger runs added recursively. The
    # same additions in the same order round the same way.
    if n < 8:
        res = -0.0
        for i in range(lo, lo + n):
            res += d[i]
        return res
    if n <= 128:
        r0 = d[lo]
        r1 = d[lo + 1]
        r2 = d[lo + 2]
        r3 = d[lo + 3]
        r4 = d[lo + 4]
        r5 = d[lo + 5]
        r6 = d[lo + 6]
        r7 = d[lo + 7]
        m = n - n % 8
        i = 8
        while i < m:
            p = lo + i
            r0 += d[p]
            r1 += d[p + 1]
            r2 += d[p + 2]
            r3 += d[p + 3]
            r4 += d[p + 4]
            r5 += d[p + 5]
            r6 += d[p + 6]
            r7 += d[p + 7]
            i += 8
        res = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))
        while i < n:
            res += d[lo + i]
            i += 1
        return res
    n2 = n // 2
    n2 -= n2 % 8
    return pairwise(d, lo, n2) + pairwise(d, lo + n2, n - n2)


def _dense(a: NDArray) -> bool:
    # whether a's items fill data[offset:offset + size] in some order of its axes, as those of a C- or
    # an F-ordered array (a transpose) do
    acc = 1
    for k in sorted(range(a.ndim), key=lambda j: a.strides[j]):
        if a.shape[k] != 1 and a.strides[k] != acc:
            return False
        acc *= a.shape[k]
    return True


def total(a: NDArray) -> float:
    # np.sum(a). NumPy adds a dense array's items in memory order, and starts at 0.0, so the sum of
    # [-0.0] is 0.0. (For other 2-D views it adds run by run in memory order; this adds them in C
    # order, so the last digits can differ there.)
    if _dense(a):
        return 0.0 + pairwise(a.data, a.offset, a.size)
    c = ascontiguous(a)
    return 0.0 + pairwise(c.data, c.offset, c.size)


def mean(a: NDArray) -> float:
    # np.mean(a): the sum divided by the count (nan for an empty array, where NumPy also warns)
    return true_divide(total(a), float(a.size))


def sum_axis(a: NDArray, axis: int) -> NDArray:
    # np.sum(a, axis=axis) of a 2-D array. NumPy's loop runs along the axis whose items lie closer
    # in memory: if that is the summed axis, it adds each line of it pairwise; otherwise it adds the
    # lines across it one after another, from 0.0.
    if a.ndim != 2:
        raise ValueError(f"sum_axis takes a 2-D array, not a {a.ndim}-D one")
    k = axis + 2 if axis < 0 else axis
    if k != 0 and k != 1:
        raise ValueError(f"axis {axis} is out of bounds for array of dimension 2")
    o = 1 - k
    n = a.shape[k]
    sk = a.strides[k]
    if sk <= a.strides[o]:
        out: list[float] = []
        for i in range(a.shape[o]):
            base = a.offset + i * a.strides[o]
            line = a.data[base : base + n] if sk == 1 else [a.data[base + t * sk] for t in range(n)]
            out.append(0.0 + pairwise(line, 0, n))
        return array(out)
    acc = zeros([a.shape[o]])
    for i in range(n):
        acc = acc + NDArray(a.data, [a.shape[o]], [a.strides[o]], a.offset + i * sk)
    return acc


def dot(a: NDArray, b: NDArray) -> float:
    # the inner product of two 1-D arrays, as np.sum(a * b) adds it (np.dot's BLAS kernel adds in
    # another order, so the last digits can differ)
    if a.ndim != 1 or b.ndim != 1 or a.shape[0] != b.shape[0]:
        raise ValueError(f"shapes {_shape_str(a.shape)} and {_shape_str(b.shape)} not aligned")
    return total(a * b)


def matmul(a: NDArray, b: NDArray) -> NDArray:
    # a @ b of 2-D arrays: rows of a times b, accumulated row by row (BLAS adds in blocks, so the
    # last digits can differ from NumPy's)
    if a.ndim != 2 or b.ndim != 2:
        raise ValueError("matmul takes 2-D arrays here")
    if a.shape[1] != b.shape[0]:
        raise ValueError(
            "matmul: Input operand 1 has a mismatch in its core dimension 0, with gufunc signature "
            + f"(n?,k),(k,m?)->(n?,m?) (size {b.shape[0]} is different from {a.shape[1]})"
        )
    m = a.shape[0]
    k = a.shape[1]
    n = b.shape[1]
    ac = ascontiguous(a)
    bc = ascontiguous(b)
    A = ac.data
    B = bc.data
    rows = [B[bc.offset + p * n : bc.offset + (p + 1) * n] for p in range(k)]
    C: list[float] = []
    for i in range(m):
        crow = [0.0] * n
        base = ac.offset + i * k
        for p in range(k):
            aip = A[base + p]
            brow = rows[p]
            for j in range(n):
                crow[j] += aip * brow[j]
        C.extend(crow)
    return NDArray(C, [m, n], [n, 1], 0)


def greater(a: NDArray, x: float) -> list[bool]:
    # (a > x).ravel().tolist(): comparison methods return bool in the subset, so no __gt__ here
    return [v > x for v in a.values()]
