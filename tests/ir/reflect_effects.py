# Reflection's effects (reflection.py): reading a type's name loads it from the record of the
# object's exact class, which the class tag selects (a read of the object, rO, and of the record,
# a constant the analysis cannot tell from the heap); comparing types compares those records;
# hasattr() with a run-time name is one pys_refl_find, which reads only the record's name table;
# repr(vars(o)) is pys_refl_vars, which reads the object's fields and may run its fields' __repr__
# (U). reflect_effects.calls pins the runtime calls, reflect_effects.fx the summaries.
class Base:
    def __init__(self, x: int) -> None:
        self.x = x


class Derived(Base):
    def __init__(self, x: int) -> None:
        super().__init__(x)
        self.y = 2


def name_of(b: Base) -> str:
    return type(b).__name__


def same(a: Base, b: Base) -> bool:
    return type(a) == type(b)


def has(b: Base, n: str) -> bool:
    return hasattr(b, n)


def text(b: Base) -> str:
    return str(vars(b))


def read(b: Base) -> int:
    return getattr(b, "y", -1)


xs: list[Base] = [Base(1), Derived(2)]
for b in xs:
    print(name_of(b), same(b, xs[0]), has(b, "y"), text(b), read(b))
