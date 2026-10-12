# error: parameter 'x' of '__init__' needs a type annotation
class A:
    def __init__(self, x) -> None:
        self.x = x

    def m(self, y):
        return self.x + y


print(A(1).m(2))
