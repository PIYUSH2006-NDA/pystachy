"""latency: a report of the request latencies of each endpoint of an access log, with statistics.

usage: python3 latency.py LOG [--time]
       pystachy build latency.py -o latency && ./latency LOG [--time]

Each line of LOG is a request: its time, method, path, status, latency in milliseconds and response
size in bytes, separated by spaces (genlog.py writes such logs):

    2026-10-13T08:00:00.123 GET /api/users 200 12.7 5321

A request whose latency is "-" (a timeout that the server logs without one) counts for its
endpoint's statuses, not for its latencies; a line that is no request is skipped and counted.
For each endpoint (method and path), in the order of the time its requests took in all, the report
gives the count of requests, and in milliseconds: the mean latency (statistics.fmean), the mean
weighted by the bytes sent (fmean with weights, the latency a byte sees), the median (median), the
low and high medians (median_low and median_high, latencies that occurred), the median of the
latencies rounded to whole milliseconds (median_grouped, as a histogram of 1 ms buckets estimates
it), the 90th and 99th percentiles (quantiles), the geometric mean (geometric_mean); then the most
common status (mode) and the share of server errors (5xx). The last row is all requests together.
--time writes how long reading the log and computing the statistics took to stderr.
"""
import sys
import time
from statistics import (fmean, geometric_mean, median, median_grouped, median_high, median_low, mode,
                        quantiles)


class Endpoint:
    # the requests of one endpoint so far
    def __init__(self, name: str) -> None:
        self.name = name
        self.latencies: list[float] = []  # in milliseconds
        self.sizes: list[int] = []  # the bytes of the same requests
        self.statuses: list[int] = []  # of all its requests
        self.timeouts = 0  # its requests without a latency


def parse(lines, endpoints: dict[str, Endpoint]) -> int:
    # adds the requests of lines (a file, or a list of str) to endpoints, by method and path, and
    # returns the count of lines that are no request
    skipped = 0
    for line in lines:
        fields = line.split()
        if len(fields) != 6:
            skipped += 1
            continue
        try:
            status = int(fields[3])
            size = int(fields[5])
            ms = -1.0 if fields[4] == "-" else float(fields[4])
        except ValueError:
            skipped += 1
            continue
        name = fields[1] + " " + fields[2]
        e = endpoints.get(name)
        if e is None:
            e = Endpoint(name)
            endpoints[name] = e
        e.statuses.append(status)
        if ms < 0.0:
            e.timeouts += 1
        else:
            e.latencies.append(ms)
            e.sizes.append(size)
    return skipped


def row(name: str, count: int, xs: list[float], sizes: list[int], statuses: list[int]) -> str:
    # one line of the report: the statistics of the latencies xs (and their sizes) of count requests
    errors = 100.0 * len([s for s in statuses if s >= 500]) / len(statuses)
    if len(xs) == 0:
        return f"{name:22} {count:8}" + " " * 81 + f"{mode(statuses):7} {errors:5.1f}%"
    percentiles = quantiles(xs, n=100)
    grouped = median_grouped([round(x) for x in xs], 1)
    by_bytes = fmean(xs, sizes) if sum(sizes) > 0 else fmean(xs)
    return (f"{name:22} {count:8} {fmean(xs):8.2f} {by_bytes:8.2f} {median(xs):8.2f} {median_low(xs):8.1f}"
            f" {median_high(xs):8.1f} {grouped:8.2f} {percentiles[89]:8.1f} {percentiles[98]:8.1f}"
            f" {geometric_mean(xs):8.2f} {mode(statuses):7} {errors:5.1f}%")


def report(endpoints: dict[str, Endpoint], skipped: int) -> None:
    total = 0
    for e in endpoints.values():
        total += len(e.statuses)
    print(f"{total} requests to {len(endpoints)} endpoints ({skipped} lines skipped); latencies in ms")
    print(f"{'endpoint':22} {'requests':>8} {'mean':>8} {'by bytes':>8} {'median':>8} {'low':>8} {'high':>8}"
          f" {'grouped':>8} {'p90':>8} {'p99':>8} {'gmean':>8} {'status':>7} {'5xx':>6}")
    # the endpoints whose requests took the most time in all first, then by name
    order = sorted(endpoints.values(), key=lambda e: (-sum(e.latencies), e.name))
    xs: list[float] = []
    sizes: list[int] = []
    statuses: list[int] = []
    for e in order:
        print(row(e.name, len(e.statuses), e.latencies, e.sizes, e.statuses))
        xs.extend(e.latencies)
        sizes.extend(e.sizes)
        statuses.extend(e.statuses)
    if len(endpoints) > 1:
        print(row("all", total, xs, sizes, statuses))


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print("usage: latency.py LOG [--time]", file=sys.stderr)
        sys.exit(2)
    t0 = time.perf_counter()
    endpoints: dict[str, Endpoint] = {}
    with open(args[0]) as f:
        skipped = parse(f, endpoints)
    t1 = time.perf_counter()
    report(endpoints, skipped)
    t2 = time.perf_counter()
    if "--time" in sys.argv:
        print(f"read {t1 - t0:.3f} s, statistics {t2 - t1:.3f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
