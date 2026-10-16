# sys.version_info is a tuple of its items (comparisons, indexing and slicing work as on
# CPython's): str() and repr() show that tuple, where CPython shows
# sys.version_info(major=3, minor=13, micro=16, releaselevel='final', serial=0).
import sys

print(sys.version_info)
print(repr(sys.version_info), str(sys.version_info[:2]))
