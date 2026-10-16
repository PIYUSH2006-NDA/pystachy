"""lazy: elementwise expressions over 1-D NDArrays that compile to one loop.

usage: from lazy import lazy
       d = lazy(a) - lazy(b)
       (d * d).sum()                          # sum((a - b) * (a - b)), without temporaries
       (lazy(a) * lazy(b) + 1.0).evaluate()   # a new NDArray, made in one pass

An operator on lazy(...) operands or numbers returns a Node, whose class is specialized for its
operands' types and its operation (_node is a template, and so is every Node's __init__). An
expression's at() is therefore a nest of direct calls that LLVM inlines into one loop: the fusion
numexpr gets from a run-time virtual machine, and Eigen from C++ expression templates. A whole
array is read when the expression is evaluated, not when it is built; lazy() copies a view of part
of one, such as a row, and a strided view, such as a column.

evaluate() computes each item by the same IEEE operations as the eager expression (Pystachy never
contracts a * b + c into a fused multiply-add), so its array is NumPy's to the last bit. sum() adds
the items in order, where np.sum adds them pairwise. Operands are 1-D and of one length, or numbers.
"""
from ndarray import NDArray, ascontiguous, true_divide


def _add(x: float, y: float) -> float:
    return x + y


def _sub(x: float, y: float) -> float:
    return x - y


def _mul(x: float, y: float) -> float:
    return x * y


class Leaf:
    # an array operand: its whole list, or a copy of a view of part of one. Loops then run to
    # len(self.data), which lets LLVM drop the bounds checks of data[i] (with a length kept in a
    # field instead, the reduction below took 1.7 times as long)
    def __init__(self, a: NDArray) -> None:
        if a.ndim != 1:
            raise ValueError(f"lazy() takes a 1-D array, not a {a.ndim}-D one")
        c = ascontiguous(a)
        whole = c.offset == 0 and c.size == len(c.data)
        self.data: list[float] = c.data if whole else c.data[c.offset : c.offset + c.size]

    def at(self, i: int) -> float:
        return self.data[i]

    def size(self) -> int:
        return len(self.data)

    def __add__(self, other):
        return _node(self, _operand(other), _add)

    def __sub__(self, other):
        return _node(self, _operand(other), _sub)

    def __mul__(self, other):
        return _node(self, _operand(other), _mul)

    def __truediv__(self, other):
        return _node(self, _operand(other), true_divide)


class Scalar:
    # a number operand, the same at every index; its size, -1, fits any length
    def __init__(self, v: float) -> None:
        self.v = v

    def at(self, i: int) -> float:
        return self.v

    def size(self) -> int:
        return -1


class Node:
    def __init__(self, left, right, op) -> None:
        m = left.size()
        k = right.size()
        if m >= 0 and k >= 0 and m != k:
            raise ValueError(f"operands could not be broadcast together with shapes ({m},) ({k},) ")
        self.left = left
        self.right = right
        self.op = op

    def at(self, i: int) -> float:
        return self.op(self.left.at(i), self.right.at(i))

    def size(self) -> int:
        # a Leaf's or a Node's: a Scalar is only ever the right operand
        return self.left.size()

    def __add__(self, other):
        return _node(self, _operand(other), _add)

    def __sub__(self, other):
        return _node(self, _operand(other), _sub)

    def __mul__(self, other):
        return _node(self, _operand(other), _mul)

    def __truediv__(self, other):
        return _node(self, _operand(other), true_divide)

    def evaluate(self) -> NDArray:
        # the expression's items as a new array: one pass, one allocation
        n = self.size()
        return NDArray([self.at(i) for i in range(n)], [n], [1], 0)

    def sum(self) -> float:
        # the items added in order from 0.0, as a loop over them adds them. np.sum adds pairwise, so
        # the last digits can differ; ndarray.total() of the eager expression gives np.sum's result.
        # (A fused sum in NumPy's pairwise order ran 3 times as long as this one: README.md.)
        s = 0.0
        for i in range(self.size()):
            s += self.at(i)
        return s


def lazy(a: NDArray) -> Leaf:
    return Leaf(a)


def _node(left, right, op):
    # a module-level template, so that each call builds the specialization of Node for its argument
    # types (inside Node's methods, Node would name the current specialization)
    return Node(left, right, op)


def _operand(v):
    # a template: a number becomes a Scalar, an expression stays as it is (arrays need lazy(): a
    # test of isinstance(v, NDArray) would not be decided at compile time, since an object may be None)
    if isinstance(v, float) or isinstance(v, int):
        return Scalar(float(v))
    return v
