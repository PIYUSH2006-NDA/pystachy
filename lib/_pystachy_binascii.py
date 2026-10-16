"""Conversion between binary data and ASCII"""
# Pystachy's binascii: a port of CPython 3.13's C module (Modules/binascii.c), which CPython
# builds into its interpreter and imports instead of this file. Pystachy loads it for import
# binascii. Functions take bytes, the a2b_*() ones also a str of ASCII characters, and raise
# the C module's errors with its messages.


class Error(ValueError):
    pass


class Incomplete(Exception):
    pass


def _ascii(data):
    # an argument a2b_*() reads as ASCII text: a bytes, or a str of ASCII characters
    if isinstance(data, str):
        if not data.isascii():
            raise ValueError("string argument should contain only ASCII characters")
        return data.encode("ascii")
    return data


def _hexdigit(c: int) -> int:
    return c - 48 if 48 <= c <= 57 else c - 87 if 97 <= c <= 102 else c - 55 if 65 <= c <= 70 else 16


_HEX = b"0123456789abcdef"


def hexlify(data: bytes, sep=None, bytes_per_sep: int = 1) -> bytes:
    """Hexadecimal representation of binary data.

  sep
    An optional single character or byte to separate hex bytes.
  bytes_per_sep
    How many bytes between separators.  Positive values count from the
    right, negative values count from the left.

The return value is a bytes object.  This function is also
available as "b2a_hex()"."""
    if bytes_per_sep > 2147483647 or bytes_per_sep < -2147483648:
        raise OverflowError("Python int too large to convert to C int")  # (a C int argument)
    out: list[int] = []
    s = -1
    if sep is not None:
        if isinstance(sep, str):
            # its characters, one byte each (a str's length counts its UTF-8 bytes in Pystachy):
            # the Latin-1 byte of a character below 256, which the C module accepts, else "?"
            sb = sep.encode("latin-1", "replace")
            if len(sb) != 1:
                raise ValueError("sep must be length 1.")
            if sb == b"?" and sep != "?":
                raise ValueError("sep must be ASCII.")
            s = sb[0]
        else:
            if len(sep) != 1:
                raise ValueError("sep must be length 1.")
            s = sep[0]
    n = len(data)
    group = bytes_per_sep if bytes_per_sep >= 0 else -bytes_per_sep
    for i in range(n):
        if s >= 0 and group > 0 and i > 0:
            # a separator before every group of bytes_per_sep bytes: counted from the right (from
            # the end) where it is positive, from the left where it is negative
            if (bytes_per_sep > 0 and (n - i) % group == 0) or (bytes_per_sep < 0 and i % group == 0):
                out.append(s)
        c = data[i]
        out.append(_HEX[c >> 4])
        out.append(_HEX[c & 15])
    return bytes(out)


def b2a_hex(data: bytes, sep=None, bytes_per_sep: int = 1) -> bytes:
    """Hexadecimal representation of binary data.

  sep
    An optional single character or byte to separate hex bytes.
  bytes_per_sep
    How many bytes between separators.  Positive values count from the
    right, negative values count from the left.

The return value is a bytes object.  This function is also
available as "hexlify()".

Example:
>>> binascii.b2a_hex(b'\\xb9\\x01\\xef')
b'b901ef'
>>> binascii.hexlify(b'\\xb9\\x01\\xef', ':')
b'b9:01:ef'
>>> binascii.b2a_hex(b'\\xb9\\x01\\xef', b'_', 2)
b'b9_01ef'"""
    return hexlify(data, sep, bytes_per_sep)


def unhexlify(hexstr, /) -> bytes:
    """Binary data of hexadecimal representation.

hexstr must contain an even number of hex digits (upper or lower case)."""
    h = _ascii(hexstr)
    if len(h) % 2:
        raise Error("Odd-length string")
    out: list[int] = []
    for i in range(0, len(h), 2):
        top = _hexdigit(h[i])
        bot = _hexdigit(h[i + 1])
        if top >= 16 or bot >= 16:
            raise Error("Non-hexadecimal digit found")
        out.append(top * 16 + bot)
    return bytes(out)


def a2b_hex(hexstr, /) -> bytes:
    """Binary data of hexadecimal representation.

hexstr must contain an even number of hex digits (upper or lower case).
This function is also available as "unhexlify()"."""
    return unhexlify(hexstr)


