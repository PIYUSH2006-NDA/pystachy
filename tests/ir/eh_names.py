# A program turns exception handling on (pys_eh_on in @main) when it may catch an exception: a
# try or with, a read of the builtin iter (whose iterator objects' __next__ a loop catches), or
# a __next__ that a loop over an object with __iter__ or next(it, default) may call. A parameter,
# a lambda's parameter or an attribute named iter, and a __next__ only called directly, with no
# __iter__ in the program and its own next(), are none of these: eh_names.calls pins @main
# without pys_eh_on. (eh_global.py: a module-level iter.)


class Node:
    def __init__(self) -> None:
        self.iter = 3

    def __next__(self) -> int:
        return self.iter


def next(n: Node) -> int:
    return n.__next__()


def bump(iter: int) -> int:
    inner = lambda: iter + 1
    return inner()


shift = lambda iter: iter * 2
print(bump(2), shift(3), Node().iter, next(Node()))
