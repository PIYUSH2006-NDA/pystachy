# error: getattr_variable_name.py:9: error: getattr() is supported with two arguments, the second a str literal
# An attribute's name known only at run time would need dynamic attribute access
class C:
    def __init__(self) -> None:
        self.a = 1


name = "a"
print(getattr(C(), name))
