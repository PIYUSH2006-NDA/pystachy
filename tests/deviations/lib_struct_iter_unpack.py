# struct.iter_unpack() gives the list of the tuples, where CPython's gives an iterator of them
# (lib/compatibility.md); a for loop and list() see the same tuples
import struct

it = struct.iter_unpack("<H", b"abcd")
print(it)
