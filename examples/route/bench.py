"""bench: route.py under CPython and as a Pystachy AOT executable, in each mode, on a trace whose
names repeat (1,000,000 events, about 2,500 names) and on one whose names are all new (100,000).
For each, the median wall time of N runs of the whole program, the median time of the routing
alone (--in-memory: the trace read first, and the routing timed in the program), and the peak RSS
of one run.

usage: python3 -I bench.py PYSTACHY [N]
The traces and the executable go to build/route/ of the checkout.
"""
import os
import statistics
import subprocess
import sys
import time

pys = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "..", "build", "route")
os.makedirs(out, exist_ok=True)
traces = []
for n, mode in [(1000000, "repeat"), (100000, "unique")]:
    path = os.path.join(out, f"ev_{mode}.tsv")
    traces.append(path)
    if not os.path.exists(path):
        # (into a file of its own first: an interrupted run leaves no short trace under this name)
        with open(path + ".part", "w") as f:
            subprocess.run([sys.executable, "-I", os.path.join(here, "genevents.py"), str(n), mode], stdout=f, check=True)
        os.replace(path + ".part", path)
exe = os.path.join(out, "route_aot")
t = time.perf_counter()
subprocess.run([pys, "build", os.path.join(here, "route.py"), "-o", exe], check=True)
print(f"pystachy build route.py: {time.perf_counter() - t:.2f} s")
rules = os.path.join(here, "rules.txt")
route = os.path.join(here, "route.py")


def peak_rss(cmd: list[str]) -> int:
    # the peak resident set of one run of cmd, in KB: a process of its own, whose only child it is
    probe = "import resource, subprocess, sys; subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, check=True); print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)"
    return int(subprocess.run([sys.executable, "-I", "-c", probe] + cmd, capture_output=True, text=True, check=True).stdout)


def measure(cmd: list[str]) -> tuple[float, float, str]:
    # the median wall time of the runs of cmd, the median routing time that cmd + --in-memory
    # reports on stderr ("routing: SECONDS s, ..."), and what a run prints
    times = []
    routing = []
    out = ""
    for _ in range(runs):
        t = time.perf_counter()
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
        times.append(time.perf_counter() - t)
        out = p.stdout
        p = subprocess.run(cmd + ["--in-memory"], capture_output=True, text=True, check=True)
        routing.append(float(p.stderr.split()[1]))
        if p.stdout != out:
            out += "  (--in-memory prints otherwise)"
    return statistics.median(times), statistics.median(routing), out


print(f"{'trace':7} {'mode':11} {'CPython':>8} {'AOT':>8} {'speedup':>7} {'routing: CPython':>17} {'AOT':>9} {'speedup':>7} {'RSS: CPython':>13} {'AOT':>8}")
for trace in traces:
    events = 1000000 if "repeat" in trace else 100000
    for mode in ["", "--no-cache", "--fnmatch"]:
        extra = [mode] if mode else []
        c = measure([sys.executable, "-I", route, rules, trace] + extra)
        a = measure([exe, rules, trace] + extra)
        rc = peak_rss([sys.executable, "-I", route, rules, trace] + extra)
        ra = peak_rss([exe, rules, trace] + extra)
        same = "" if c[2] == a[2] else "  OUTPUT DIFFERS"
        name = os.path.basename(trace)[3:-4]
        print(f"{name:7} {mode or 'cached':11} {c[0]:7.3f}s {a[0]:7.3f}s {c[0] / a[0]:6.1f}x {c[1] * 1e9 / events:14.0f} ns {a[1] * 1e9 / events:6.0f} ns {c[1] / a[1]:6.1f}x {rc / 1024:10.1f} MB {ra / 1024:5.1f} MB{same}")
# what --names costs: a dict of every distinct name, which the trace of new names makes grow
for trace in traces:
    name = os.path.basename(trace)[3:-4]
    rc = peak_rss([sys.executable, "-I", route, rules, trace, "--names"])
    ra = peak_rss([exe, rules, trace, "--names"])
    print(f"{name:7} cached, --names: RSS CPython {rc / 1024:.1f} MB, AOT {ra / 1024:.1f} MB")
