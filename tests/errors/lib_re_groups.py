# error: lib_re_groups.py:6: error: re.Match.groups() is not supported: return annotation: unsupported type annotation
# a tuple as long as the pattern's group count has no type in Pystachy (m.group(1, 2) has one)
import re

m = re.match("(a)(b)", "ab")
print(m.groups() if m is not None else None)
