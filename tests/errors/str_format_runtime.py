# error: str_format_runtime.py:5: error: str.format() of a format string computed at run time is not supported (only of a string literal, "{}".format(...), or of a module global that one assignment binds to one)
# fmt.format(x) where fmt is known only when it runs: CPython reads whatever fmt holds, while
# Pystachy compiles the fields of a literal format
def f(fmt: str, x: int) -> str:
    return fmt.format(x)


print(f("{:>4}", 1))
