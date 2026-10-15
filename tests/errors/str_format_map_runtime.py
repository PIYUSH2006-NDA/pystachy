# error: str_format_map_runtime.py:4: error: str.format_map() of a format string computed at run time is not supported (only of a string literal: "{}".format_map(...))
# format_map() of a format string a variable holds
FMT = "{a}"
print(FMT.format_map({"a": 1}))
