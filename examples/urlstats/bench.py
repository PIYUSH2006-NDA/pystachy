"""bench: urlstats.py under CPython and as a Pystachy AOT executable, on generated logs of 200,000 and
1,000,000 requests, making the report and printing each request's canonical URL (--canon): the
median wall time of N runs, process start-up included, the median of the times the runs report for
reading the log (--time), and the peak RSS of one run; and whether the two print the same.

usage: python3 -I bench.py PYSTACHY [N]
The logs and the executable go to build/urlstats/ of the checkout.
"""
import hashlib
import os
import statistics
import subprocess
import sys
import time

pys = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "..", "build", "urlstats")
os.makedirs(out, exist_ok=True)
logs = []
for n in [200000, 1000000]:
    path = os.path.join(out, f"log_{n // 1000}k.txt" if n < 1000000 else f"log_{n // 1000000}m.txt")
    logs.append(path)
    if not os.path.exists(path):
        # (into a file of its own first: an interrupted run leaves no short log under this name)
        with open(path + ".part", "w") as f:
            subprocess.run([sys.executable, "-I", os.path.join(here, "genlog.py"), str(n)], stdout=f, check=True)
        os.replace(path + ".part", path)
exe = os.path.join(out, "urlstats_aot")
t = time.perf_counter()
subprocess.run([pys, "build", os.path.join(here, "urlstats.py"), "-o", exe], check=True)
print(f"pystachy build urlstats.py: {time.perf_counter() - t:.2f} s")
prog = os.path.join(here, "urlstats.py")


def peak_rss(cmd: list[str]) -> int:
    # the peak resident set of one run of cmd, in KB: a process of its own, whose only child it is
    probe = "import resource, subprocess, sys; subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, check=True); print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)"
    return int(subprocess.run([sys.executable, "-I", "-c", probe] + cmd, capture_output=True, text=True, check=True).stdout)


def measure(cmd: list[str], args: list[str]) -> tuple[float, float, int, str]:
    # the median wall time of the runs of cmd with args, the median of the reading times they
    # report, the peak RSS of one, and a digest of what a run prints
    times = []
    reads = []
    digest = ""
    for _ in range(runs):
        t = time.perf_counter()
        p = subprocess.run(cmd + ["--time"] + args, capture_output=True, check=True)
        times.append(time.perf_counter() - t)
        reads.append(float(p.stderr.decode().split("read ")[1].split(" s")[0]))  # "read 2.715 s, report 0.084 s"
        digest = hashlib.sha256(p.stdout).hexdigest()
    return statistics.median(times), statistics.median(reads), peak_rss(cmd + args), digest


print(f"{'log':5} {'mode':7} {'CPython':>9} {'AOT':>9} {'speedup':>8} {'read CPython':>13} {'read AOT':>9} {'CPython RSS':>12} {'AOT RSS':>9}")
for log in logs:
    for mode in ["", "--canon"]:
        args = ([mode] if mode else []) + [log]
        c = measure([sys.executable, "-I", prog], args)
        a = measure([exe], args)
        same = "" if c[3] == a[3] else "  OUTPUT DIFFERS"
        name = os.path.basename(log)[4:-4]
        print(f"{name:5} {mode or 'report':7} {c[0]:8.3f}s {a[0]:8.3f}s {c[0] / a[0]:7.2f}x {c[1]:12.3f}s {a[1]:8.3f}s {c[2] / 1024:9.1f} MB {a[2] / 1024:6.1f} MB{same}")
