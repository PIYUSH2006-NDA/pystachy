# examples/linediff: unified and word diffs of two generated versions of a text, through difflib's
# SequenceMatcher, as CPython prints them; then its errors, whose last line goes to stderr
import os
import tempfile

import gentext
import linediff

print(linediff.span(0, 0), linediff.span(3, 4), linediff.span(3, 9), linediff.span(5, 5))
print(linediff.groups([("equal", 0, 10, 0, 10), ("replace", 10, 11, 10, 12), ("equal", 11, 30, 12, 31), ("delete", 30, 31, 31, 31)], 3))
print(linediff.groups([("equal", 0, 5, 0, 5)], 3), linediff.groups([], 3))
print(linediff.marked("the quick brown fox".split(), "the slow brown dog jumps".split()))
print(linediff.unified(["a", "b", "c"], ["a", "c", "d"], 1, "old", "new"))

old, new = gentext.versions(400)
d = tempfile.mkdtemp()
paths = [os.path.join(d, "old.txt"), os.path.join(d, "new.txt")]
for path, lines in [(paths[0], old), (paths[1], new)]:
    with open(path, "w") as f:
        for line in lines:
            f.write(line + "\n")
for n in [3, 1, 0]:
    for line in linediff.unified(old, new, n, "old.txt", "new.txt"):
        print(line)
print(linediff.summary(old, new, False))
for argv in [["--words"], ["-q"], ["--words", "-q"], ["-U", "2", "-q"]]:
    print(argv, "->", linediff.main(argv + paths))
print(linediff.main(["-q", paths[0], paths[0]]))
print(linediff.main(["-x"] + paths), linediff.main([paths[0]]))
for path in paths:
    os.remove(path)
os.rmdir(d)
