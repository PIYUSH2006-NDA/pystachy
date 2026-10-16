# error: get_value() returns both int and str (each function has one return type)
# string.Formatter's get_value() returns a positional or a keyword argument, whose types must
# be those of one union (lib/compatibility.md)
import string

print(string.Formatter().format("{0} and {x}", 1, x="b"))
