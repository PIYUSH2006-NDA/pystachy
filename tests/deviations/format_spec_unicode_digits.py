# Documented deviation: a format spec's width or precision written in non-ASCII decimal digits
# is not read as a number, where CPython reads it as one ("٣" is 3 there): the spec is invalid
x = 12
for spec in ["٣", ".٢f"]:
    try:
        print(repr(format(1.5, spec)))
    except ValueError as e:
        print("ValueError", e)
try:
    print(repr(f"{x:٣}"), repr("{:٣}".format(x)))
except ValueError as e:
    print("ValueError", e)
