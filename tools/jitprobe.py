"""Check dead-code removal at the JIT boundary, without timing thresholds.

usage: python3 tools/jitprobe.py [-c LABEL=COMMAND]...
A transparent lli wrapper inspects the bitcode the driver actually executes.
"""
import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SOURCE = '''import jitprobe_module

def note() -> int:
    print("default")
    return 7

def unused_default(x: int = note()) -> int:
    return x

def unused_left(x: int) -> int:
    return unused_right(x - 1) if x else 0

def unused_right(x: int) -> int:
    return unused_left(x - 1) if x else 0

def live_leaf(x: int) -> int:
    return x + 1

def live_root(x: int) -> int:
    return live_leaf(x) * 2

class Item:
    def __init__(self, x: int):
        self.x = x
    def __eq__(self, other: "Item") -> bool:
        return self.x == other.x
    def __lt__(self, other: "Item") -> bool:
        return self.x < other.x
    def __repr__(self) -> str:
        return f"Item({self.x})"

print(live_root(20))
print([Item(1)] == [Item(1)], [Item(1)] < [Item(2)])
print(sorted([Item(2), Item(1)]))
'''


def run(command, env):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=60, check=False)
    if result.returncode or result.stderr:
        raise RuntimeError(f"{shlex.join(command)}: exit {result.returncode}\n{result.stderr.decode()}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-c", action="append", default=[], metavar="LABEL=COMMAND")
    args = parser.parse_args()
    commands = args.c or [f"hosted={shlex.quote(sys.executable)} -m pystachy", f"native={ROOT / 'pystachy'}"]
    llvm = os.environ.get("PYSTACHY_LLVM", "")
    with tempfile.TemporaryDirectory(prefix="pystachy-jitprobe-") as tmp:
        temp = Path(tmp)
        source = temp / "probe.py"
        source.write_text(SOURCE + "\n".join(f"def unused_{i}(x: int) -> int:\n    return x + {i}\n" for i in range(32)))
        (temp / "jitprobe_module.py").write_text('print("import")\n')
        capture = temp / "executed.ll"
        bindir = temp / "bin"
        bindir.mkdir()
        real = {}
        for name in ("clang", "opt", "lli", "llvm-link", "llvm-as"):
            path = shutil.which(str(Path(llvm) / name) if llvm else name)
            if path is None:
                raise RuntimeError(f"cannot find {name}; set PYSTACHY_LLVM")
            real[name] = str(Path(path).absolute())
            if name != "lli":
                (bindir / name).symlink_to(real[name])
        wrapper = bindir / "lli"
        wrapper.write_text(f"#!/bin/sh\n{shlex.quote(real['opt'])} -S -passes=verify /dev/fd/9 -o {shlex.quote(str(capture))} || exit $?\nexec {shlex.quote(real['lli'])} \"$@\"\n")
        wrapper.chmod(0o755)
        env = os.environ | {"PYSTACHY_LLVM": str(bindir), "PYSTACHY_PATH": str(temp)}
        expected = run([sys.executable, str(source)], env)
        for spec in commands:
            label, command = spec.split("=", 1)
            cmd = shlex.split(command)
            raw = run(cmd + ["ir", str(source)], env).decode()
            dead = set(re.findall(r"^define internal .*?@([^ (]*unused_[^ (]*)\(", raw, re.MULTILINE))
            if len(dead) != 35:
                raise RuntimeError(f"{label}: expected 35 emitted unused functions, got {len(dead)}")
            capture.unlink(missing_ok=True)
            if run(cmd + ["run", str(source)], env) != expected:
                raise RuntimeError(f"{label}: JIT output differs from CPython")
            executed = capture.read_text()
            remaining = {name for name in dead if f"@{name}(" in executed}
            if remaining:
                raise RuntimeError(f"{label}: {len(remaining)} unused functions reached lli: {sorted(remaining)[:3]}")
            for name in ("pys_obj_eq", "pys_obj_cmp", "pys_obj_repr"):
                if not re.search(rf"^define .*?@{name}\(", executed, re.MULTILINE):
                    raise RuntimeError(f"{label}: runtime callback {name} is missing")
            print(f"{label}: 35 unused functions removed; live calls, defaults, imports and runtime callbacks preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
