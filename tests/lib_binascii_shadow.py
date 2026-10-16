# The program's directory holds a package binascii (tests/binascii/), which CPython never imports in
# place of its C module: neither does Pystachy, which loads its stand-in, lib/_pystachy_binascii.py
import binascii
from binascii import b2a_base64, crc32

print(binascii.__name__, binascii.hexlify(b"\x00\xff"), crc32(b"shadow"), b2a_base64(b"x", newline=False))
