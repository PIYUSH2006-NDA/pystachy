# error: percent_runtime_format_opt.py:3: error: % formatting with a format string computed at run time is not supported (only of a string literal, "%d" % x, or of a module global that one assignment binds to one)
def f(fmt: str | None) -> str:
    return fmt % 3


print(f("%d"))
