# itertools' iterators are generators here (lib/compatibility.md), so hasattr() finds the
# generator's methods and attributes on them, where CPython's iterators are objects of the C
# types, which have none of them (calling one is a compile-time error here)
from itertools import chain, count, islice

print(hasattr(count(), "send"), hasattr(count(), "close"), hasattr(count(), "throw"))
print(hasattr(chain("ab"), "gi_frame"), hasattr(islice("ab", 1), "gi_running"))
print(hasattr(count(), "__next__"), hasattr(count(), "__iter__"))
