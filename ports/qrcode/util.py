import math
# Pystachy port: no `re` (#11); its uses are written as loops below

from qrcode import LUT, base, exceptions
from qrcode.base import RSBlock

# QR encoding modes.
MODE_NUMBER = 1 << 0
MODE_ALPHA_NUM = 1 << 1
MODE_8BIT_BYTE = 1 << 2
MODE_KANJI = 1 << 3

# Encoding mode sizes.
MODE_SIZE_SMALL = {
    MODE_NUMBER: 10,
    MODE_ALPHA_NUM: 9,
    MODE_8BIT_BYTE: 8,
    MODE_KANJI: 8,
}
MODE_SIZE_MEDIUM = {
    MODE_NUMBER: 12,
    MODE_ALPHA_NUM: 11,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 10,
}
MODE_SIZE_LARGE = {
    MODE_NUMBER: 14,
    MODE_ALPHA_NUM: 13,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 12,
}

# Pystachy port: a str, not bytes (M7: bytes). A Pystachy str holds UTF-8 bytes, so the data,
# which upstream encodes to UTF-8, is iterated, indexed, sliced and measured as those bytes
# here too. RE_ALPHA_NUM is a loop in optimal_mode() (#11: re).
ALPHA_NUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

# The number of bits for numeric delimited data lengths.
NUMBER_LENGTH = {3: 10, 2: 7, 1: 4}

# Pystachy port: annotated; a display is typed by its first item, here `[]` (M1)
PATTERN_POSITION_TABLE: list[list[int]] = [
    [],
    [6, 18],
    [6, 22],
    [6, 26],
    [6, 30],
    [6, 34],
    [6, 22, 38],
    [6, 24, 42],
    [6, 26, 46],
    [6, 28, 50],
    [6, 30, 54],
    [6, 32, 58],
    [6, 34, 62],
    [6, 26, 46, 66],
    [6, 26, 48, 70],
    [6, 26, 50, 74],
    [6, 30, 54, 78],
    [6, 30, 56, 82],
    [6, 30, 58, 86],
    [6, 34, 62, 90],
    [6, 28, 50, 72, 94],
    [6, 26, 50, 74, 98],
    [6, 30, 54, 78, 102],
    [6, 28, 54, 80, 106],
    [6, 32, 58, 84, 110],
    [6, 30, 58, 86, 114],
    [6, 34, 62, 90, 118],
    [6, 26, 50, 74, 98, 122],
    [6, 30, 54, 78, 102, 126],
    [6, 26, 52, 78, 104, 130],
    [6, 30, 56, 82, 108, 134],
    [6, 34, 60, 86, 112, 138],
    [6, 30, 58, 86, 114, 142],
    [6, 34, 62, 90, 118, 146],
    [6, 30, 54, 78, 102, 126, 150],
    [6, 24, 50, 76, 102, 128, 154],
    [6, 28, 54, 80, 106, 132, 158],
    [6, 32, 58, 84, 110, 136, 162],
    [6, 26, 54, 82, 110, 138, 166],
    [6, 30, 58, 86, 114, 142, 170],
]

G15 = (1 << 10) | (1 << 8) | (1 << 5) | (1 << 4) | (1 << 2) | (1 << 1) | (1 << 0)
G18 = (
    (1 << 12)
    | (1 << 11)
    | (1 << 10)
    | (1 << 9)
    | (1 << 8)
    | (1 << 5)
    | (1 << 2)
    | (1 << 0)
)
G15_MASK = (1 << 14) | (1 << 12) | (1 << 10) | (1 << 4) | (1 << 1)

PAD0 = 0xEC
PAD1 = 0x11


# Precompute bit count limits, indexed by error correction level and code size
def _data_count(block):
    return block.data_count


BIT_LIMIT_TABLE = [
    [0]
    + [
        8 * sum(map(_data_count, base.rs_blocks(version, error_correction)))
        for version in range(1, 41)
    ]
    for error_correction in range(4)
]


def BCH_type_info(data):
    d = data << 10
    while BCH_digit(d) - BCH_digit(G15) >= 0:
        d ^= G15 << (BCH_digit(d) - BCH_digit(G15))

    return ((data << 10) | d) ^ G15_MASK


def BCH_type_number(data):
    d = data << 12
    while BCH_digit(d) - BCH_digit(G18) >= 0:
        d ^= G18 << (BCH_digit(d) - BCH_digit(G18))
    return (data << 12) | d


def BCH_digit(data):
    digit = 0
    while data != 0:
        digit += 1
        data >>= 1
    return digit


