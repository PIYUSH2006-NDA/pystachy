"""What a port's edits are: its "Pystachy port:" markers by cause, and the census blockers they remove.

usage: python3 -I tools/port_edits.py [PORT[=UPSTREAM] ...]
PORT is a port's directory (default: each directory under ports/). Its markers are sorted by
cause, the roadmap milestone (#5) that would make the edit unnecessary, with keyword rules on
the marker's text; the rules are heuristic, and a marker that says only "see above" takes the
cause of the marker before it. With UPSTREAM, the upstream package's directory (or its .py file,
for a package of one module), tools/census.py scans the upstream modules the port keeps and the
port, and the blockers whose counts differ are listed, "unannotated" split into functions
(compiled as templates) and methods (rejected until classes are templates). #171 reports a run
over 14 ports.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
CENSUS = os.path.join(TOOLS, "census.py")

# The first rule that matches a marker's text, lowercased, gives its cause.
RULES = [
    ("notice", r"changed for pystachy on|each change is marked|lists them|end copy|this file is not|is copied here|changed where a|comment says"),
    ("M7 long tail", r"^\s*append\(\)"),
    ("scope cut", r"grapheme_"),
    ("UTF-8 text (#120)", r"#120|code point|whose iteration steps|utf-8|_chars|pwcs"),
    ("M4 dynamic values", r"literals and tables hold keys|was tables\.|was literals\.|for k, v in literals|is_aot|obj: mapping|obj: tuple|array_types|whose tables are written|mappingproxytype|vs1[56]_"),
    ("M1 loader, annotations", r"tuple of \d+ tuples|a tuple is indexed only|^\s*a list\s*$|list\(\)\s*$|a dict filled by loops|variable-length tuples|their types are|for the else above"),
    ("M6 stdlib", r"moved from the module level|for earthgravity|^\s*gravity"),
    ("M2 classes", r"for list\[among\]"),
    ("M7 long tail", r"iter\(|next\(|steps? `|`continue` would not"),
    ("M3 functions as values", r"imported above|for _wcwidth"),
    ("scope cut", r"image factory"),
    ("M3 functions as values", r"\bm3\b|#8\b|lambda|key=|function as a value|functions? (are|is) not (a )?values?|not a value|closure|nested function|decorat|reduce\(|\bmap\(|method=|no w\.method|alias|star\b|\*args"),
    ("M2 classes", r"inherit|subclass|base class|base\b.*left out|generic\[|__class__|type\(self\)|classes as|holds classes|values are classes|copy of basestemmer|class body"),
    ("M4 dynamic values", r"\bm4\b|#9\b|\bany\b|union|optional|may be none|\bnone\b|object\b|isinstance|mixed|rebound|rebind|keeps its argument|not rebound|narrowed"),
    ("M7 long tail", r"str\.format|\.format\(|%r|percent|\bsets?\b|set\(|frozenset|\|=|generator|yield|bytes|bytearray|#125|unsigned|\bm7\b|#12\b|slice|del of|del \w+\[|tuple indexed|only a constant indexes"),
    ("M6 stdlib", r"\bm6\b|#11\b|#129|itertools|functools|\bre\b|remagic|regex|collections|importlib|pathlib|chain|operator|warnings|\benum\b|copy\.copy|calendar|argparse|struct|math\.|datetime|namedtuple|\bfonts?\b|isatty"),
    ("M1 loader, annotations", r"\bm1\b|#6\b|#121|#116|#122|python 2|xrange|version|type_checking|startswith|quoted|#17\b|\\n\{"),
    ("M2 classes", r"\bm2\b|#7\b|annotat|-> ?\w|field|property|setter|declared"),
    ("scope cut", r"left out|not ported|not imported|dropped|removed|omitted|only the|pymeeus|no _languages|need"),
]


def cause(note):
    for name, pat in RULES:
        if re.search(pat, note):
            return name
    return "see above" if re.search(r"see above|as above|\(same\)|\(see", note) else "other"


def modules(port):
    """The .py files under port, by their path there."""
    out = []
    for dp, dn, fn in os.walk(port):
        dn.sort()
        out += [os.path.relpath(os.path.join(dp, f), port) for f in sorted(fn) if f.endswith(".py")]
    return out


def markers(port):
    counts = {}
    for rel in modules(port):
        prev = "other"
        for line in open(os.path.join(port, rel), encoding="utf-8"):
            if "Pystachy port:" in line:
                c = cause(line.split("Pystachy port:", 1)[1].lower())
                prev = prev if c == "see above" else c
                if prev != "notice":
                    counts[prev] = counts.get(prev, 0) + 1
    return counts


def census(root):
    """The census's blocker counts over root, "unannotated" split by the kind of unit."""
    with tempfile.TemporaryDirectory() as tmp:
        js = os.path.join(tmp, "census.json")
        subprocess.run([sys.executable, "-I", CENSUS, root, "--json", js], check=True, stdout=subprocess.DEVNULL)
        rows = json.load(open(js))
    counts = {}
    for r in rows:
        if "error" in r:  # a module the census could not read or parse: no counts rather than zeros
            sys.exit(f"tools/census.py cannot scan the {os.path.basename(root)}'s module {r['module']}: {r['error']}")
        for k, n in r.get("blockers", {}).items():
            k = k + " " + r["kind"] if k == "unannotated" else k
            counts[k] = counts.get(k, 0) + n
    return counts


def compare(port, upstream):
    """Print the census blockers of the modules the port keeps from upstream, upstream's against the port's."""
    with tempfile.TemporaryDirectory() as tmp:
        n, only = 0, []
        for rel in modules(port):
            src = upstream if os.path.isfile(upstream) and rel == "__init__.py" else os.path.join(upstream, rel)
            if not os.path.isfile(src):
                only.append(rel)
                continue
            n += 1
            for side, path in (("upstream", src), ("port", os.path.join(port, rel))):
                os.makedirs(os.path.dirname(os.path.join(tmp, side, rel)), exist_ok=True)
                shutil.copyfile(path, os.path.join(tmp, side, rel))
        up, po = census(os.path.join(tmp, "upstream")), census(os.path.join(tmp, "port"))
    diff = sorted((k for k in set(up) | set(po) if up.get(k, 0) != po.get(k, 0)),
                  key=lambda k: (po.get(k, 0) - up.get(k, 0), k))
    print(f"  census blockers, upstream -> port, in the {n} module{'s' * (n != 1)} the port keeps"
          + (f" (only in the port: {', '.join(only)})" if only else "") + (":" if diff else ": no change"))
    for k in diff:
        print(f"  {up.get(k, 0):6} -> {po.get(k, 0):<4} {k}")


def main():
    ports = os.path.relpath(os.path.join(TOOLS, "..", "ports"))
    args = sys.argv[1:] or [os.path.join(ports, d) for d in sorted(os.listdir(ports))
                            if os.path.isdir(os.path.join(ports, d))]
    total = {}
    for a in args:
        port, _, upstream = a.partition("=")
        for path in (port, upstream):
            if path and not os.path.exists(path):
                sys.exit(f"{path}: no such file or directory")
        if not os.path.isdir(port):
            sys.exit(f"{port}: not a port's directory")
        counts = markers(port)
        n = sum(counts.values())
        print(f"{port}: {n} marker{'s' * (n != 1)}")
        for c, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {n:6}  {c}")
            total[c] = total.get(c, 0) + n
        if upstream:
            compare(port, upstream)
    if len(args) > 1:
        n = sum(total.values())
        print(f"{n} markers in {len(args)} ports")
        for c, k in sorted(total.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {k:6}  {100 * k / max(n, 1):4.1f}%  {c}")


main()
