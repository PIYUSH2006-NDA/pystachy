ROW = "{:<6}|{:>4}"
TITLE: str = "== {title} =="


def row(name: str, n: int) -> str:
    return ROW.format(name, n)


def late(n: int) -> str:
    return LATE.format(n)


try:
    print(late(1))
except NameError as e:
    print("NameError:", e)
LATE = "<{}>"
print(late(2))
