class Pair:
    def __init__(self, x: int) -> None:
        self.x = x

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Pair) and other.x == self.x

    def __repr__(self) -> str:
        return f"Pair({self.x})"


class Key(Pair):
    def __hash__(self) -> int:
        return self.x


def same(a: object, b: object) -> bool:
    return a is b
