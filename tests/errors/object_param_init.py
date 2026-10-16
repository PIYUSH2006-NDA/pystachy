# error: object_param_init.py:5: error: unsupported type annotation
# A parameter annotated object is a template's (each call types it), which __init__, whose
# parameters type the fields it assigns, cannot be: an object type of any value is not supported
class Holder:
    def __init__(self, value: object) -> None:
        self.value = value


print(Holder(1).value)
