# error: isinstance_none_import.py:6: error: cannot infer the type of 'x' from None here, before a value of another type is assigned to it; annotate it (x: T | None)
# The import rebinds x on the loop's second pass: CPython prints True, then False.
def f() -> None:
    x = None
    for i in range(2):
        print(isinstance(x, type(None)))
        import sys as x


f()
