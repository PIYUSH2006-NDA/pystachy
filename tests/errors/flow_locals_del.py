# error: expected str, got int
def f() -> int:
    value = "3"
    del value
    value = 3
    return value
print(f())
