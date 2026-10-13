"""bench: mailmerge.py under CPython and as a Pystachy AOT executable, in each mode, on 100,000
generated records: the median wall time of N runs, the peak RSS of one, and whether the mailboxes
are the same.

usage: python3 -I bench.py PYSTACHY [N]
The data and the executable go to build/mailmerge/ of the checkout.
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
out = os.path.join(here, "..", "..", "build", "mailmerge")
os.makedirs(out, exist_ok=True)
data = os.path.join(out, "data_100k.tsv")
if not os.path.exists(data):
    # (into a file of its own first: an interrupted run leaves no short file under this name)
    with open(data + ".part", "w") as f:
        subprocess.run([sys.executable, "-I", os.path.join(here, "gendata.py"), "100000"], stdout=f, check=True)
    os.replace(data + ".part", data)
exe = os.path.join(out, "mailmerge_aot")
t = time.perf_counter()
subprocess.run([pys, "build", os.path.join(here, "mailmerge.py"), "-o", exe], check=True)
print(f"pystachy build mailmerge.py: {time.perf_counter() - t:.2f} s")
template = os.path.join(here, "notice.txt")
mailmerge = os.path.join(here, "mailmerge.py")


def peak_rss(cmd: list[str]) -> int:
    # the peak resident set of one run of cmd, in KB: a process of its own, whose only child it is
    probe = "import resource, subprocess, sys; subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True); print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)"
    return int(subprocess.run([sys.executable, "-I", "-c", probe] + cmd, capture_output=True, text=True, check=True).stdout)


def measure(cmd: list[str]) -> tuple[float, int, str]:
    # the median wall time of the runs, the peak RSS of one, and the SHA-256 of what a run prints
    times = []
    digest = ""
    for _ in range(runs):
        t = time.perf_counter()
        p = subprocess.run(cmd, capture_output=True, check=True)
        times.append(time.perf_counter() - t)
        digest = hashlib.sha256(p.stdout).hexdigest()
    return statistics.median(times), peak_rss(cmd), digest


print(f"{'mode':12} {'CPython':>9} {'AOT':>9} {'speedup':>8} {'CPython RSS':>12} {'AOT RSS':>9}")
for mode in ["", "--safe", "--split"]:
    extra = [mode] if mode else []
    c = measure([sys.executable, "-I", mailmerge, template, data] + extra)
    a = measure([exe, template, data] + extra)
    same = "" if c[2] == a[2] else "  OUTPUT DIFFERS"
    print(f"{mode or 'substitute':12} {c[0]:8.3f}s {a[0]:8.3f}s {c[0] / a[0]:7.2f}x {c[1] / 1024:9.1f} MB {a[1] / 1024:6.1f} MB{same}")
