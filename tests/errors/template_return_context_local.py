# error: expected int, got float
def indirect(a, b):
    result = [a, b]
    return result


result: list[int | float] = indirect(1, 2.5)