def pattern_position(version):
    return PATTERN_POSITION_TABLE[version - 1]


def mask_func(pattern):
    """
    Return the mask function for the given mask pattern.
    """
    if pattern == 0:  # 000
        return lambda i, j: (i + j) % 2 == 0
    if pattern == 1:  # 001
        return lambda i, j: i % 2 == 0
    if pattern == 2:  # 010
        return lambda i, j: j % 3 == 0
    if pattern == 3:  # 011
        return lambda i, j: (i + j) % 3 == 0
    if pattern == 4:  # 100
        return lambda i, j: (math.floor(i / 2) + math.floor(j / 3)) % 2 == 0
    if pattern == 5:  # 101
        return lambda i, j: (i * j) % 2 + (i * j) % 3 == 0
    if pattern == 6:  # 110
        return lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0
    if pattern == 7:  # 111
        return lambda i, j: ((i * j) % 3 + (i + j) % 2) % 2 == 0
    raise TypeError("Bad mask pattern: " + pattern)  # pragma: no cover


# Pystachy port: mask_func's lambdas as one function of the pattern and the position, which
# map_data calls where upstream calls the lambda (M3: lambdas). The last line raises the
# TypeError of upstream's `"..." + pattern`, str + int, which Pystachy rejects; no pattern
# outside range(8) gets here through make(), which checks it.
def mask_bit(pattern, i, j):
    if pattern == 0:  # 000
        return (i + j) % 2 == 0
    if pattern == 1:  # 001
        return i % 2 == 0
    if pattern == 2:  # 010
        return j % 3 == 0
    if pattern == 3:  # 011
        return (i + j) % 3 == 0
    if pattern == 4:  # 100
        return (math.floor(i / 2) + math.floor(j / 3)) % 2 == 0
    if pattern == 5:  # 101
        return (i * j) % 2 + (i * j) % 3 == 0
    if pattern == 6:  # 110
        return ((i * j) % 2 + (i * j) % 3) % 2 == 0
    if pattern == 7:  # 111
        return ((i * j) % 3 + (i + j) % 2) % 2 == 0
    raise TypeError('can only concatenate str (not "int") to str')  # pragma: no cover


def mode_sizes_for_version(version):
    if version < 10:
        return MODE_SIZE_SMALL
    elif version < 27:
        return MODE_SIZE_MEDIUM
    else:
        return MODE_SIZE_LARGE


def length_in_bits(mode, version):
    if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE, MODE_KANJI):
        raise TypeError(f"Invalid mode ({mode})")  # pragma: no cover

    check_version(version)

    return mode_sizes_for_version(version)[mode]


def check_version(version):
    if version < 1 or version > 40:
        raise ValueError(f"Invalid version (was {version}, expected 1 to 40)")


def lost_point(modules):
    modules_count = len(modules)

    lost_point = 0

    lost_point = _lost_point_level1(modules, modules_count)
    lost_point += _lost_point_level2(modules, modules_count)
    lost_point += _lost_point_level3(modules, modules_count)
    lost_point += _lost_point_level4(modules, modules_count)

    return lost_point


def _lost_point_level1(modules, modules_count):
    lost_point = 0

    # Pystachy port: a list of the range; a range is no value (M7)
    modules_range = list(range(modules_count))
    container = [0] * (modules_count + 1)

    for row in modules_range:
        this_row = modules[row]
        previous_color = this_row[0]
        length = 0
        for col in modules_range:
            if this_row[col] == previous_color:
                length += 1
            else:
                if length >= 5:
                    container[length] += 1
                length = 1
                previous_color = this_row[col]
        if length >= 5:
            container[length] += 1

    for col in modules_range:
        previous_color = modules[0][col]
        length = 0
        for row in modules_range:
            if modules[row][col] == previous_color:
                length += 1
            else:
                if length >= 5:
                    container[length] += 1
                length = 1
                previous_color = modules[row][col]
        if length >= 5:
            container[length] += 1

    lost_point += sum(
        container[each_length] * (each_length - 2)
        for each_length in range(5, modules_count + 1)
    )

    return lost_point


