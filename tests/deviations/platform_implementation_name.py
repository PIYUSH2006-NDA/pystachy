# Documented deviation: sys.implementation.name is "pystachy", not CPython's "cpython", and a test
# of it is decided at compile time, so the branch for CPython is not compiled
import sys

print(sys.implementation.name)
if sys.implementation.name == "cpython":
    print("CPython")
else:
    print("not CPython")
