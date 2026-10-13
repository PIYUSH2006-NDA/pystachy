# class templates in an imported module: each object's specialization is made where the program
# makes it, and one that cannot be made (Never) is an error only where the program makes one


class Cell:
    def __init__(self, v, label="c"):
        self.v = v
        self.label = label

    def get(self):
        return self.v

    def relabel(self, label):
        return Cell(self.v, label)

    @staticmethod
    def of(v) -> "Cell":
        return Cell(v, "of")

    def __repr__(self) -> str:
        return f"Cell({self.v!r}, {self.label})"


class Never:
    def __init__(self, v):
        self.v = None


def make(v):
    return Cell(v)


def boxed(n: int) -> Cell:
    # (an annotation that names a class template, as Cell does, types nothing: what boxed()
    # returns is one of Cell's specializations, as in the main program)
    return Cell(n, "b")


def labels(*cells: Cell, **named: "Cell") -> list[str]:
    return [c.label for c in cells] + [k + "=" + c.label for k, c in named.items()]
