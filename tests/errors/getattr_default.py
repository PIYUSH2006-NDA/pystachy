# error: getattr_default.py:8: error: getattr() is supported with two arguments, the second a str literal
# getattr() with a default would return either the attribute or the default
class C:
    def __init__(self) -> None:
        self.a = 1


print(getattr(C(), "b", 0))
