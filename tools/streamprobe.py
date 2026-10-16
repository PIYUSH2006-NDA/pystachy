"""sum(), min() and max() of range() and of generator expressions take the items as they come (#88),
and so do a for loop over a generator and sum() of one (#490).

usage: python3 tools/streamprobe.py [NATIVE_COMPILER]
Builds a program that reduces N = 100,000,000 items in each way (an int sum, a float sum, a sum
with a start, max(), min(), a for loop over a generator, sum() of a generator), runs the executable
under a 64 MiB address-space limit, where the list of the items alone would take 800 MB, and checks
what it prints against the values computed in closed form. Its peak memory does not grow with N
(no RSS or timing threshold).
"""
from pathlib import Path
import resource
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
N = 100_000_000
PROGRAM = """import sys
from collections.abc import Iterator


def count(n: int) -> Iterator[int]:
    i = 0
    while i < n:
        yield i
        i += 1


n = int(sys.argv[1])
print(sum(range(n)))
print(sum(x * 0.5 for x in range(n)))
print(sum((x % 7 for x in range(n)), 10))
print(max(x % 1000003 for x in range(n)), min(-x for x in range(n)))
threes = 0
for x in count(n):
    threes += x % 3
print(threes, sum(count(n)))
"""


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (64 * 1024 * 1024, 64 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def main():
    native = (Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "pystachy").resolve()
    sevens = sum(range(7)) * (N // 7) + sum(range(N % 7)) + 10
    threes = 3 * (N // 3) + (1 if N % 3 == 2 else 0)
    want = f"{N * (N - 1) // 2}\n{float(N * (N - 1) // 4)}\n{sevens}\n1000002 {-(N - 1)}\n{threes} {N * (N - 1) // 2}\n"
    with tempfile.TemporaryDirectory(prefix="pystachy-stream-") as tmp:
        src = Path(tmp) / "reduce.py"
        exe = Path(tmp) / "reduce"
        src.write_text(PROGRAM)
        subprocess.run([str(native), "build", str(src), "-o", str(exe)], check=True)
        r = subprocess.run([str(exe), str(N)], capture_output=True, text=True, preexec_fn=limits, timeout=120)
        if r.returncode != 0 or r.stdout != want:
            print(f"streamprobe: {N} items under 64 MiB: exit {r.returncode}", file=sys.stderr)
            print(r.stdout + r.stderr, file=sys.stderr)
            print("wanted:\n" + want, file=sys.stderr)
            return 1
    print(f"streamprobe: sum(), min(), max() and generators of {N} items ran under 64 MiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
