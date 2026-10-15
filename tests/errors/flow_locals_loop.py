# error: expected str, got int
def f() -> int:
    value = "3"
    for i in range(1):
        value = int(value)
    return value
print(f())
