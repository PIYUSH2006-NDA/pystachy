# The decoding work of lib/re: re._decoded counts the code points it has decoded (CPython's re has
# no such counter). An operation decodes its subject once and keeps it, also where a function that
# sub() calls matches another string, so a substitution's work grows with its string, not with
# the string's square. Spans after such a call are still the subject's (here byte indices, which
# CPython counts in code points: a<é1>b<é3>)
import re

outer = re.compile("a")
inner = re.compile("b")


def replacement(m) -> str:
    inner.match("b")
    return "x"


for n in [10, 100, 1000, 10000]:
    before = re._decoded
    r = outer.sub(replacement, "a" * n)
    work = re._decoded - before
    print(n, r == "x" * n, work, work <= n + 1)


def mark(m) -> str:
    inner.search("xb")
    return "<" + str(m.group(1)) + str(m.start()) + ">"


print(re.compile("(é)").sub(mark, "aébé"), re.compile("(é)").subn(mark, "ééé"))
