# error: expected str, got int
def f() -> int:
    value = "3"
    try:
        value = int(value)
    except ValueError:
        print(value)
    return value
print(f())
