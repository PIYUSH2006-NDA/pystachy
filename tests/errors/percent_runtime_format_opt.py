# error: percent_runtime_format_opt.py:3: error: % formatting with a format string computed at run time is not supported (only a string literal: "%d" % x)
def f(fmt: str | None) -> str:
    return fmt % 3


print(f("%d"))
