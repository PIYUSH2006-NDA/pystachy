"""bench: latency.py under CPython and as a Pystachy AOT executable, on generated logs of 1,000,000
and 4,000,000 requests: the median wall time of N runs (process start-up included), the medians of
the times the runs report for reading the log and for the statistics (--time), and the peak RSS of
one run; and whether CPython and the executable print the same report.

usage: python3 -I bench.py PYSTACHY [N]
The logs and the executable go to build/latency/ of the checkout.
"""
import os
import statistics
import subprocess
import sys
import time

pys = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "..", "build", "latency")
os.makedirs(out, exist_ok=True)
logs = []
for n in [1000000, 4000000]:
    path = os.path.join(out, f"log_{n // 1000000}m.txt")
    logs.append(path)
    if not os.path.exists(path):
        # (into a file of its own first: an interrupted run leaves no short log under this name)
        with open(path + ".part", "w") as f:
            subprocess.run([sys.executable, "-I", os.path.join(here, "genlog.py"), str(n)], stdout=f, check=True)
        os.replace(path + ".part", path)
exe = os.path.join(out, "latency_aot")
t = time.perf_counter()
subprocess.run([pys, "build", os.path.join(here, "latency.py"), "-o", exe], check=True)
print(f"pystachy build latency.py: {time.perf_counter() - t:.2f} s")
program = os.path.join(here, "latency.py")


def peak_rss(cmd: list[str]) -> int:
    # the peak resident set of one run of cmd, in KB: a process of its own, whose only child it is
    probe = "import resource, subprocess, sys; subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, check=True); print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)"
    return int(subprocess.run([sys.executable, "-I", "-c", probe] + cmd, capture_output=True, text=True, check=True).stdout)


def run(cmd: list[str]) -> tuple[float, float, float, str]:
    # one run: its wall time, the times it reports for reading and for the statistics, its output
    t = time.perf_counter()
    p = subprocess.run(cmd + ["--time"], capture_output=True, text=True, check=True)
    wall = time.perf_counter() - t
    words = p.stderr.split()  # "read 0.402 s, statistics 0.022 s"
    return wall, float(words[1]), float(words[4]), p.stdout


print(f"{'log':4} {'CPython':>9} {'AOT':>9} {'speedup':>8} {'read CPython':>13} {'read AOT':>9}"
      f" {'stats CPython':>14} {'stats AOT':>10} {'CPython RSS':>12} {'AOT RSS':>9}")
for log in logs:
    cpython = [sys.executable, "-I", program, log]
    aot = [exe, log]
    run(cpython)  # one untimed run of each first, for the file cache
    run(aot)
    c: list[tuple[float, float, float, str]] = []
    a: list[tuple[float, float, float, str]] = []
    for _ in range(runs):  # in turn, so that a slow moment of the machine slows both
        c.append(run(cpython))
        a.append(run(aot))
    same = "" if c[0][3] == a[0][3] else "  OUTPUT DIFFERS"
    med = [statistics.median(r[i] for r in c) for i in range(3)] + [statistics.median(r[i] for r in a) for i in range(3)]
    name = os.path.basename(log)[4:-4]
    print(f"{name:4} {med[0]:8.3f}s {med[3]:8.3f}s {med[0] / med[3]:7.2f}x {med[1]:12.3f}s {med[4]:8.3f}s"
          f" {med[2]:13.3f}s {med[5]:9.3f}s {peak_rss(cpython) / 1024:9.1f} MB {peak_rss(aot) / 1024:6.1f} MB{same}")
