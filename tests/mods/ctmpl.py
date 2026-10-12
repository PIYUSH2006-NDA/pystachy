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

    def __repr__(self) -> str:
        return f"Cell({self.v!r}, {self.label})"


class Never:
    def __init__(self, v):
        self.v = None


def make(v):
    return Cell(v)
