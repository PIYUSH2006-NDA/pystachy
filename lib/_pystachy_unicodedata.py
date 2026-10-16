"""This module provides access to the Unicode Character Database which
defines character properties for all Unicode characters. The data in
this database is based on the UnicodeData.txt file version
15.1.0 which is publicly available from ftp://ftp.unicode.org/.

The module uses the same names and symbols as defined by the
UnicodeData File Format 15.1.0."""
# unicodedata for Pystachy: CPython builds unicodedata into its interpreter (Modules/unicodedata.c),
# so Pystachy loads this port of it for import unicodedata (specs.STANDINS). Its tables are
# CPython's: tools/unicodedata_tables.py writes them into _pystachy_unicodedata_db.py and, for
# name() and lookup(), which alone import it, _pystachy_unicodedata_names.py; each is decoded the
# first time a function needs it. A Pystachy str holds UTF-8, so a function's character is the one
# code point its argument's bytes encode, and normalize() works on the code points. ucd_3_2_0 is
# Unicode 3.2.0's view, as CPython's change records give it. The docstrings are CPython 3.13.16's.
import _pystachy_unicodedata_db as _db
import _pystachy_unicodedata_names as _n

unidata_version = "15.1.0"


_SBASE = 0xAC00
_LBASE = 0x1100
_VBASE = 0x1161
_TBASE = 0x11A7
_LCOUNT = 19
_VCOUNT = 21
_TCOUNT = 28
_NCOUNT = _VCOUNT * _TCOUNT
_SCOUNT = _LCOUNT * _NCOUNT
_NAME_MAXLEN = 256
# the jamo's short names, of the leading consonants, vowels and trailing consonants (CPython's
# hangul_syllables)
_JAMO_L = ["G", "GG", "N", "D", "DD", "R", "M", "B", "BB", "S", "SS", "", "J", "JJ", "C", "K", "T", "P", "H"]
_JAMO_V = ["A", "AE", "YA", "YAE", "EO", "E", "YEO", "YE", "O", "WA", "WAE", "OE", "YO", "U", "WEO", "WE", "WI", "YU", "EU",
           "YI", "I"]
_JAMO_T = ["", "G", "GG", "GS", "N", "NJ", "NH", "D", "L", "LG", "LM", "LB", "LS", "LT", "LP", "LH", "M", "B", "BS", "S",
           "SS", "NG", "J", "C", "K", "T", "P", "H"]

# ---- the tables of _db, decoded the first time they are read, into lists of ints (few objects,
# as the collector sees them) that the functions bisect
_cats: list[str] = []
_bidis: list[str] = []
_eaws: list[str] = []
_props: list[int] = []  # (five numbers for each record: category, bidirectional, east asian width, mirrored, combining)
_starts: list[list[int]] = []  # (the runs' starts, of the current version and of 3.2.0)
_recs: list[list[int]] = []  # (each run's record)
_unassigned: list[int] = []  # (3.2.0's unassigned code points: the start and the end past it of each range)
_numvalues: list[float] = []
_num: list[list[int]] = []  # (the code points with numeric values, then decimal + 1, digit + 1, numeric's index + 1)
_num32: list[list[int]] = []  # (3.2.0's where they differ: the code points, then decimal + 1, numeric's index + 1)
_tags: list[str] = []
_dec: list[list[int]] = []  # (the code points with decompositions, where each starts in the next, which holds
                            # each one's tag index * 32 + its length, then its code points)
_comp: dict[int, int] = {}  # (first * 0x110000 + last: the composite)
_first: dict[int, bool] = {}  # (the characters that start a composition)
_norm32: dict[int, int] = {}  # (3.2.0's corrected decompositions)


def _numbers(text: str) -> list[int]:
    # the base-36 numbers of text, separated by spaces (read from its bytes, making no str)
    out: list[int] = []
    v = 0
    digits = False
    for x in text.encode():
        if x == 32:
            if digits:
                out.append(v)
            v = 0
            digits = False
        else:
            v = v * 36 + (x - 48 if x < 58 else x - 87)
            digits = True
    if digits:
        out.append(v)
    return out


