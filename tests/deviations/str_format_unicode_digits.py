# Documented deviation: a str.format() field name of non-ASCII decimal digits names a keyword
# argument, where CPython reads it as an argument number ("{٠}" is "{0}" there)
print("{0}|{٣}".format("zero", **{"٣": "three"}))
try:
    print("{٠}".format("zero"))
except KeyError as e:
    print("KeyError", e)
