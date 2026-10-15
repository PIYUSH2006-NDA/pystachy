# error: closed union operations require narrowing with isinstance() first
def search(values: list[list[int] | list[str]], value: list[int]) -> bool:
    return value in values


values: list[list[int] | list[str]] = [[1], ["1"]]
print(search(values, [1]))
