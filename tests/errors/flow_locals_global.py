# error: expected str, got int
value = "3"
def f() -> int:
    global value
    value = int(value)
    return value
print(f())
