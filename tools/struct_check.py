"""Check lib/_pystachy_struct.py on CPython against CPython's C module _struct.

The compiler parses a format it knows and packs and unpacks each item through the port's
functions (Gen.struct_call); this composes them the same way, item by item, for random formats
and values, and compares the bytes, the values and the errors with those of _struct: the integer
codes at the edges of their ranges and beyond, the float codes with signed zeros, subnormals,
infinities, NaNs and ties of rounding, the bytes codes cut and padded, unpack_from()'s offsets
and iter_unpack()'s buffers. calcsize() runs on random formats, also invalid ones. The port's
functions must have the C module's signatures, docstrings and names.
Usage: python3 -I tools/struct_check.py [--rounds N]
"""
import _struct
import argparse
import importlib.util
import inspect
import math
from pathlib import Path
import random
import sys

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.dont_write_bytecode = True  # (no __pycache__ in lib/)
INTS = "bBhHiIlLqQnNP"
CODES = INTS + "efd?csp"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def outcome(f, args):
    try:
        r = f(*args)
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    return repr(r) if not isinstance(r, float) else repr(r) + ("-" if math.copysign(1.0, r) < 0 else "")


def items(port, fmt):
    # the items of a valid format as the compiler parses it: (code, count, offset), the size, the
    # byte order and whether it is native (CPython's prepare_s)
    native = True
    little = True
    i = 0
    if fmt and fmt[0] in "@=<>!":
        native = fmt[0] == "@"
        little = fmt[0] in "@=<"
        i = 1
    table = port._NATIVE if native else port._STANDARD
    out = []
    size = 0
    while i < len(fmt):
        c = fmt[i]
        i += 1
        if c.isspace():
            continue
        num = 1
        if c.isdigit():
            j = i - 1
            while fmt[i].isdigit():
                i += 1
            num = int(fmt[j:i])
            c = fmt[i]
            i += 1
        k = table[c]
        if native and size > 0 and k > 1:
            size += (k - 1) - (size - 1) % k
        if c not in "x" and (num or c in "sp"):
            out.append((c, num, size))
        size += num * k
    return out, size, little, native


def pack(port, fmt, values):
    # struct.pack(fmt, *values) through the port's functions, as the compiler composes the call
    its, size, little, native = items(port, fmt)
    n = sum(1 if c in "sp" else count for c, count, _ in its)
    if len(values) != n:
        raise port.error(f"pack expected {n} items for packing (got {len(values)})")
    table = port._NATIVE if native else port._STANDARD
    out = bytearray(size)
    j = 0
    for c, count, off in its:
        for r in range(1 if c in "sp" else count):
            v = values[j]
            j += 1
            if c in "sp":
                b = port._pack_bytes(v, count, c == "p")
            elif c == "c":
                b = port._pack_char(v)
            elif c == "?":
                b = bytes([1 if v else 0])
            elif c in "efd":
                b = port._pack_float(c, float(v), little)
            else:
                b = port._pack_int(c, v, table[c], c in "bhilqnP", little)  # (P packs any int, as CPython's PyLong_AsVoidPtr takes one)
            at = off + (0 if c in "sp" else r * table[c])
            out[at : at + len(b)] = b
    return bytes(out)


def unpack(port, fmt, buffer, start=None):
    its, size, little, native = items(port, fmt)
    table = port._NATIVE if native else port._STANDARD
    if start is None:
        port._need(buffer, size)
        start = 0
    out = []
    for c, count, off in its:
        for r in range(1 if c in "sp" else count):
            at = start + off + (0 if c in "sp" else r * table[c])
            if c == "s":
                out.append(buffer[at : at + count])
            elif c == "p":
                out.append(port._unpack_pascal(buffer, at, count))
            elif c == "c":
                out.append(buffer[at : at + 1])
            elif c == "?":
                out.append(buffer[at] != 0)
            elif c in "efd":
                out.append(port._unpack_float(c, buffer, at, little))
            else:
                out.append(port._unpack_int(buffer, at, table[c], c in "bhilqn", little))
    return tuple(out)


def iter_offsets(fmt, buf, size):
    # where each tuple _struct.iter_unpack() gives starts
    return [i * size for i, t in enumerate(_struct.iter_unpack(fmt, buf))]


def same(a, b):
    # values as tuples of reprs, NaNs equal and signed zeros told apart
    def key(x):
        if isinstance(x, float):
            return ("f", "nan" if math.isnan(x) else repr(x), math.copysign(1.0, x))
        return ("v", repr(x))
    return [key(x) for x in a] == [key(x) for x in b]


def random_format(gen, std_only=False):
    order = gen.choice(["", "@", "=", "<", ">", "!"] if not std_only else ["<", ">", "!", "="])
    native = order in ("", "@")
    parts = []
    for i in range(gen.randrange(1, 6)):
        c = gen.choice(CODES + "x")
        if not native and c in "nNP":
            c = "q"
        count = gen.choice(["", "", "", "0", "1", "2", "3", "7"])
        parts.append(count + c)
        if gen.random() < 0.1:
            parts.append(" ")
    return order + "".join(parts)