def _lost_point_level2(modules, modules_count):
    lost_point = 0

    # Pystachy port: a list of the range, and a while loop that steps `col`, skipping one where
    # upstream skips an item of iter(modules_range) with next() (M7: range values, iterators)
    modules_range = list(range(modules_count - 1))
    for row in modules_range:
        this_row = modules[row]
        next_row = modules[row + 1]
        # use iter() and next() to skip next four-block. e.g.
        # d a f   if top-right a != b bottom-right,
        # c b e   then both abcd and abef won't lost any point.
        col = 0
        while col < modules_count - 1:
            top_right = this_row[col + 1]
            if top_right != next_row[col + 1]:
                # reduce 33.3% of runtime via next().
                # None: raise nothing if there is no next item.
                col += 1  # Pystachy port: see above
            elif top_right != this_row[col]:
                pass  # Pystachy port: `continue` would not step `col`
            elif top_right != next_row[col]:
                pass  # Pystachy port: as above
            else:
                lost_point += 3
            col += 1  # Pystachy port: see above

    return lost_point


def _lost_point_level3(modules, modules_count):
    # 1 : 1 : 3 : 1 : 1 ratio (dark:light:dark:light:dark) pattern in
    # row/column, preceded or followed by light area 4 modules wide. From ISOIEC.
    # pattern1:     10111010000
    # pattern2: 00001011101
    # Pystachy port: a list of the range, and while loops that step `col` and `row`, skipping
    # one where upstream skips an item of iter(modules_range_short) with next() (M7: range
    # values, iterators)
    modules_range = list(range(modules_count))
    lost_point = 0

    for row in modules_range:
        this_row = modules[row]
        col = 0
        while col < modules_count - 10:
            if (
                not this_row[col + 1]
                and this_row[col + 4]
                and not this_row[col + 5]
                and this_row[col + 6]
                and not this_row[col + 9]
                and (
                    this_row[col + 0]
                    and this_row[col + 2]
                    and this_row[col + 3]
                    and not this_row[col + 7]
                    and not this_row[col + 8]
                    and not this_row[col + 10]
                    or not this_row[col + 0]
                    and not this_row[col + 2]
                    and not this_row[col + 3]
                    and this_row[col + 7]
                    and this_row[col + 8]
                    and this_row[col + 10]
                )
            ):
                lost_point += 40
            # horspool algorithm.
            # if this_row[col + 10]:
            #   pattern1 shift 4, pattern2 shift 2. So min=2.
            # else:
            #   pattern1 shift 1, pattern2 shift 1. So min=1.
            if this_row[col + 10]:
                col += 1  # Pystachy port: see above
            col += 1  # Pystachy port: see above

    for col in modules_range:
        row = 0
        while row < modules_count - 10:  # Pystachy port: see above
            if (
                not modules[row + 1][col]
                and modules[row + 4][col]
                and not modules[row + 5][col]
                and modules[row + 6][col]
                and not modules[row + 9][col]
                and (
                    modules[row + 0][col]
                    and modules[row + 2][col]
                    and modules[row + 3][col]
                    and not modules[row + 7][col]
                    and not modules[row + 8][col]
                    and not modules[row + 10][col]
                    or not modules[row + 0][col]
                    and not modules[row + 2][col]
                    and not modules[row + 3][col]
                    and modules[row + 7][col]
                    and modules[row + 8][col]
                    and modules[row + 10][col]
                )
            ):
                lost_point += 40
            if modules[row + 10][col]:
                row += 1  # Pystachy port: see above
            row += 1  # Pystachy port: see above

    return lost_point


def _lost_point_level4(modules, modules_count):
    # Pystachy port: each row's count of True for sum(map(sum, modules)) (M4: sum() of
    # bool | None items); every module is True or False by now
    dark_count = sum(row.count(True) for row in modules)
    percent = float(dark_count) / (modules_count**2)
    # Every 5% departure from 50%, rating++
    rating = int(abs(percent * 100 - 50) / 5)
    return rating * 10


def optimal_data_chunks(data, minimum=4):
    """
    An iterator returning QRData chunks optimized to the data content.

    :param minimum: The minimum number of bytes in a row to split as a chunk.
    """
    # Pystachy port: returns the list of the chunks that upstream's generator yields (M7:
    # generators). Where upstream compiles the regexes rb"\d{minimum,}" and
    # b"[ALPHA_NUM]{minimum,}", or rb"^\d+$" and b"^[ALPHA_NUM]+$" for data of up to
    # `minimum` bytes, a pattern is the str of the characters it matches, `minimum` and
    # whether it is anchored (#11: re).
    data = to_bytestring(data)
    num_pattern = "0123456789"
    alpha_pattern = ALPHA_NUM
    anchored = len(data) <= minimum
    chunks = []
    num_bits = _optimal_split(data, num_pattern, minimum, anchored)
    for is_num, chunk in num_bits:
        if is_num:
            chunks.append(QRData(chunk, mode=MODE_NUMBER, check_data=False))
        else:
            for is_alpha, sub_chunk in _optimal_split(chunk, alpha_pattern, minimum, anchored):
                mode = MODE_ALPHA_NUM if is_alpha else MODE_8BIT_BYTE
                chunks.append(QRData(sub_chunk, mode=mode, check_data=False))
    return chunks


