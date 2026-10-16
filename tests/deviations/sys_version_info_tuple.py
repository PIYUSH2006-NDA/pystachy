# sys.version_info is a tuple of its items (comparisons, indexing and slicing work as on
# CPython's): str() and repr() show that tuple, where CPython shows
# sys.version_info(major=3, minor=13, micro=16, releaselevel='final', serial=0); and each read
# makes a new tuple, where CPython's sys.version_info is one object (is gives True).
import sys

print(sys.version_info)
print(repr(sys.version_info), str(sys.version_info[:2]))
print(sys.version_info is sys.version_info, sys.version_info == sys.version_info)