def _bisect(keys: list[int], c: int) -> int:
    # the number of keys at most c (sorted keys)
    lo = 0
    hi = len(keys)
    while lo < hi:
        mid = (lo + hi) // 2
        if keys[mid] <= c:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _find(keys: list[int], c: int) -> int:
    # the index of c in sorted keys, -1 if it is not there
    i = _bisect(keys, c) - 1
    return i if i >= 0 and keys[i] == c else -1


def _decode_props() -> None:
    for x in _db.CATEGORIES.split():
        _cats.append(x)
    for x in _db.BIDIRECTIONAL.split():
        _bidis.append("" if x == "-" else x)
    for x in _db.EAST_ASIAN_WIDTHS.split():
        _eaws.append(x)
    for v in _numbers(_db.PROPS):
        _props.append(v)
    for text in [_db.RUNS, _db.RUNS_3_2_0]:
        starts: list[int] = []
        recs: list[int] = []
        vs = _numbers(text)
        at = 0
        for i in range(0, len(vs), 2):
            at += vs[i]
            starts.append(at)
            recs.append(vs[i + 1])
        _starts.append(starts)
        _recs.append(recs)
    vs = _numbers(_db.UNASSIGNED_3_2_0)
    at = 0
    for i in range(0, len(vs), 2):
        at += vs[i]
        _unassigned.append(at)
        at += vs[i + 1]
        _unassigned.append(at)


def _record(c: int, old: bool) -> int:
    # the offset in _props of code point c's record, in the current version or 3.2.0's
    if len(_props) == 0:
        _decode_props()
    return 5 * _recs[1 if old else 0][_bisect(_starts[1 if old else 0], c) - 1]


def _unassigned_3_2_0(c: int) -> bool:
    # has Unicode 3.2.0 no character c, where the current version has one (CPython's change
    # record with a category of 0)
    if len(_props) == 0:
        _decode_props()
    return _bisect(_unassigned, c) % 2 == 1


def _decode_numeric() -> None:
    for w in _db.NUMERIC_VALUES.split():
        _numvalues.append(float(w))
    for text, width in [(_db.NUMERIC, 4), (_db.NUMERIC_3_2_0, 3)]:
        cols: list[list[int]] = [[] for k in range(width)]
        vs = _numbers(text)
        at = 0
        for i in range(0, len(vs), width):
            at += vs[i]
            cols[0].append(at)
            for k in range(1, width):
                cols[k].append(vs[i + k])
        if width == 4:
            for col in cols:
                _num.append(col)
        else:
            for col in cols:
                _num32.append(col)


def _decode_decomp() -> None:
    for x in _db.DECOMPOSITION_TAGS.split():
        _tags.append("" if x == "-" else x)
    keys: list[int] = []
    starts: list[int] = []
    data: list[int] = []
    vs = _numbers(_db.DECOMPOSITIONS)
    at = 0
    i = 0
    while i < len(vs):
        at += vs[i]
        keys.append(at)
        starts.append(len(data))
        k = vs[i + 1]
        for j in range(i + 1, i + 2 + k % 32):
            data.append(vs[j])
        i += 2 + k % 32
    _dec.append(keys)
    _dec.append(starts)
    _dec.append(data)
    vs = _numbers(_db.COMPOSITIONS)
    for i in range(0, len(vs), 3):
        _comp[vs[i] * 0x110000 + vs[i + 1]] = vs[i + 2]
        _first[vs[i]] = True
    vs = _numbers(_db.NORMALIZATION_3_2_0)
    for i in range(0, len(vs), 2):
        _norm32[vs[i]] = vs[i + 1]


def _decomp_of(c: int) -> int:
    # where c's decomposition starts in _dec[2], -1 for none
    if len(_tags) == 0:
        _decode_decomp()
    i = _find(_dec[0], c)
    return _dec[1][i] if i >= 0 else -1


# ---- the characters of str arguments


