"""Try to compile 'import M' for every module of a Python standard library with Pystachy.

usage: python3 tools/import_sweep.py [COMPILER] [LIBDIR] [OUT.json]
       (defaults: ./pystachy, the running CPython's stdlib directory, build/import-sweep.json)
       python3 tools/import_sweep.py --overlay [COMPILER] LIBDIR DIR
Each module is compiled (pystachy ir) in a program of its own, with LIBDIR on PYSTACHY_PATH; the
JSON maps each module to "OK", the compiler's error or a timeout, and a summary groups the errors.

PYSTACHY_PATH comes before the lib/ beside the compiler, so LIBDIR's own re, heapq, functools ...
would hide the modules lib/ has in their place. PYSTACHY_PATH is therefore a directory of symbolic
links to the entries of LIBDIR, less the modules and packages whose names lib/ has, and the sweep
leaves those out (the JSON names lib/'s module that replaces each). --overlay makes that directory
as DIR, for 'PYSTACHY_PATH=DIR pystachy run prog.py' (DIR's symbolic links are made anew).
"""
import collections
import json
import os
import subprocess
import sys
import sysconfig
import tempfile

TIMEOUT = 120  # seconds per module
SKIP = ("test", "tests", "idlelib", "tkinter", "turtledemo", "site-packages", "dist-packages", "lib2to3", "ensurepip", "venv", "__pycache__")


def modules(lib):
    out = []
    for dp, dn, fn in os.walk(lib):
        dn[:] = sorted(d for d in dn if d not in SKIP and not d.startswith("."))
        for f in sorted(fn):
            if not f.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), lib)[:-3].replace(os.sep, ".")
            if rel.endswith(".__init__"):
                rel = rel[:-9]
            if rel.endswith("__main__") or rel.startswith("__") or "-" in rel:
                continue
            out.append(rel)
    return out


def ported(pys):
    # the modules and packages of the lib/ beside the compiler, whose home is found as it finds it
    home = os.getenv("PYSTACHY_HOME", "")
    if home == "":
        home = os.path.dirname(pys)
        if not os.path.exists(os.path.join(home, "runtime.c")):
            home = os.path.dirname(home)
    lib = os.path.join(home, "lib")
    names = set()
    for e in os.listdir(lib) if os.path.isdir(lib) else []:
        if e.endswith(".py"):
            names.add(e[:-3])
        elif os.path.exists(os.path.join(lib, e, "__init__.py")):
            names.add(e)
    return names


def overlay(lib, names, out):
    # out: a symbolic link to each entry of lib, less the modules and packages called names
    os.makedirs(out, exist_ok=True)
    for e in os.listdir(out):
        if not os.path.islink(os.path.join(out, e)):
            sys.exit(f"{out} holds {e}, which is not a symbolic link")
        os.unlink(os.path.join(out, e))
    for e in sorted(os.listdir(lib)):
        if (e[:-3] if e.endswith(".py") else e) not in names:
            os.symlink(os.path.join(os.path.abspath(lib), e), os.path.join(out, e))


def main():
    args = sys.argv[1:]
    if args[:1] == ["--overlay"]:
        if len(args) not in (3, 4):
            sys.exit("usage: python3 tools/import_sweep.py --overlay [COMPILER] LIBDIR DIR")
        overlay(args[-2], ported(os.path.abspath(args[1] if len(args) == 4 else "./pystachy")), args[-1])
        return
    pys = os.path.abspath(args[0] if len(args) > 0 else "./pystachy")
    lib = (args[1] if len(args) > 1 else sysconfig.get_paths()["stdlib"]).rstrip("/")
    out = args[2] if len(args) > 2 else "build/import-sweep.json"
    names = ported(pys)
    res = {}
    left = []
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "path")
        overlay(lib, names, path)
        env = dict(os.environ, PYSTACHY_PATH=path)
        prog = os.path.join(d, "prog.py")
        for m in modules(lib):
            if m.split(".")[0] in names:
                res[m] = "left out: lib/ has " + m.split(".")[0]
                left.append(m)
                continue
            with open(prog, "w") as f:
                f.write(f"import {m}\n")
            try:
                p = subprocess.run([pys, "ir", prog, "-o", os.devnull], capture_output=True, text=True, env=env,
                                   timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                res[m] = f"timeout: no result after {TIMEOUT} s"
                continue
            err = p.stderr.strip().splitlines()
            res[m] = "OK" if p.returncode == 0 else (err[-1].replace(path + "/", lib + "/").replace(d + "/", "") if err else f"exit {p.returncode}")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    ok = sorted(m for m, v in res.items() if v == "OK")
    print(f"{len(ok)} of {len(res) - len(left)} modules import: {' '.join(ok)}\n")
    if left:
        print(f"{len(left)} left out, as lib/ has {', '.join(sorted(names & {m.split('.')[0] for m in left}))}: {' '.join(sorted(left))}\n")
    why = collections.Counter()
    for m, v in res.items():
        if v != "OK" and m not in left:
            msg = v.split("error: ", 1)[-1]
            if msg.startswith("timeout: "):
                msg = "timeout"
            if "is not supported: it is not a builtin module" in msg:
                msg = "imports the missing module " + msg.split("'")[1]
            why[msg[:100]] += 1
    for k, n in why.most_common(30):
        print(f"{n:5}  {k}")


main()
