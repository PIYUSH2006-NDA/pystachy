"""bench: topk.py under CPython and as a Pystachy AOT executable, picking with heapq (the default)
and by sorting (--sort), on generated texts of 1,000,000 and 4,000,000 words: the median wall time
of N runs, the medians of the times the runs report for picking (--time), and the peak RSS of one.

usage: python3 -I bench.py PYSTACHY [N]
The texts and the executable go to build/topk/ of the checkout.
"""
import os
import statistics
import subprocess
import sys
import time

pys = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "..", "build", "topk")
os.makedirs(out, exist_ok=True)
texts = []
for n in [1000000, 4000000]:
    path = os.path.join(out, f"text_{n // 1000000}m.txt")
    texts.append(path)
    if not os.path.exists(path):
        # (into a file of its own first: an interrupted run leaves no short text under this name)
        with open(path + ".part", "w") as f:
            subprocess.run([sys.executable, "-I", os.path.join(here, "gentext.py"), str(n)], stdout=f, check=True)
        os.replace(path + ".part", path)
exe = os.path.join(out, "topk_aot")
t = time.perf_counter()
subprocess.run([pys, "build", os.path.join(here, "topk.py"), "-o", exe], check=True)
print(f"pystachy build topk.py: {time.perf_counter() - t:.2f} s")
topk = os.path.join(here, "topk.py")


def peak_rss(cmd: list[str]) -> int:
    # the peak resident set of one run of cmd, in KB: a process of its own, whose only child it is
    probe = "import resource, subprocess, sys; subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, check=True); print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)"
    return int(subprocess.run([sys.executable, "-I", "-c", probe] + cmd, capture_output=True, text=True, check=True).stdout)


def measure(cmd: list[str]) -> tuple[float, float, int, str]:
    # the median wall time of the runs, the median of the picking times they report, the peak RSS
    # of one, and what a run prints
    times = []
    picks = []
    out = ""
    for _ in range(runs):
        t = time.perf_counter()
        p = subprocess.run(cmd + ["--time"], capture_output=True, text=True, check=True)
        times.append(time.perf_counter() - t)
        picks.append(float(p.stderr.split("pick ")[1].split(" s")[0]))  # "count 0.402 s, pick 0.022 s"
        out = p.stdout
    return statistics.median(times), statistics.median(picks), peak_rss(cmd), out


print(f"{'text':5} {'mode':6} {'CPython':>9} {'AOT':>9} {'speedup':>8} {'pick CPython':>13} {'pick AOT':>9} {'CPython RSS':>12} {'AOT RSS':>9}")
for text in texts:
    for mode in ["", "--sort"]:
        extra = [mode] if mode else []
        c = measure([sys.executable, "-I", topk, text] + extra)
        a = measure([exe, text] + extra)
        same = "" if c[3] == a[3] else "  OUTPUT DIFFERS"
        name = os.path.basename(text)[5:-4]
        print(f"{name:5} {mode or 'heap':6} {c[0]:8.3f}s {a[0]:8.3f}s {c[0] / a[0]:7.2f}x {c[1]:12.3f}s {a[1]:8.3f}s {c[2] / 1024:9.1f} MB {a[2] / 1024:6.1f} MB{same}")
