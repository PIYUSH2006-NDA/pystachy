# error: list[int] in a closed union is not supported

def unsupported(value: list[int] | str) -> int:
    return 0

print(unsupported("a"))
