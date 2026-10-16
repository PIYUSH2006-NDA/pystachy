__doc__: str = "annotated"  # (no docstring: a variable of its own, which a function rebinds)


def retitle() -> str:
    global __doc__
    __doc__ = "retitled"
    return __doc__
