# error: exc_super_cls.py:6: error: super() is only supported without arguments, in the methods of exception classes
class E(ValueError):
    @classmethod
    def name(cls) -> str:
        # a class method that takes cls alone: CPython raises TypeError (__str__ needs an object)
        return super(E, cls).__str__()


print(E.name())
