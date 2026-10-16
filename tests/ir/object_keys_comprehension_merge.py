# a dict comprehension (#472) and a dict display with ** (#479) of objects as keys (#484): hashed
# by their class, the stores run its __hash__ and __eq__ (U, as d[k] = v does), hashed by
# identity, none of the program's code


class Node:
    pass


class Hashed:
    def __init__(self, v: int) -> None:
        self.v = v

    def __eq__(self, other: "Hashed") -> bool:
        return self.v == other.v

    def __hash__(self) -> int:
        return self.v


def hashed_comp(xs: list[Hashed]) -> int:
    return len({x: 1 for x in xs})


def hashed_merge(a: dict[Hashed, int], b: dict[Hashed, int]) -> int:
    return len({**a, **b})


def node_comp(xs: list[Node]) -> int:
    return len({x: 1 for x in xs})


def node_merge(a: dict[Node, int], b: dict[Node, int]) -> int:
    return len({**a, **b})


print(hashed_comp([Hashed(1), Hashed(1)]), hashed_merge({Hashed(1): 1}, {Hashed(1): 2}))
print(node_comp([Node(), Node()]), node_merge({Node(): 1}, {Node(): 2}))
