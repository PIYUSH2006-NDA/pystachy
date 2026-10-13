# Documented deviations of lib/textwrap (CPython 3.13's textwrap with marked edits) from CPython.
import textwrap

# A width counts a str's UTF-8 bytes, as len() does in Pystachy: past ASCII, fewer characters fit
# on a line. CPython prints ['aa ää-', 'ää'], ['Grüße aus', 'Köln'] and Grüße aus [...].
print(textwrap.wrap("aa ää-ää", 7))
print(textwrap.wrap("Grüße aus Köln", 9))
print(textwrap.shorten("Grüße aus Köln, sagt sie.", 15))

# A word longer than the width is broken after that many bytes, which can fall inside a
# character: two lines then hold its bytes apart, and joined they are the word again. CPython
# prints [3] True.
lines = textwrap.wrap("ééé", 3)
print([len(s) for s in lines], "".join(lines) == "ééé")
