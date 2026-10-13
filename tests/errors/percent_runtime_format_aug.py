# error: percent_runtime_format_aug.py:3: error: % formatting with a format string computed at run time is not supported (only a string literal: "%d" % x)
s = "%s-%s"
s %= ("a", "b")
print(s)
