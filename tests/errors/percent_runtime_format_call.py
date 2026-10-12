# error: percent_runtime_format_call.py:7: error: % formatting with a format string computed at run time is not supported (only a string literal: "%d" % x)
# a format string a function returns, as a translated message is (gettext)
def tr(s: str) -> str:
    return s


print(tr("%d items") % 3)
