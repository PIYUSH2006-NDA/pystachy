# error: expected str, got int
def f() -> int:
    value = "3"
    def read() -> str:
        return value
    value = int(value)
    print(read())
    return value
print(f())
