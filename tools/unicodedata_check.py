"""Check lib/_pystachy_unicodedata.py on CPython against CPython's C module unicodedata.

For every code point, the port's category(), bidirectional(), east_asian_width(), mirrored(),
combining(), decomposition(), decimal(), digit(), numeric() and name() must give what CPython's
give, also ucd_3_2_0's; lookup() must take every name name() gives, the aliases and named
sequences, and the derived names, and reject what CPython rejects; normalize() and is_normalized()
of random strings (of characters that decompose, compose and reorder, Hangul and unassigned
ones) must agree in the four forms of both versions. The functions must have the C module's
signatures (but for default, which the port takes as *default) and docstrings.
Usage: python3 -I tools/unicodedata_check.py [--rounds N]
"""
import argparse
import importlib.util
import inspect
from pathlib import Path
import random
import sys
import unicodedata

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.dont_write_bytecode = True  # (no __pycache__ in lib/)
sys.path.insert(0, str(LIB))  # (the port imports its tables)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def outcome(f, *args):
    try:
        return repr(f(*args))
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=50000)
    options = parser.parse_args()
    port = load("_unicodedata_port", LIB / "_pystachy_unicodedata.py")
    gen = random.Random(20261016)
    count = failures = 0

    def report(what, got, want):
        nonlocal failures
        failures += 1
        if failures <= 20:
            print(f"{what}: {got}, where CPython's is {want}")

    def same(what, got, want):
        nonlocal count
        count += 1
        if got != want:
            report(what, got, want)

    props = ["category", "bidirectional", "east_asian_width", "mirrored", "combining", "decomposition"]
    values = ["decimal", "digit", "numeric", "name"]
    for c in range(sys.maxunicode + 1):
        ch = chr(c)
        for mine, theirs, v in ((port, unicodedata, ""), (port.ucd_3_2_0, unicodedata.ucd_3_2_0, "ucd_3_2_0.")):
            got = tuple(getattr(mine, f)(ch) for f in props) + tuple(getattr(mine, f)(ch, None) for f in values)
            want = tuple(getattr(theirs, f)(ch) for f in props) + tuple(getattr(theirs, f)(ch, None) for f in values)
            count += 1
            if got != want:
                report(f"{v}properties of U+{c:04X}", got, want)
            n = want[-1]
            if n is not None:
                same(f"{v}lookup({n!r})", outcome(mine.lookup, n), outcome(theirs.lookup, n))
                low = n.lower()
                same(f"{v}lookup({low!r})", outcome(mine.lookup, low), outcome(theirs.lookup, low))
    # the errors without a default, of a code point without the value
    for f in values:
        for ch in ("\U000e0000", "a", ""):
            same(f"{f}({ch!r})", outcome(getattr(port, f), ch), outcome(getattr(unicodedata, f), ch))
            same(f"{f}({ch!r}, 1, 2)", outcome(getattr(port, f), ch, 1, 2), outcome(getattr(unicodedata, f), ch, 1, 2))
    for f in props + values:
        for s in ("", "ab", "é́"):
            same(f"{f}({s!r})", outcome(getattr(port, f), s), outcome(getattr(unicodedata, f), s))
    # lookup() of the aliases, the named sequences and derived names (also not quite ones)
    for path in (LIB / "_pystachy_unicodedata_names.py",):
        names = load("_names_check", path)
        for entry in names.ALIASES + names.NAMED_SEQUENCES:
            n = entry[entry.find(":") + 1:]
            for v, mine, theirs in (("", port, unicodedata), ("ucd_3_2_0.", port.ucd_3_2_0, unicodedata.ucd_3_2_0)):
                same(f"{v}lookup({n!r})", outcome(mine.lookup, n), outcome(theirs.lookup, n))
    probes = ["", " ", "A", "a", "LATIN SMALL LETTER A ", " LATIN SMALL LETTER A", "LATIN SMALL  LETTER A", "x" * 256, "x" * 257,
              "LATIN SMALL LETTER A\x00B", "é", "HANGUL SYLLABLE ", "HANGUL SYLLABLE G", "HANGUL SYLLABLE GA ",
              "hangul syllable gaga", "HANGUL SYLLABLE GGAEGG", "Hangul Syllable Ae", "HANGUL SYLLABLE YIH",
              "CJK UNIFIED IDEOGRAPH-", "CJK UNIFIED IDEOGRAPH-4E0", "CJK UNIFIED IDEOGRAPH-04E00", "CJK UNIFIED IDEOGRAPH-4e00",
              "CJK UNIFIED IDEOGRAPH-2A6DF", "CJK UNIFIED IDEOGRAPH-2A6E0", "CJK UNIFIED IDEOGRAPH-110000", "CJK UNIFIED IDEOGRAPH-4E00X",
              "TANGUT IDEOGRAPH-17000", "tangut ideograph-187f7", "TANGUT IDEOGRAPH-18800", "TANGUT IDEOGRAPH-18D00",
              "CJK COMPATIBILITY IDEOGRAPH-F900", "cjk compatibility ideograph-f900", "CJK COMPATIBILITY IDEOGRAPH-0F900",
              "NUSHU CHARACTER-1B170", "KHITAN SMALL SCRIPT CHARACTER-18B00", "LATIN SMALL LETTER R WITH TILDE"]
    jamo = port._JAMO_L + port._JAMO_V + port._JAMO_T + ["X", "Q", "-"]
    for r in range(2000):
        probes.append("HANGUL SYLLABLE " + "".join(gen.choice(jamo) for i in range(gen.randrange(4))))
        probes.append(gen.choice(["CJK UNIFIED IDEOGRAPH-", "TANGUT IDEOGRAPH-"]) + f"{gen.randrange(0x10000, 0x40000):X}")
    for n in probes:
        for v, mine, theirs in (("", port, unicodedata), ("ucd_3_2_0.", port.ucd_3_2_0, unicodedata.ucd_3_2_0)):
            same(f"{v}lookup({n[:40]!r})", outcome(mine.lookup, n), outcome(theirs.lookup, n))
    # normalize() and is_normalized() of random strings
    pool = [c for c in range(0x30000) if unicodedata.decomposition(chr(c)) or unicodedata.combining(chr(c))]
    pool += [0xAC00, 0xAC01, 0xD7A3, 0x1100, 0x1112, 0x1161, 0x1175, 0x11A7, 0x11A8, 0x11C2, 0x11C3, 0x0378, 0xE000,
             0x2F868, 0x2F874, 0x2F91F, 0x2F95F, 0x2F9BF, 0x1F600, 0x10FFFF, 0xD800, 0xDFFF]
    pool += [ord(x) for x in "aeiouAEIOUcCsnNkKgGhH0 "]
    for r in range(options.rounds):
        s = "".join(chr(gen.choice(pool)) for i in range(gen.randrange(1, 12)))
        if r % 3 == 0:
            s = unicodedata.normalize(gen.choice(["NFC", "NFD", "NFKC", "NFKD"]), s)
        for form in ("NFC", "NFD", "NFKC", "NFKD"):
            for v, mine, theirs in (("", port, unicodedata), ("ucd_3_2_0.", port.ucd_3_2_0, unicodedata.ucd_3_2_0)):
                same(f"{v}normalize({form!r}, {s!r})", outcome(mine.normalize, form, s), outcome(theirs.normalize, form, s))
                same(f"{v}is_normalized({form!r}, {s!r})", outcome(mine.is_normalized, form, s), outcome(theirs.is_normalized, form, s))
    for form, s in (("NFX", "a"), ("nfc", "a"), ("NFX", ""), ("", "")):
        same(f"normalize({form!r}, {s!r})", outcome(port.normalize, form, s), outcome(unicodedata.normalize, form, s))
        same(f"is_normalized({form!r}, {s!r})", outcome(port.is_normalized, form, s), outcome(unicodedata.is_normalized, form, s))
    same("UCD('x')", outcome(port.UCD, "x"), outcome(unicodedata.UCD, "x"))
    # the signatures and docstrings
    for n in props + values + ["lookup", "normalize", "is_normalized"]:
        a = getattr(unicodedata, n)
        for b in (getattr(port, n), getattr(port.UCD, n)):
            same(f"{n}.__doc__", (b.__doc__ or "").rstrip(), (a.__doc__ or "").rstrip())
        mine = str(inspect.signature(getattr(port, n))).split(" -> ")[0].replace(": str", "")
        want = a.__text_signature__.replace("$self, ", "").replace(", default=<unrepresentable>, /", ", /, *default")
        same(f"{n} signature", mine, want)
    same("__doc__", port.__doc__, unicodedata.__doc__)
    same("unidata_version", port.unidata_version, unicodedata.unidata_version)
    same("ucd_3_2_0.unidata_version", port.ucd_3_2_0.unidata_version, unicodedata.ucd_3_2_0.unidata_version)
    print(f"{count} checks, {failures} differ")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