# Pystachy port: returns the list of the pairs that upstream's generator yields (M7:
# generators), and _search() finds what re.search() found (#11: re)
def _optimal_split(data, chars, minimum, anchored):
    parts = []
    while data:
        start, end = _search(data, chars, minimum, anchored)
        if start < 0:
            break
        if start:
            parts.append((False, data[:start]))
        parts.append((True, data[start:end]))
        data = data[end:]
    if data:
        parts.append((False, data))
    return parts


# Pystachy port: the start and end of the match of the pattern (see optimal_data_chunks) in
# `data`, or -1, -1 for no match (#11: re): the first run of `minimum` or more characters
# of `chars`, which the regex takes whole; or, `anchored` ("^[chars]+$"), the run at the
# start if it goes to the end or to a final "\n", before which `$` matches too. A negative
# `minimum` makes the regex's "{-1,}" (or the like) literal text, not a repeat: one of the
# characters followed by that text.
def _search(data, chars, minimum, anchored):
    if minimum < 0:
        text = "{" + str(minimum) + ",}"
        for i in range(len(data) - len(text)):
            if data[i] in chars and data[i + 1 : i + 1 + len(text)] == text:
                return i, i + 1 + len(text)
        return -1, -1
    start = 0
    while start < len(data):
        end = start
        while end < len(data) and data[end] in chars:
            end += 1
        if anchored:
            if end > 0 and (end == len(data) or (end == len(data) - 1 and data[end] == "\n")):
                return start, end
            return -1, -1
        if end - start >= minimum:
            return start, end
        start = end + 1
    return -1, -1


def to_bytestring(data):
    """
    Convert data to a (utf-8 encoded) byte-string if it isn't a byte-string
    already.
    """
    if not isinstance(data, bytes):
        # Pystachy port: a str whose items are the UTF-8 bytes that upstream encodes (M7:
        # bytes). A Pystachy str holds them already. Where a str holds code points, as
        # CPython's does ("\u00e9" is one), each character becomes chr() of each of its bytes,
        # so that the port makes upstream's codes under CPython too.
        data = str(data)
        if len("\u00e9") == 1:
            data = "".join([_utf8_bytes(c) for c in data])
    return data


# Pystachy port: chr() of each byte of the character's UTF-8 encoding (see to_bytestring)
def _utf8_bytes(c):
    o = ord(c)
    if o < 0x80:
        return c
    if o < 0x800:
        return chr(0xC0 | o >> 6) + chr(0x80 | o & 0x3F)
    if o < 0x10000:
        return chr(0xE0 | o >> 12) + chr(0x80 | o >> 6 & 0x3F) + chr(0x80 | o & 0x3F)
    return (
        chr(0xF0 | o >> 18) + chr(0x80 | o >> 12 & 0x3F)
        + chr(0x80 | o >> 6 & 0x3F) + chr(0x80 | o & 0x3F)
    )


def optimal_mode(data):
    """
    Calculate the optimal mode for this chunk of data.
    """
    if data.isdigit():
        return MODE_NUMBER
    # Pystachy port: RE_ALPHA_NUM.match(data), rb"^[ALPHA_NUM]*\Z", as a loop (#11: re)
    if all(c in ALPHA_NUM for c in data):
        return MODE_ALPHA_NUM
    return MODE_8BIT_BYTE


class QRData:
    """
    Data held in a QR compatible format.

    Doesn't currently handle KANJI.
    """

    # Pystachy port: annotated (M2); the data is a str (M7: bytes)
    def __init__(self, data: str, mode: int | None = None, check_data: bool = True):
        """
        If ``mode`` isn't provided, the most compact QR data type possible is
        chosen.
        """
        if check_data:
            data = to_bytestring(data)

        if mode is None:
            self.mode: int = optimal_mode(data)  # Pystachy port: annotated (M2)
        else:
            self.mode = mode
            if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE):
                raise TypeError(f"Invalid mode ({mode})")  # pragma: no cover
            if check_data and mode < optimal_mode(data):  # pragma: no cover
                raise ValueError(f"Provided data can not be represented in mode {mode}")

        self.data = data

    def __len__(self):
        return len(self.data)

    def write(self, buffer):
        if self.mode == MODE_NUMBER:
            for i in range(0, len(self.data), 3):
                chars = self.data[i : i + 3]
                bit_length = NUMBER_LENGTH[len(chars)]
                buffer.put(int(chars), bit_length)
        elif self.mode == MODE_ALPHA_NUM:
            for i in range(0, len(self.data), 2):
                chars = self.data[i : i + 2]
                if len(chars) > 1:
                    buffer.put(
                        ALPHA_NUM.find(chars[0]) * 45 + ALPHA_NUM.find(chars[1]), 11
                    )
                else:
                    buffer.put(ALPHA_NUM.find(chars), 6)
        else:
            # Iterating a bytestring in Python 3 returns an integer,
            # no need to ord().
            data = self.data
            for c in data:
                buffer.put(ord(c), 8)  # Pystachy port: ord() of each byte (M7: bytes)

    def __repr__(self):
        return repr(self.data)


