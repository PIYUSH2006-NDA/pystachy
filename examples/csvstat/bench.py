"""bench: csvstat.py under CPython and as a Pystachy AOT executable, on a generated file of 200,000
orders (the median wall time of N runs, with process start-up, and the peak RSS of one); and
rwbench.py, csv.reader's and csv.writer's own time per row on that file (the medians of N runs).
CPython's and the executable's runs are taken in turn, after an untimed one of each.

usage: python3 -I bench.py PYSTACHY [N]
The file and the executables go to build/csvstat/ of the checkout.
"""
import os
import statistics
import subprocess
import sys
import time

pys = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
rows = 200000
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "..", "build", "csvstat")
os.makedirs(out, exist_ok=True)
data = os.path.join(out, f"orders_{rows}.csv")
if not os.path.exists(data):
    # (into a file of its own first: an interrupted run leaves no short file under this name)
    with open(data + ".part", "w") as f:
        subprocess.run([sys.executable, "-I", os.path.join(here, "gencsv.py"), str(rows)], stdout=f, check=True)
    os.replace(data + ".part", data)
print(f"{data}: {rows} rows, {os.path.getsize(data) / 1e6:.1f} MB")
exes = {}
for prog in ["csvstat", "rwbench"]:
    exes[prog] = os.path.join(out, prog + "_aot")
    t = time.perf_counter()
    subprocess.run([pys, "build", os.path.join(here, prog + ".py"), "-o", exes[prog]], check=True)
    print(f"pystachy build {prog}.py: {time.perf_counter() - t:.2f} s")


def peak_rss(cmd: list[str]) -> int:
    # the peak resident set of one run of cmd, in KB: a process of its own, whose only child it is
    probe = "import resource, subprocess, sys; subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, check=True); print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)"
    return int(subprocess.run([sys.executable, "-I", "-c", probe] + cmd, capture_output=True, text=True, check=True).stdout)


def measure(cmds: list[list[str]]) -> list[tuple[float, int, str]]:
    # for each command, the median wall time of the runs (the commands' runs alternate, so that a
    # change in the machine's load reaches each), the peak RSS of one, and what a run prints
    times: list[list[float]] = [[] for _ in cmds]
    printed = ["" for _ in cmds]
    for cmd in cmds:
        subprocess.run(cmd, capture_output=True, check=True)  # (untimed: the builds' load lingers)
    for _ in range(runs):
        for k in range(len(cmds)):
            t = time.perf_counter()
            p = subprocess.run(cmds[k], capture_output=True, text=True, check=True)
            times[k].append(time.perf_counter() - t)
            printed[k] = p.stdout
    return [(statistics.median(times[k]), peak_rss(cmds[k]), printed[k]) for k in range(len(cmds))]


def per_row(cmds: list[list[str]]) -> list[list[float]]:
    # for each command (a run of rwbench), the median read, parse and write times per row (us) of
    # the runs, in turn with the others'
    times: list[list[list[float]]] = [[[], [], []] for _ in cmds]
    for _ in range(runs):
        for k in range(len(cmds)):
            words = subprocess.run(cmds[k], capture_output=True, text=True, check=True).stdout.splitlines()[1].split()
            for j in range(3):
                times[k][j].append(float(words[1 + 3 * j]))
    return [[statistics.median(ts) for ts in times[k]] for k in range(len(cmds))]


csvstat = os.path.join(here, "csvstat.py")
print(f"{'csvstat':10} {'CPython':>9} {'AOT':>9} {'speedup':>8} {'CPython RSS':>12} {'AOT RSS':>9}")
for extra in [[], ["--csv"]]:
    c, a = measure([[sys.executable, "-I", csvstat, data] + extra, [exes["csvstat"], data] + extra])
    same = "" if c[2] == a[2] else "  OUTPUT DIFFERS"
    print(f"{' '.join(extra) or 'report':10} {c[0]:8.3f}s {a[0]:8.3f}s {c[0] / a[0]:7.1f}x {c[1] / 1024:9.1f} MB {a[1] / 1024:6.1f} MB{same}")
copy = os.path.join(out, "copy.csv")
c, a = per_row([[sys.executable, "-I", os.path.join(here, "rwbench.py"), data, copy], [exes["rwbench"], data, copy]])
print(f"{'per row':10} {'CPython':>9} {'AOT':>9} {'speedup':>8}")
for k, what in enumerate(["read", "parse", "write"]):
    print(f"{what:10} {c[k]:7.3f}us {a[k]:7.3f}us {c[k] / a[k]:7.1f}x")
