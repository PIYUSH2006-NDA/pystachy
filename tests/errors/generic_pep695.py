# error: generic classes (class C[T]) are not supported: write class C(Generic[T]), with T = TypeVar("T")
class Box[T]:
    def __init__(self, item: T) -> None:
        self.item = item


print(Box(1).item)
