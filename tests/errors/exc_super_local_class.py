# error: exc_super_local_class.py:5: error: super() is only supported without arguments, in the methods of exception classes
class E(ValueError):
    def __init__(self, m: str):
        # E is a local here, not the class: CPython raises UnboundLocalError
        super(E, self).__init__(m)
        E = 5
        print(E)


print(E("x"))
