# error: expected str, got int
def f(flag: bool) -> int:
    value = "3"
    if flag:
        value = int(value)
    return value
print(f(True))
