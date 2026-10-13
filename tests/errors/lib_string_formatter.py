# error: cannot infer the type of 'used_args', an empty set so far
# lib/string's Formatter stays uncompiled (lib/README.md): it needs CPython's C module _string,
# whose import is optional here, and sets of mixed items
import string

print(string.Formatter().format("{0} and {1}", "a", "b"))
