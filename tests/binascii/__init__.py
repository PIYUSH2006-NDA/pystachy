# (tests/lib_binascii_shadow.py) Never imported: binascii is built into CPython, which imports its
# own module rather than this package, and so does Pystachy (its stand-in, lib/_pystachy_binascii.py)
raise ImportError("tests/binascii was imported in place of the binascii module")