def _code(s: str, what: str) -> int:
    # the code point of a str of one character, as CPython's argument clinic takes it
    b = s.encode("utf-8", "surrogatepass")
    n = len(b)
    k = 0 if n == 0 else 1 if b[0] < 0x80 else 2 if b[0] < 0xE0 else 3 if b[0] < 0xF0 else 4
    if n == 0 or n != k:
        raise TypeError(f"{what} must be a unicode character, not str")
    if k == 1:
        return b[0]
    if k == 2:
        return (b[0] & 0x1F) << 6 | (b[1] & 0x3F)
    if k == 3:
        return (b[0] & 0x0F) << 12 | (b[1] & 0x3F) << 6 | (b[2] & 0x3F)
    return (b[0] & 0x07) << 18 | (b[1] & 0x3F) << 12 | (b[2] & 0x3F) << 6 | (b[3] & 0x3F)


def _codes(s: str) -> list[int]:
    # the code points of s, whose bytes are UTF-8 (with surrogates in their three-byte form)
    b = s.encode("utf-8", "surrogatepass")
    out: list[int] = []
    i = 0
    n = len(b)
    while i < n:
        x = b[i]
        if x < 0x80:
            out.append(x)
            i += 1
        elif x < 0xE0:
            out.append((x & 0x1F) << 6 | (b[i + 1] & 0x3F))
            i += 2
        elif x < 0xF0:
            out.append((x & 0x0F) << 12 | (b[i + 1] & 0x3F) << 6 | (b[i + 2] & 0x3F))
            i += 3
        else:
            out.append((x & 0x07) << 18 | (b[i + 1] & 0x3F) << 12 | (b[i + 2] & 0x3F) << 6 | (b[i + 3] & 0x3F))
            i += 4
    return out


def _text(cs: list[int]) -> str:
    # the str of code points cs ("%c" % c is c's UTF-8, where Pystachy's chr() of one below 256 is that byte)
    return "".join(["%c" % c for c in cs])


# ---- the functions, of the current version (old False) or of 3.2.0 (old True)


def _decimal(c: int, old: bool) -> int:
    # decimal(), -1 for none
    if len(_numvalues) == 0:
        _decode_numeric()
    if old and _unassigned_3_2_0(c):
        return -1
    i = _find(_num32[0], c) if old else -1
    if i >= 0:
        return _num32[1][i] - 1
    i = _find(_num[0], c)
    return _num[1][i] - 1 if i >= 0 else -1


def _digit(c: int) -> int:
    # digit(), -1 for none (also 3.2.0's: CPython's digit() reads no change record)
    if len(_numvalues) == 0:
        _decode_numeric()
    i = _find(_num[0], c)
    return _num[2][i] - 1 if i >= 0 else -1


def _numeric(c: int, old: bool) -> float:
    # numeric(), -1.0 for none
    if len(_numvalues) == 0:
        _decode_numeric()
    if old and _unassigned_3_2_0(c):
        return -1.0
    i = _find(_num32[0], c) if old else -1
    if i >= 0:
        k = _num32[2][i]
    else:
        i = _find(_num[0], c)
        k = _num[3][i] if i >= 0 else 0
    return _numvalues[k - 1] if k > 0 else -1.0


