# Documented deviations of lib/string (CPython 3.13's string with marked edits) from CPython.
from string import Template, capwords

# Template.flags is lib/re's int: CPython prints re.IGNORECASE.
print(Template.flags)

# The column of an invalid placeholder counts a str's bytes past ASCII, as lib/re's positions do:
# CPython prints col 3 and col 7.
for t in ["\xe9 $", "na\xefve\nna\xefve $1"]:
    try:
        Template(t).substitute()
    except ValueError as e:
        print(e)

# capwords() capitalizes ASCII letters alone, as str.capitalize() does: CPython prints
# Élan Vital.
print(capwords("\xe9lan vital"))
