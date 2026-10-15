# error: comparing closed union values requires narrowing with isinstance() first
def compare(a: list[int] | list[str], b: list[int] | list[str]) -> bool:
    return a == b


print(compare([1], ["1"]))
