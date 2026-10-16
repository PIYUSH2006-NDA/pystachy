# Documented deviations of lib/collections' deque (Pystachy's own) from CPython's.
from collections import deque
from collections.abc import MutableSequence, Sequence

# maxlen is a plain field, which an assignment changes: CPython's is read-only (AttributeError).
d = deque([1, 2, 3])
d.maxlen = 2
print(d.maxlen)

# CPython registers deque as a collections.abc.MutableSequence; isinstance() finds Pystachy's no
# Sequence: CPython prints True True.
print(isinstance(d, Sequence), isinstance(d, MutableSequence))
