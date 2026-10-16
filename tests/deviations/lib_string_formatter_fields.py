# Documented deviation: string.Formatter looks up no attributes or items of an argument (a
# field name with ".name" or "[key]" raises ValueError: the types they give are known only once
# the format string is parsed), and check_unused_args() gets the arguments used as a list, in
# the order of their first use, rather than a set. CPython prints
# 2.5
# 2.5
# b
# set {0, 1}
from string import Formatter


class Point:
    def __init__(self, x: float) -> None:
        self.x = x


for s in ["{0.x}", "{p.x}"]:
    try:
        print(Formatter().format(s, Point(2.5), p=Point(2.5)))
    except ValueError as e:
        print("ValueError:", e)
try:
    print(Formatter().format("{0[1]}", ["a", "b"]))
except ValueError as e:
    print("ValueError:", e)


class Show(Formatter):
    def check_unused_args(self, used_args, args, kwargs):
        print("list" if isinstance(used_args, list) else "set", used_args)


Show().format("{1}{0}{1}", "a", "b")
