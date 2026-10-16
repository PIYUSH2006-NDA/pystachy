"""bench: montecarlo.py under CPython and as a Pystachy AOT executable, with 1 and 10 million
samples; the median wall and CPU (user + system) times of N runs, and whether both print the same
estimates. On a shared host, the CPU time varies less than the wall time.

usage: python3 -I bench.py PYSTACHY [N]
The executable goes to build/montecarlo/ of the checkout.
"""
import os
import resource
import statistics
import subprocess
import sys
import time

pys = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "..", "build", "montecarlo")
os.makedirs(out, exist_ok=True)
prog = os.path.join(here, "montecarlo.py")
exe = os.path.join(out, "montecarlo_aot")
t = time.perf_counter()
subprocess.run([pys, "build", prog, "-o", exe], check=True)
print(f"pystachy build montecarlo.py: {time.perf_counter() - t:.2f} s")


def cpu() -> float:
    # the user and system time of the finished child processes so far
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def measure(cmd: list[str]) -> tuple[float, float, str]:
    # the median wall and CPU times of the runs, and what a run prints
    walls = []
    cpus = []
    printed = ""
    for _ in range(runs):
        t = time.perf_counter()
        c = cpu()
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
        walls.append(time.perf_counter() - t)
        cpus.append(cpu() - c)
        printed = p.stdout
    return statistics.median(walls), statistics.median(cpus), printed


print(f"{'samples':>10} {'CPython':>9} {'AOT':>9} {'speedup':>8} {'CPython CPU':>12} {'AOT CPU':>9} {'speedup':>8}")
for n in [1000000, 10000000]:
    c = measure([sys.executable, "-I", prog, "42", str(n)])
    a = measure([exe, "42", str(n)])
    same = "" if c[2] == a[2] else "  OUTPUT DIFFERS"
    print(f"{n:>10} {c[0]:8.3f}s {a[0]:8.3f}s {c[0] / a[0]:7.1f}x {c[1]:11.3f}s {a[1]:8.3f}s {c[1] / a[1]:7.1f}x{same}")
