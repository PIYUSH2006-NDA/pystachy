# error: expected str, got int
def f() -> int:
    value = "3"
    read = lambda: value
    value = int(value)
    print(read())
    return value
print(f())
