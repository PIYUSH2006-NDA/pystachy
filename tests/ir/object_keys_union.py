# a | b and dict(pairs) of dicts whose keys are objects: hashed by their class, they run its
# __hash__ and __eq__ (U, as d.update() does), hashed by identity, none of the program's code


class Node:
    pass


class Hashed:
    def __init__(self, v: int) -> None:
        self.v = v

    def __eq__(self, other: "Hashed") -> bool:
        return self.v == other.v

    def __hash__(self) -> int:
        return self.v


def hashed_or(a: dict[Hashed, int], b: dict[Hashed, int]) -> int:
    return len(a | b)


def hashed_pairs(ps: list[tuple[Hashed, int]]) -> int:
    return len(dict(ps))


def node_or(a: dict[Node, int], b: dict[Node, int]) -> int:
    return len(a | b)


def node_pairs(ps: list[tuple[Node, int]]) -> int:
    return len(dict(ps))


print(hashed_or({Hashed(1): 1}, {Hashed(2): 2}), hashed_pairs([(Hashed(1), 1)]))
print(node_or({Node(): 1}, {Node(): 2}), node_pairs([(Node(), 1)]))
