# Documented deviation: a str holds UTF-8, so the text read from a Latin-1 file holds each
# character from U+0080 up as two bytes, which len() and indexing count, as for any such text:
# "Grüße" is 7 long and its [2] is the byte 195 (CPython: 5 and 252), and read(1) and read(2)
# of "üße" are 2 and 3 long (CPython: 1 and 2). chr() of 128 to 255 is that one byte, a
# character that a write to a Latin-1 file gives as itself, but chr() results that together make
# UTF-8 are the one character they encode: chr(195) + chr(169) is written as "é", the one byte
# 233, and write() returns 1 (CPython writes the two characters, bytes 195 and 169, and returns 2).
import os
import tempfile

d = tempfile.mkdtemp()
p = d + "/dev.txt"
os.system("printf 'Gr\\374\\337e' > '" + p + "'")
w = open(p, encoding="latin-1").read()
print(w, w == "Grüße", len(w), ord(w[2]))
f = open(p, encoding="latin-1")
print(repr(f.read(2)), len(f.read(1)), len(f.read(2)), repr(f.read()))
f.close()
f = open(p, "w", encoding="latin-1")
print(f.write(chr(195) + chr(169)), f.write(chr(195) + "x"))
f.close()
f = open(p, encoding="latin-1")
b: list[int] = []
c = f.read(1)
while c != "":
    b.append(ord(c))
    c = f.read(1)
f.close()
print(b)
os.remove(p)
os.rmdir(d)
