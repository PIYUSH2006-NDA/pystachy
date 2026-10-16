# binascii.hexlify() and b2a_hex() of sep=None separate nothing, as without a sep: the stand-in's
# default is None, where the C module's is no object, so CPython raises TypeError (object of type
# 'NoneType' has no len()) for a sep of None
import binascii

print(binascii.hexlify(b"\x01\x02\x03", None), binascii.b2a_hex(b"\x01\x02\x03", None, 2))