def value_for(gen, c, count):
    if c in INTS:
        size = _struct.calcsize("@" + c) if c in "nNP" else _struct.calcsize("<" + c) if gen.random() < 0.5 else _struct.calcsize("@" + c)
        top = 1 << (8 * size)
        signed = c in "bhilqn"
        lo, hi = (-(top // 2), top // 2 - 1) if signed else (0, top - 1)
        v = gen.choice([lo, hi, lo - 1, hi + 1, 0, -1, 1, gen.randrange(lo, hi + 1), gen.randrange(-300, 300)])
        return max(min(v, 2 ** 63 - 1), -(2 ** 63))  # (Pystachy's ints)
    if c in "efd":
        return gen.choice([0.0, -0.0, 1.0, -1.5, 65504.0, 65520.0, 65519.999, 3.4028234663852886e38, 3.4028235677973366e38,
                           1e39, 1e-40, 5e-324, 2.0 ** -149, 2.0 ** -150, 3 * 2.0 ** -150, 2.0 ** -24, 2.0 ** -25,
                           math.inf, -math.inf, math.nan, -math.nan, 1e308, 0.1, 1 / 3, 1.0000001, 1 + 2 ** -24,
                           1 + 3 * 2 ** -24, 1 + 2 ** -11, 1 + 3 * 2 ** -11, gen.uniform(-1e6, 1e6),
                           math.ldexp(gen.random(), gen.randrange(-160, 140))])
    if c == "?":
        return gen.choice([True, False, 0, 3, b"", b"x"])
    if c == "c":
        return gen.choice([b"a", b"\xff", b"", b"ab"])
    return bytes(gen.randrange(256) for i in range(gen.choice([0, 1, count, count + 2, 300])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=20000)
    options = parser.parse_args()
    port = load("_struct_port", LIB / "_pystachy_struct.py")
    gen = random.Random(20261016)
    count = failures = 0

    def report(what, got, want):
        nonlocal failures
        failures += 1
        if failures <= 20:
            print(f"{what}: {got}, where CPython's is {want}")

    for r in range(options.rounds):
        fmt = random_format(gen)
        count += 1
        got = outcome(port.calcsize, (fmt,))
        want = outcome(_struct.calcsize, (fmt,))
        if got != want:
            report(f"calcsize({fmt!r})", got, want)
        if want.startswith("error"):
            continue
        its = items(port, fmt)[0]
        values = [value_for(gen, c, n) for c, n, _ in its for k in range(1 if c in "sp" else n)]
        if gen.random() < 0.05:
            values = values[:-1] if values else [1]
        count += 1
        got = outcome(lambda f, *v: pack(port, f, v), [fmt] + values)
        want = outcome(_struct.pack, [fmt] + values)
        if got != want:
            report(f"pack({fmt!r}, {values!r})", got, want)
        size = _struct.calcsize(fmt)
        data = bytes(gen.randrange(256) for i in range(size))
        if gen.random() < 0.1:
            data = data[:-1] + (b"" if gen.random() < 0.5 else b"xy")
        count += 1
        try:
            a = unpack(port, fmt, data)
        except Exception as e:
            a = f"{type(e).__name__}: {e}"
        try:
            b = _struct.unpack(fmt, data)
        except Exception as e:
            b = f"{type(e).__name__}: {e}"
        if not (isinstance(a, tuple) and isinstance(b, tuple) and same(a, b)) and a != b:
            if not (isinstance(a, str) and a.startswith("OverflowError: integer result") and isinstance(b, tuple)
                    and any(isinstance(x, int) and x >= 2 ** 63 for x in b)):
                report(f"unpack({fmt!r}, {data!r})", a, b)
        # unpack_from at an offset, also negative, and iter_unpack
        buf = bytes(gen.randrange(256) for i in range(gen.randrange(0, 3 * size + 3)))
        off = gen.randrange(-len(buf) - 2, len(buf) + 2)
        count += 1
        got = outcome(port._offset, (buf, off, size))
        want_t = outcome(_struct.unpack_from, (fmt, buf, off))
        if got.startswith("error") != want_t.startswith("error") or (got.startswith("error") and got != want_t):
            report(f"unpack_from({fmt!r}, {len(buf)} bytes, {off})", got, want_t)
        count += 1
        got = outcome(port._offsets, (buf, size))
        want_i = outcome(iter_offsets, (fmt, buf, size))
        if got != want_i:
            report(f"iter_unpack({fmt!r}, {len(buf)} bytes)", got, want_i)
    # the C module's names, signatures and docstrings
    names = sorted(n for n in dir(_struct) if not n.startswith("__"))
    for n in names:
        a = getattr(_struct, n)
        b = getattr(port, n, None)
        count += 1
        if b is None:
            report(n, "missing", "defined")
            continue
        if n == "error":
            continue
        if (a.__doc__ or "").rstrip() != (b.__doc__ or "").rstrip():
            report(f"{n}.__doc__", repr(b.__doc__), repr(a.__doc__))
        sig = a.__text_signature__
        if sig is not None:
            mine = str(inspect.signature(b)).split(" -> ")[0]
            for t in (": str", ": bytes", ": int"):
                mine = mine.replace(t, "")
            if mine.replace(" = ", "=") != sig.replace("$module, ", "").replace("$module", "").replace("(, ", "(").replace("(/)", "()"):
                report(f"{n} signature", mine, sig)
    for n in ("pack", "unpack", "unpack_from", "iter_unpack"):
        count += 1
        if (getattr(_struct.Struct, n).__doc__ or "").rstrip() != (getattr(port.Struct, n).__doc__ or "").rstrip():
            report(f"Struct.{n}.__doc__", repr(getattr(port.Struct, n).__doc__), repr(getattr(_struct.Struct, n).__doc__))
    if _struct.__doc__ != port.__doc__:
        report("__doc__", repr(port.__doc__[:40]), repr(_struct.__doc__[:40]))
    print(f"{count} checks, {failures} differ")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
