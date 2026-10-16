# Documented deviation: a str holds UTF-8, and a stepped slice selects its bytes, as a plain
# slice, indexing and iteration count them: "añb" is 4 bytes, so s[::-1] reverses those bytes (as
# "".join(reversed(s)) does here; the result is not valid UTF-8, so it is not printed), s[1:3:1]
# is the two bytes of "ñ" and s[::3] is "ab" (CPython: lengths 3, "ñb" and "a"). ASCII text
# slices exactly as in CPython.
s = "añb"
r = s[::-1]
print(len(s), len(r), r == "".join(reversed(s)), r[::-1] == s, r[0] == "b", r[-1] == "a")
print(s[::2] == "a" + s[2], s[1:3:1] == "ñ", s[::3] == "ab")