class BitBuffer:
    def __init__(self):
        self.buffer: list[int] = []
        self.length = 0

    def __repr__(self):
        return ".".join([str(n) for n in self.buffer])

    def get(self, index):
        buf_index = math.floor(index / 8)
        return ((self.buffer[buf_index] >> (7 - index % 8)) & 1) == 1

    def put(self, num, length):
        for i in range(length):
            self.put_bit(((num >> (length - i - 1)) & 1) == 1)

    def __len__(self):
        return self.length

    def put_bit(self, bit):
        buf_index = self.length // 8
        if len(self.buffer) <= buf_index:
            self.buffer.append(0)
        if bit:
            self.buffer[buf_index] |= 0x80 >> (self.length % 8)
        self.length += 1


def create_bytes(buffer: BitBuffer, rs_blocks: list[RSBlock]):
    offset = 0

    maxDcCount = 0
    maxEcCount = 0

    dcdata: list[list[int]] = []
    ecdata: list[list[int]] = []

    for rs_block in rs_blocks:
        dcCount = rs_block.data_count
        ecCount = rs_block.total_count - dcCount

        maxDcCount = max(maxDcCount, dcCount)
        maxEcCount = max(maxEcCount, ecCount)

        current_dc = [0xFF & buffer.buffer[i + offset] for i in range(dcCount)]
        offset += dcCount

        # Get error correction polynomial.
        if ecCount in LUT.rsPoly_LUT:
            rsPoly = base.Polynomial(LUT.rsPoly_LUT[ecCount], 0)
        else:
            rsPoly = base.Polynomial([1], 0)
            for i in range(ecCount):
                rsPoly = rsPoly * base.Polynomial([1, base.gexp(i)], 0)

        rawPoly = base.Polynomial(current_dc, len(rsPoly) - 1)

        modPoly = rawPoly % rsPoly
        current_ec = []
        mod_offset = len(modPoly) - ecCount
        for i in range(ecCount):
            modIndex = i + mod_offset
            current_ec.append(modPoly[modIndex] if (modIndex >= 0) else 0)

        dcdata.append(current_dc)
        ecdata.append(current_ec)

    data = []
    for i in range(maxDcCount):
        for dc in dcdata:
            if i < len(dc):
                data.append(dc[i])
    for i in range(maxEcCount):
        for ec in ecdata:
            if i < len(ec):
                data.append(ec[i])

    return data


def create_data(version, error_correction, data_list):
    buffer = BitBuffer()
    for data in data_list:
        buffer.put(data.mode, 4)
        buffer.put(len(data), length_in_bits(data.mode, version))
        data.write(buffer)

    # Calculate the maximum number of bits for the given version.
    rs_blocks = base.rs_blocks(version, error_correction)
    bit_limit = sum(block.data_count * 8 for block in rs_blocks)
    if len(buffer) > bit_limit:
        raise exceptions.DataOverflowError(
            "Code length overflow. Data size (%s) > size available (%s)"
            % (len(buffer), bit_limit)
        )

    # Terminate the bits (add up to four 0s).
    for _ in range(min(bit_limit - len(buffer), 4)):
        buffer.put_bit(False)

    # Delimit the string into 8-bit words, padding with 0s if necessary.
    delimit = len(buffer) % 8
    if delimit:
        for _ in range(8 - delimit):
            buffer.put_bit(False)

    # Add special alternating padding bitstrings until buffer is full.
    bytes_to_fill = (bit_limit - len(buffer)) // 8
    for i in range(bytes_to_fill):
        if i % 2 == 0:
            buffer.put(PAD0, 8)
        else:
            buffer.put(PAD1, 8)

    return create_bytes(buffer, rs_blocks)
