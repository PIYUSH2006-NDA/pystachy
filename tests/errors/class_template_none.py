# error: class_template_none.py:5: error: cannot infer the type of field 'v'; annotate it (self.v: T = ...) (specializing Box(None) for the call at tests/errors/class_template_none.py:8)
# a field given None: no specialization types it (another call's T | None needs unions)
class Box:
    def __init__(self, v):
        self.v = v


b = Box(None)
print(b.v)
