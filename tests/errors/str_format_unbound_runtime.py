# error: str_format_unbound_runtime.py:4: error: str.format() of a format string computed at run time is not supported (only of a string literal, "{}".format(...), or of a module global that one assignment binds to one)
# str.format(fmt, ...) through the class, of a format string known only when it runs
def show(fmt: str, x: int) -> str:
    return str.format(fmt, x)


print(show("{:>4}", 1))
