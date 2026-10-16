# Documented deviations of lib/io's StringIO (Pystachy's own) from CPython's.
import io

# Positions and sizes count a str's bytes past ASCII, as len() and slicing do in Pystachy; CPython
# counts characters, and prints hél 3, then 5 5, then 'éll'.
s = io.StringIO("héllo")
print(s.read(3), s.tell())
print(s.seek(0, 2), len("héllo"))
s.seek(1)
print(repr(s.read(3)))
