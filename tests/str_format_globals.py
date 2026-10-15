# str.format() of a module global that a single assignment binds to a string literal: the
# literal's fields, once the name is read (a read before the assignment raises NameError, as in
# CPython), also through a from-import, an annotated assignment and another module's attribute
import mods.fmtconstants as fc
from mods.fmtconstants import ROW, ROW as R2, TITLE

LINE = "{0}: {1!r}"
SEP: str = "{sep}".join(["a", "b"])
WIDE = "{:{w}}|"


def show(k: str, v: str) -> str:
    return LINE.format(k, v)


def early() -> str:
    return LATER.format(1)


try:
    print(early())
except NameError as e:
    print("NameError:", e)
LATER = "later {}"
print(early())
print(show("key", "välue"), WIDE.format(3, w=5), SEP)
print(ROW.format("ab", 7), R2.format("c", 8), fc.row("d", 9), fc.late(3))
print(TITLE.format(title="x"), TITLE.format_map({"title": "y"}))
print(fc.ROW.format("e", 10), fc.TITLE.format(title="z"))
try:
    print(LINE.format("only"))
except IndexError as e:
    print("IndexError:", e)
print(list(map(LINE.format, ["a", "b"], [1, 2])))
