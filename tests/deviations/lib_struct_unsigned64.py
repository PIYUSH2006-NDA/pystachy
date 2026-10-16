# An unsigned 8-byte value from 2**63 on (Q, native L, N and P) raises OverflowError as it is
# unpacked: Pystachy's ints are 64-bit, where CPython's int holds it (lib/compatibility.md)
import struct

try:
    print(struct.unpack("<Q", b"\xff" * 8))
except OverflowError as e:
    print("OverflowError:", e)
print(struct.unpack("<Q", b"\xff" * 7 + b"\x7f"))
