# Iterating a str gives its bytes (lib/compatibility.md), so a character of more than one byte
# reaches unicodedata's functions as its bytes, which are no character: TypeError, where CPython
# gives the character's combining class (re.findall("(?s).", s) gives the characters)
import unicodedata

try:
    print([unicodedata.combining(c) for c in "\u00e9"])
except TypeError as e:
    print("TypeError:", e)
print([unicodedata.combining(c) for c in "abc"])
