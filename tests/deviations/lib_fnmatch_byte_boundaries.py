# Internal byte boundaries have no CPython fnmatch counterpart. Forward and backward traversal
# must use the same complete-sequence policy; malformed bytes stand alone beside valid Unicode.
import fnmatch

for char in [chr(128), chr(191), chr(192), chr(193), chr(194), chr(233), chr(240), chr(244), chr(245), chr(255)]:
    print("byte", fnmatch._next_char(char, 0) == 1, fnmatch._last_char(char) == 0,
          fnmatch._next_char(char + "-", 0) == 1, fnmatch._last_char("a" + char) == 1)

for text in [chr(233) + chr(128), chr(240) + chr(128) + chr(128), chr(194) + "x", "a" + chr(128)]:
    print("truncated", fnmatch._next_char(text, 0) == 1, fnmatch._last_char(text) == len(text) - 1)

for char in ["é", "中", "😀"]:
    for text in [char, "a" + char, chr(233) + char, chr(128) + char]:
        start = len(text) - len(char)
        print("complete", fnmatch._last_char(text) == start, fnmatch._next_char(text, start) == len(text))
    text = char + chr(128)
    print("trailing byte", fnmatch._last_char(text) == len(char), fnmatch._next_char(text, 0) == len(char))

# Existing re._codes accepts structurally complete encodings by value. Range translation must
# not introduce ord() errors for those encodings (the broader regex scalar policy is unchanged).
overlong = chr(224) + chr(128) + chr(128)
outside = chr(244) + chr(191) + chr(191) + chr(191)
print("values", fnmatch._char_value(overlong) == 0, fnmatch._char_value(outside) == 1310719)
print("translated", len(fnmatch.translate("[" + overlong + "-a]")) > 0,
      fnmatch.translate("[" + outside + "-a]") == r"(?s:(?!))\Z")