_B64 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def _b64value(c: int) -> int:
    # the value of base64 digit c, or 64 for a byte that is none (table_a2b_base64)
    if 65 <= c <= 90:
        return c - 65
    if 97 <= c <= 122:
        return c - 71
    if 48 <= c <= 57:
        return c + 4
    return 62 if c == 43 else 63 if c == 47 else 64


def b2a_base64(data: bytes, /, *, newline: bool = True) -> bytes:
    """Base64-code line of data."""
    out: list[int] = []
    n = len(data)
    i = 0
    while i + 3 <= n:
        v = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2]
        out.append(_B64[v >> 18])
        out.append(_B64[(v >> 12) & 63])
        out.append(_B64[(v >> 6) & 63])
        out.append(_B64[v & 63])
        i += 3
    if n - i == 1:
        v = data[i] << 16
        out.append(_B64[v >> 18])
        out.append(_B64[(v >> 12) & 63])
        out.append(61)
        out.append(61)
    elif n - i == 2:
        v = (data[i] << 16) | (data[i + 1] << 8)
        out.append(_B64[v >> 18])
        out.append(_B64[(v >> 12) & 63])
        out.append(_B64[(v >> 6) & 63])
        out.append(61)
    if newline:
        out.append(10)
    return bytes(out)


def a2b_base64(data, /, *, strict_mode: bool = False) -> bytes:
    """Decode a line of base64 data.

  strict_mode
    When set to True, bytes that are not part of the base64 standard are not allowed.
    The same applies to excess data after padding (= / ==)."""
    a = _ascii(data)
    out: list[int] = []
    quad = 0
    left = 0
    pads = 0
    for i in range(len(a)):
        c = a[i]
        if c == 61:
            # a pad: those that end a quad count, the others are ignored (but in strict mode)
            pads += 1
            if quad >= 2 and quad + pads <= 4:
                continue
            if not strict_mode:
                continue
            if quad == 1:
                break  # (the error below)
            raise Error("Leading padding not allowed" if quad == 0 and i == 0 else "Excess padding not allowed")
        v = _b64value(c)
        if v >= 64:
            if strict_mode:
                raise Error("Only base64 data is allowed")
            continue
        if pads > 0 and strict_mode:
            raise Error("Excess data after padding" if quad + pads == 4 else "Discontinuous padding not allowed")
        pads = 0
        if quad == 0:
            quad = 1
            left = v
        elif quad == 1:
            quad = 2
            out.append(((left << 2) | (v >> 4)) & 255)
            left = v & 15
        elif quad == 2:
            quad = 3
            out.append(((left << 4) | (v >> 2)) & 255)
            left = v & 3
        else:
            quad = 0
            out.append(((left << 6) | v) & 255)
            left = 0
    if quad == 1:
        raise Error("Invalid base64-encoded string: number of data characters (" + str(len(out) // 3 * 4 + 1) + ") cannot be 1 more than a multiple of 4")
    if quad != 0 and quad + pads < 4:
        raise Error("Incorrect padding")
    return bytes(out)


def _crc32_table() -> list[int]:
    t: list[int] = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        t.append(c)
    return t


_CRC32 = _crc32_table()


def crc32(data: bytes, crc: int = 0, /) -> int:
    """Compute CRC-32 incrementally."""
    c = ~crc & 0xFFFFFFFF
    for b in data:
        c = _CRC32[(c ^ b) & 255] ^ (c >> 8)
    return ~c & 0xFFFFFFFF


def _crc_hqx_table() -> list[int]:
    t: list[int] = []
    for n in range(256):
        c = n << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
        t.append(c)
    return t


_CRC_HQX = _crc_hqx_table()


def crc_hqx(data: bytes, crc: int, /) -> int:
    """Compute CRC-CCITT incrementally."""
    c = crc & 0xFFFF
    for b in data:
        c = ((c << 8) & 0xFF00) ^ _CRC_HQX[((c >> 8) & 255) ^ b]
    return c


def b2a_uu(data: bytes, /, *, backtick: bool = False) -> bytes:
    """Uuencode line of data."""
    n = len(data)
    if n > 45:
        raise Error("At most 45 bytes at once")
    out: list[int] = [96 if backtick and n == 0 else 32 + n]
    left = 0
    bits = 0
    i = 0
    while i < n or bits != 0:
        left = ((left << 8) | data[i]) if i < n else left << 8
        bits += 8
        i += 1
        while bits >= 6:
            c = (left >> (bits - 6)) & 63
            bits -= 6
            out.append(96 if backtick and c == 0 else c + 32)
        left &= (1 << bits) - 1
    out.append(10)
    return bytes(out)


def a2b_uu(data, /) -> bytes:
    """Decode a line of uuencoded data."""
    a = _ascii(data)
    if len(a) == 0:
        raise Error("Missing length byte")
    n = (a[0] - 32) & 63
    out: list[int] = []
    left = 0
    bits = 0
    i = 1
    while len(out) < n:
        c = a[i] if i < len(a) else 0
        if c == 10 or c == 13 or i >= len(a):
            c = 0  # (spaces an end of line ate)
        else:
            if c < 32 or c > 96:
                raise Error("Illegal char")
            c = (c - 32) & 63
        left = (left << 6) | c
        bits += 6
        if bits >= 8:
            bits -= 8
            out.append((left >> bits) & 255)
            left &= (1 << bits) - 1
        i += 1
    while i < len(a):
        c = a[i]
        if c != 32 and c != 96 and c != 10 and c != 13:
            raise Error("Trailing garbage")
        i += 1
    return bytes(out)


def a2b_qp(data, header: bool = False) -> bytes:
    """Decode a string of qp-encoded data."""
    a = _ascii(data)
    n = len(a)
    out: list[int] = []
    i = 0
    while i < n:
        c = a[i]
        if c == 61:
            i += 1
            if i >= n:
                break
            c = a[i]
            if c == 10 or c == 13:
                # a soft line break, to the end of its line
                if c != 10:
                    while i < n and a[i] != 10:
                        i += 1
                if i < n:
                    i += 1
            elif c == 61:
                # (a broken case, from Python's broken qp)
                out.append(61)
                i += 1
            elif i + 1 < n and _hexdigit(c) < 16 and _hexdigit(a[i + 1]) < 16:
                out.append(_hexdigit(c) * 16 + _hexdigit(a[i + 1]))
                i += 2
            else:
                out.append(61)
        elif header and c == 95:
            out.append(32)
            i += 1
        else:
            out.append(c)
            i += 1
    return bytes(out)


_HEXU = b"0123456789ABCDEF"


def b2a_qp(data: bytes, quotetabs: bool = False, istext: bool = True, header: bool = False) -> bytes:
    """Encode a string using quoted-printable encoding.

On encoding, when istext is set, newlines are not encoded, and white
space at end of lines is.  When istext is not set, \\r and \\n (CR/LF)
are both encoded.  When quotetabs is set, space and tabs are encoded."""
    n = len(data)
    # line ends are CRLF where the first LF follows a CR: the output's line ends then are all
    p = 0
    while p < n and data[p] != 10:
        p += 1
    crlf = 0 < p < n and data[p - 1] == 13
    out: list[int] = []
    i = 0
    linelen = 0
    while i < n:
        c = data[i]
        if (c > 126 or c == 61 or (header and c == 95)
                or (c == 46 and linelen == 0 and (i + 1 == n or data[i + 1] == 10 or data[i + 1] == 13 or data[i + 1] == 0))
                or (not istext and (c == 13 or c == 10))
                or ((c == 9 or c == 32) and i + 1 == n)
                or (c < 33 and c != 13 and c != 10 and (quotetabs or (c != 9 and c != 32)))):
            if linelen + 3 >= 76:
                # a soft line break
                out.append(61)
                if crlf:
                    out.append(13)
                out.append(10)
                linelen = 0
            out.append(61)
            out.append(_HEXU[c >> 4])
            out.append(_HEXU[c & 15])
            i += 1
            linelen += 3
        elif istext and (c == 10 or (i + 1 < n and c == 13 and data[i + 1] == 10)):
            linelen = 0
            # white space before a line end is encoded
            if len(out) > 0 and (out[-1] == 32 or out[-1] == 9):
                w = out[-1]
                out[-1] = 61
                out.append(_HEXU[w >> 4])
                out.append(_HEXU[w & 15])
            if crlf:
                out.append(13)
            out.append(10)
            i += 2 if c == 13 else 1
        else:
            if i + 1 != n and data[i + 1] != 10 and linelen + 1 >= 76:
                out.append(61)
                if crlf:
                    out.append(13)
                out.append(10)
                linelen = 0
            linelen += 1
            out.append(95 if header and c == 32 else c)
            i += 1
    return bytes(out)