def _decomposition(c: int, old: bool) -> str:
    if old and _unassigned_3_2_0(c):
        return ""
    if _SBASE <= c < _SBASE + _SCOUNT:
        s = c - _SBASE
        lv = f"{_LBASE + s // _NCOUNT:04X} {_VBASE + (s % _NCOUNT) // _TCOUNT:04X}"
        return lv if s % _TCOUNT == 0 else f"{lv} {_TBASE + s % _TCOUNT:04X}"
    at = _decomp_of(c)
    if at < 0:
        return ""
    data = _dec[2]
    parts = [_tags[data[at] // 32]] if data[at] >= 32 else []
    for j in range(at + 1, at + 1 + data[at] % 32):
        parts.append(f"{data[j]:04X}")
    return " ".join(parts)


def _combining(c: int) -> int:
    # (the current version's, which normalize() orders by, also 3.2.0's)
    return _props[_record(c, False) + 4]


def _nfd(cs: list[int], k: bool, old: bool) -> list[int]:
    # the canonical (k: compatibility) decomposition of cs, in canonical order (nfd_nfkd)
    out: list[int] = []
    stack: list[int] = []
    for x in cs:
        stack.append(x)
        while len(stack) > 0:
            code = stack.pop()
            if _SBASE <= code < _SBASE + _SCOUNT:
                s = code - _SBASE
                out.append(_LBASE + s // _NCOUNT)
                out.append(_VBASE + (s % _NCOUNT) // _TCOUNT)
                if s % _TCOUNT != 0:
                    out.append(_TBASE + s % _TCOUNT)
                continue
            if old and code in _norm32:
                stack.append(_norm32[code])
                continue
            at = -1 if old and _unassigned_3_2_0(code) else _decomp_of(code)
            data = _dec[2]
            if at < 0 or (data[at] >= 32 and not k):
                out.append(code)  # (none, or a compatibility decomposition in NFD and NFC)
                continue
            for j in range(at + data[at] % 32, at, -1):
                stack.append(data[j])
    # each run of combining characters, sorted by their classes, stably
    i = 0
    n = len(out)
    while i < n:
        if _combining(out[i]) == 0:
            i += 1
            continue
        start = i
        while i < n and _combining(out[i]) != 0:
            i += 1
        for j in range(start + 1, i):
            code = out[j]
            cc = _combining(code)
            m = j
            while m > start and _combining(out[m - 1]) > cc:
                out[m] = out[m - 1]
                m -= 1
            out[m] = code
    return out


def _nfc(cs: list[int], k: bool, old: bool) -> list[int]:
    # the canonical (k: compatibility) composition of cs (nfc_nfkc)
    if len(_tags) == 0:
        _decode_decomp()
    data = _nfd(cs, k, old)
    n = len(data)
    out: list[int] = []
    skipped: dict[int, bool] = {}
    i = 0
    while i < n:
        if i in skipped:
            del skipped[i]
            i += 1
            continue
        code = data[i]
        if _LBASE <= code < _LBASE + _LCOUNT and i + 1 < n and _VBASE <= data[i + 1] < _VBASE + _VCOUNT:
            # a Hangul syllable of its jamo
            code = _SBASE + ((code - _LBASE) * _VCOUNT + data[i + 1] - _VBASE) * _TCOUNT
            i += 2
            if i < n and _TBASE < data[i] < _TBASE + _TCOUNT:
                code += data[i] - _TBASE
                i += 1
            out.append(code)
            continue
        if code not in _first:
            out.append(code)
            i += 1
            continue
        # the characters after it that are not blocked, combined with it in turn
        i1 = i + 1
        comb = 0
        while i1 < n:
            code1 = data[i1]
            comb1 = _combining(code1)
            if comb != 0:
                if comb1 == 0:
                    break
                if comb >= comb1:
                    i1 += 1  # (blocked)
                    continue
            key = code * 0x110000 + code1
            if key not in _comp:
                if comb1 == 0:
                    break
                comb = comb1
                i1 += 1
                continue
            code = _comp[key]
            skipped[i1] = True
            i1 += 1
            if code not in _first:
                break
        out.append(code)
        i += 1
    return out


def _normalize(form: str, s: str, old: bool) -> str:
    if len(s) == 0:
        return s  # (before the form is checked, as CPython's)
    if form != "NFC" and form != "NFKC" and form != "NFD" and form != "NFKD":
        raise ValueError("invalid normalization form")
    k = form == "NFKC" or form == "NFKD"
    cs = _codes(s)
    return _text(_nfc(cs, k, old) if form == "NFC" or form == "NFKC" else _nfd(cs, k, old))


# ---- the names, of _pystachy_unicodedata_names, decoded the first time name() or lookup() reads them
_nm: list[int] = []  # (NAMES' numbers: for each name, the distance, the number of its words, their indexes)
_name_cp: list[int] = []  # (the named code points)
_name_at: list[int] = []  # (where each one's number of words is in _nm)
_word_start: list[int] = []  # (where each of WORDS' words starts in it, and ends)
_word_end: list[int] = []
_word_order: list[int] = []  # (the words' indexes in the words' order)
_suffix_prefix: list[str] = []  # (the prefixes of names that end in their code point in hex)
_suffix_ranges: list[list[int]] = []
_cjk: list[int] = []  # (the code points of the derived names CJK UNIFIED IDEOGRAPH-XXXX, as ranges)
_tangut: list[int] = []  # (and TANGUT IDEOGRAPH-XXXX's, which only lookup() takes)
_aliases: dict[str, int] = {}  # (an alias: its character's code point, which ucd_3_2_0.lookup() rejects)
_sequences: dict[str, str] = {}  # (a named sequence's name: its characters)


def _ranges(text: str, out: list[int]) -> None:
    vs = _numbers(text)
    at = 0
    for i in range(0, len(vs), 2):
        at += vs[i]
        out.append(at)
        at += vs[i + 1]
        out.append(at)


def _in(ranges: list[int], c: int) -> bool:
    return _bisect(ranges, c) % 2 == 1


def _decode_names() -> None:
    for v in _numbers(_n.NAMES):
        _nm.append(v)
    at = 0
    i = 0
    while i < len(_nm):
        at += _nm[i]
        _name_cp.append(at)
        _name_at.append(i + 1)
        i += 2 + _nm[i + 1]
    start = 0
    w = _n.WORDS
    for i in range(len(w) + 1):
        if i == len(w) or w[i] == " ":
            _word_start.append(start)
            _word_end.append(i)
            start = i + 1
    for v in _numbers(_n.WORD_ORDER):
        _word_order.append(v)
    for entry in _n.SUFFIXED:
        cut = entry.find(":")
        rs: list[int] = []
        _ranges(entry[cut + 1 :], rs)
        _suffix_prefix.append(entry[:cut])
        _suffix_ranges.append(rs)
    _ranges(_n.CJK, _cjk)
    _ranges(_n.TANGUT, _tangut)
    for entry in _n.ALIASES:
        cut = entry.find(":")
        _aliases[entry[cut + 1 :]] = int(entry[:cut], 16)
    for entry in _n.NAMED_SEQUENCES:
        cut = entry.find(":")
        _sequences[entry[cut + 1 :]] = _text([int(w, 16) for w in entry[:cut].split()])


def _word(i: int) -> str:
    return _n.WORDS[_word_start[i] : _word_end[i]]


def _word_index(w: str) -> int:
    # the index in WORDS of word w, -1 if it is none of them
    lo = 0
    hi = len(_word_order)
    while lo < hi:
        mid = (lo + hi) // 2
        if _word(_word_order[mid]) < w:
            lo = mid + 1
        else:
            hi = mid
    return _word_order[lo] if lo < len(_word_order) and _word(_word_order[lo]) == w else -1


def _regular(up: str) -> int:
    # the code point of the regular name up (in upper case), -1 for none: its words' indexes,
    # sought among the names'
    ws = [_word_index(w) for w in up.split(" ")]
    for x in ws:
        if x < 0:
            return -1
    n = len(ws)
    for e in range(len(_name_cp)):
        at = _name_at[e]
        if _nm[at] == n and _nm[at + 1] == ws[0]:
            same = True
            for j in range(1, n):
                if _nm[at + 1 + j] != ws[j]:
                    same = False
                    break
            if same:
                return _name_cp[e]
    return -1


def _name(c: int, old: bool) -> str:
    # name(), "" for none (_getucname)
    if old and _unassigned_3_2_0(c):
        return ""
    if _SBASE <= c < _SBASE + _SCOUNT:
        s = c - _SBASE
        return "HANGUL SYLLABLE " + _JAMO_L[s // _NCOUNT] + _JAMO_V[(s % _NCOUNT) // _TCOUNT] + _JAMO_T[s % _TCOUNT]
    if len(_name_at) == 0:
        _decode_names()
    if _in(_cjk, c):
        return f"CJK UNIFIED IDEOGRAPH-{c:04X}"
    e = _find(_name_cp, c)
    if e >= 0:
        at = _name_at[e]
        return " ".join([_word(_nm[at + 1 + j]) for j in range(_nm[at])])
    for k in range(len(_suffix_prefix)):
        if _in(_suffix_ranges[k], c):
            return f"{_suffix_prefix[k]}-{c:04X}"
    return ""


def _upper(s: str) -> str:
    # s with its ASCII letters in upper case, as CPython's Py_TOUPPER compares names
    return "".join([chr(ord(x) - 32) if "a" <= x <= "z" else x for x in s])


def _jamo(name: str, at: int, column: list[str]) -> list[int]:
    # the longest of column's short names at name[at:], in any case: its index and its length, or
    # -1 and 0 (find_syllable)
    best = -1
    size = -1
    for i in range(len(column)):
        s = column[i]
        if len(s) > size and _upper(name[at : at + len(s)]) == s:
            best = i
            size = len(s)
    return [best, size if size >= 0 else 0]


def _hex(s: str) -> int:
    # parse_hex_code: four to six hex digits, not starting with 0, at most 0x10FFFF; else -1
    if len(s) < 4 or len(s) > 6 or s[0] == "0":
        return -1
    v = 0
    for x in _upper(s):
        if "0" <= x <= "9":
            v = v * 16 + ord(x) - 48
        elif "A" <= x <= "F":
            v = v * 16 + ord(x) - 55
        else:
            return -1
    return v if v <= 0x10FFFF else -1


def _lookup(name: str, old: bool) -> str:
    if len(name) > _NAME_MAXLEN:
        raise KeyError("name too long")
    shown = name[: name.find("\x00")] if "\x00" in name else name  # (CPython's message is the C string)
    if len(_name_at) == 0:
        _decode_names()
    up = _upper(name)
    if up.startswith("HANGUL SYLLABLE "):
        lv = _jamo(name, 16, _JAMO_L[:_LCOUNT])
        vv = _jamo(name, 16 + lv[1], _JAMO_V[:_VCOUNT])
        tv = _jamo(name, 16 + lv[1] + vv[1], _JAMO_T[:_TCOUNT])
        if lv[0] != -1 and vv[0] != -1 and tv[0] != -1 and 16 + lv[1] + vv[1] + tv[1] == len(name):
            return _text([_SBASE + (lv[0] * _VCOUNT + vv[0]) * _TCOUNT + tv[0]])
        raise KeyError(f"undefined character name '{shown}'")
    for prefix, ranges in [("CJK UNIFIED IDEOGRAPH-", _cjk), ("TANGUT IDEOGRAPH-", _tangut)]:
        if up.startswith(prefix):
            v = _hex(name[len(prefix) :])
            if v < 0 or not _in(ranges, v):
                raise KeyError(f"undefined character name '{shown}'")
            return _text([v])
    for k in range(len(_suffix_prefix)):
        prefix = _suffix_prefix[k] + "-"
        if up.startswith(prefix):
            v = _hex(up[len(prefix) :])
            if v >= 0 and _in(_suffix_ranges[k], v) and f"{v:04X}" == up[len(prefix) :]:
                return _text([v])
    if up in _sequences and not old:
        return _sequences[up]
    if up in _aliases and not old:
        return _text([_aliases[up]])
    c = _regular(up)
    if c >= 0:
        return _text([c])
    raise KeyError(f"undefined character name '{shown}'")


def _property(c: int, old: bool, k: int) -> int:
    return _props[_record(c, old) + k]


# ---- the module's functions, with CPython's signatures and docstrings


def decimal(chr: str, /, *default):
    """Converts a Unicode character into its equivalent decimal value.

Returns the decimal value assigned to the character chr as integer.
If no such value is defined, default is returned, or, if not given,
ValueError is raised."""
    if len(default) > 1:
        raise TypeError(f"decimal expected at most 2 arguments, got {len(default) + 1}")
    v = _decimal(_code(chr, "decimal() argument 1"), False)
    if v >= 0:
        return v
    if len(default) == 0:
        raise ValueError("not a decimal")
    else:
        return default[0]  # (the length of default is known as the program compiles)


def digit(chr: str, /, *default):
    """Converts a Unicode character into its equivalent digit value.

Returns the digit value assigned to the character chr as integer.
If no such value is defined, default is returned, or, if not given,
ValueError is raised."""
    if len(default) > 1:
        raise TypeError(f"digit expected at most 2 arguments, got {len(default) + 1}")
    v = _digit(_code(chr, "digit() argument 1"))
    if v >= 0:
        return v
    if len(default) == 0:
        raise ValueError("not a digit")
    else:
        return default[0]  # (the length of default is known as the program compiles)


def numeric(chr: str, /, *default):
    """Converts a Unicode character into its equivalent numeric value.

Returns the numeric value assigned to the character chr as float.
If no such value is defined, default is returned, or, if not given,
ValueError is raised."""
    if len(default) > 1:
        raise TypeError(f"numeric expected at most 2 arguments, got {len(default) + 1}")
    v = _numeric(_code(chr, "numeric() argument 1"), False)
    if v != -1.0:
        return v
    if len(default) == 0:
        raise ValueError("not a numeric character")
    else:
        return default[0]  # (the length of default is known as the program compiles)


def category(chr: str, /) -> str:
    """Returns the general category assigned to the character chr as string."""
    return _cats[_property(_code(chr, "category() argument"), False, 0)]


def bidirectional(chr: str, /) -> str:
    """Returns the bidirectional class assigned to the character chr as string.

If no such value is defined, an empty string is returned."""
    return _bidis[_property(_code(chr, "bidirectional() argument"), False, 1)]


def combining(chr: str, /) -> int:
    """Returns the canonical combining class assigned to the character chr as integer.

Returns 0 if no combining class is defined."""
    return _property(_code(chr, "combining() argument"), False, 4)


def mirrored(chr: str, /) -> int:
    """Returns the mirrored property assigned to the character chr as integer.

Returns 1 if the character has been identified as a "mirrored"
character in bidirectional text, 0 otherwise."""
    return _property(_code(chr, "mirrored() argument"), False, 3)


def east_asian_width(chr: str, /) -> str:
    """Returns the east asian width assigned to the character chr as string."""
    return _eaws[_property(_code(chr, "east_asian_width() argument"), False, 2)]


def decomposition(chr: str, /) -> str:
    """Returns the character decomposition mapping assigned to the character chr as string.

An empty string is returned in case no such mapping is defined."""
    return _decomposition(_code(chr, "decomposition() argument"), False)


def is_normalized(form: str, unistr: str, /) -> bool:
    """Return whether the Unicode string unistr is in the normal form 'form'.

Valid values for form are 'NFC', 'NFKC', 'NFD', and 'NFKD'."""
    return _normalize(form, unistr, False) == unistr


def normalize(form: str, unistr: str, /) -> str:
    """Return the normal form 'form' for the Unicode string unistr.

Valid values for form are 'NFC', 'NFKC', 'NFD', and 'NFKD'."""
    return _normalize(form, unistr, False)


def name(chr: str, /, *default):
    """Returns the name assigned to the character chr as a string.

If no name is defined, default is returned, or, if not given,
ValueError is raised."""
    if len(default) > 1:
        raise TypeError(f"name expected at most 2 arguments, got {len(default) + 1}")
    v = _name(_code(chr, "name() argument 1"), False)
    if v != "":
        return v
    if len(default) == 0:
        raise ValueError("no such name")
    else:
        return default[0]  # (the length of default is known as the program compiles)


def lookup(name: str, /) -> str:
    """Look up character by name.

If a character with the given name is found, return the
corresponding character.  If not found, KeyError is raised."""
    return _lookup(name, False)


_made: list[bool] = []  # (once ucd_3_2_0 is made: CPython makes no other UCD object)


class UCD:
    # (CPython's unicodedata.UCD, whose one object is ucd_3_2_0: the database of Unicode 3.2.0)
    def __init__(self, version: str) -> None:
        if len(_made) > 0:
            raise TypeError("cannot create 'unicodedata.UCD' instances")
        self.unidata_version = version

    def decimal(self, chr: str, /, *default):
        """Converts a Unicode character into its equivalent decimal value.

Returns the decimal value assigned to the character chr as integer.
If no such value is defined, default is returned, or, if not given,
ValueError is raised."""
        if len(default) > 1:
            raise TypeError(f"decimal expected at most 2 arguments, got {len(default) + 1}")
        v = _decimal(_code(chr, "decimal() argument 1"), True)
        if v >= 0:
            return v
        if len(default) == 0:
            raise ValueError("not a decimal")
        else:
            return default[0]  # (the length of default is known as the program compiles)

    def digit(self, chr: str, /, *default):
        """Converts a Unicode character into its equivalent digit value.

Returns the digit value assigned to the character chr as integer.
If no such value is defined, default is returned, or, if not given,
ValueError is raised."""
        if len(default) > 1:
            raise TypeError(f"digit expected at most 2 arguments, got {len(default) + 1}")
        v = _digit(_code(chr, "digit() argument 1"))
        if v >= 0:
            return v
        if len(default) == 0:
            raise ValueError("not a digit")
        else:
            return default[0]  # (the length of default is known as the program compiles)

    def numeric(self, chr: str, /, *default):
        """Converts a Unicode character into its equivalent numeric value.

Returns the numeric value assigned to the character chr as float.
If no such value is defined, default is returned, or, if not given,
ValueError is raised."""
        if len(default) > 1:
            raise TypeError(f"numeric expected at most 2 arguments, got {len(default) + 1}")
        v = _numeric(_code(chr, "numeric() argument 1"), True)
        if v != -1.0:
            return v
        if len(default) == 0:
            raise ValueError("not a numeric character")
        else:
            return default[0]  # (the length of default is known as the program compiles)

    def category(self, chr: str, /) -> str:
        """Returns the general category assigned to the character chr as string."""
        return _cats[_property(_code(chr, "category() argument"), True, 0)]

    def bidirectional(self, chr: str, /) -> str:
        """Returns the bidirectional class assigned to the character chr as string.

If no such value is defined, an empty string is returned."""
        return _bidis[_property(_code(chr, "bidirectional() argument"), True, 1)]

    def combining(self, chr: str, /) -> int:
        """Returns the canonical combining class assigned to the character chr as integer.

Returns 0 if no combining class is defined."""
        return _property(_code(chr, "combining() argument"), True, 4)

    def mirrored(self, chr: str, /) -> int:
        """Returns the mirrored property assigned to the character chr as integer.

Returns 1 if the character has been identified as a "mirrored"
character in bidirectional text, 0 otherwise."""
        return _property(_code(chr, "mirrored() argument"), True, 3)

    def east_asian_width(self, chr: str, /) -> str:
        """Returns the east asian width assigned to the character chr as string."""
        return _eaws[_property(_code(chr, "east_asian_width() argument"), True, 2)]

    def decomposition(self, chr: str, /) -> str:
        """Returns the character decomposition mapping assigned to the character chr as string.

An empty string is returned in case no such mapping is defined."""
        return _decomposition(_code(chr, "decomposition() argument"), True)

    def is_normalized(self, form: str, unistr: str, /) -> bool:
        """Return whether the Unicode string unistr is in the normal form 'form'.

Valid values for form are 'NFC', 'NFKC', 'NFD', and 'NFKD'."""
        return _normalize(form, unistr, True) == unistr

    def normalize(self, form: str, unistr: str, /) -> str:
        """Return the normal form 'form' for the Unicode string unistr.

Valid values for form are 'NFC', 'NFKC', 'NFD', and 'NFKD'."""
        return _normalize(form, unistr, True)

    def name(self, chr: str, /, *default):
        """Returns the name assigned to the character chr as a string.

If no name is defined, default is returned, or, if not given,
ValueError is raised."""
        if len(default) > 1:
            raise TypeError(f"name expected at most 2 arguments, got {len(default) + 1}")
        v = _name(_code(chr, "name() argument 1"), True)
        if v != "":
            return v
        if len(default) == 0:
            raise ValueError("no such name")
        else:
            return default[0]  # (the length of default is known as the program compiles)

    def lookup(self, name: str, /) -> str:
        """Look up character by name.

If a character with the given name is found, return the
corresponding character.  If not found, KeyError is raised."""
        return _lookup(name, True)


ucd_3_2_0 = UCD("3.2.0")
_made.append(True)
