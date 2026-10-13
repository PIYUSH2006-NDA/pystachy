"""bench: suggest.py under CPython and as a Pystachy AOT executable, for a generated vocabulary of
20,000 words and texts of 25 and 100 lines; the median wall time of N runs and the peak RSS of one.

usage: python3 -I bench.py PYSTACHY [N]
The vocabulary, the texts and the executable go to build/suggest/ of the checkout.
"""
import os
import statistics
import subprocess
import sys
import time

pys = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "..", "build", "suggest")
os.makedirs(out, exist_ok=True)


def generate(name: str, args: list[str]) -> str:
    path = os.path.join(out, name)
    if not os.path.exists(path):
        # (into a file of its own first: an interrupted run leaves no short file under this name)
        with open(path + ".part", "w") as f:
            subprocess.run([sys.executable, "-I", os.path.join(here, "genvocab.py")] + args, stdout=f, check=True)
        os.replace(path + ".part", path)
    return path


vocab = generate("vocab.txt", ["vocab", "20000"])
texts = [generate("text25.txt", ["text", "20000", "25"]), generate("text100.txt", ["text", "20000", "100"])]
exe = os.path.join(out, "suggest_aot")
t = time.perf_counter()
subprocess.run([pys, "build", os.path.join(here, "suggest.py"), "-o", exe], check=True)
print(f"pystachy build suggest.py: {time.perf_counter() - t:.2f} s")
prog = os.path.join(here, "suggest.py")


def peak_rss(cmd: list[str]) -> int:
    # the peak resident set of one run of cmd, in KB: a process of its own, whose only child it is
    probe = "import resource, subprocess, sys; subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL); print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)"
    return int(subprocess.run([sys.executable, "-I", "-c", probe] + cmd, capture_output=True, text=True, check=True).stdout)


def measure(cmd: list[str]) -> tuple[float, int, str]:
    # the median wall time of the runs, the peak RSS of one, and what a run prints (suggest exits
    # with 1 when it found unknown words)
    times = []
    printed = ""
    for _ in range(runs):
        t = time.perf_counter()
        p = subprocess.run(cmd, capture_output=True, text=True)
        times.append(time.perf_counter() - t)
        printed = p.stdout
    return statistics.median(times), peak_rss(cmd), printed


print(f"{'text':10} {'unknown':>8} {'CPython':>9} {'AOT':>9} {'speedup':>8} {'CPython RSS':>12} {'AOT RSS':>9}")
for text in texts:
    c = measure([sys.executable, "-I", prog, vocab, text])
    a = measure([exe, vocab, text])
    same = "" if c[2] == a[2] else "  OUTPUT DIFFERS"
    unknown = c[2].splitlines()[-1].split()[0]
    print(f"{os.path.basename(text):10} {unknown:>8} {c[0]:8.3f}s {a[0]:8.3f}s {c[0] / a[0]:7.1f}x {c[1] / 1024:9.1f} MB {a[1] / 1024:6.1f} MB{same}")
