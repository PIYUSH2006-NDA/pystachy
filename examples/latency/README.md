# latency: the request latencies of each endpoint of an access log, with statistics

`latency.py` reads an access log, a request a line (its time, method, path, status, latency in
milliseconds and response size in bytes), and prints for each endpoint the count of its requests
and the statistics of their latencies: the mean (`statistics.fmean`), the mean weighted by the bytes
sent (`fmean` with `weights`: the latency a byte sees), the median (`median`), the low and high
medians (`median_low` and `median_high`, latencies that occurred), the median of the latencies
rounded to whole milliseconds (`median_grouped`, the estimate a histogram of 1 ms buckets gives),
the 90th and 99th percentiles (`quantiles(n=100)`) and the geometric mean (`geometric_mean`); then
the most common status (`mode`) and the share of server errors, and a last row for all requests. It
is ordinary Python, which CPython runs as it is and Pystachy compiles as it is, with
[`lib/statistics`](../../lib/README.md#statistics-a-port-of-cpythons): CPython's module, edited in
marked places, whose weighted `fmean()` adds the products as CPython's C `math.sumprod()` does.

```
$ python3 genlog.py 1000000 > access.log    # 55 MB
$ head -2 access.log
2026-10-13T08:00:00.010 GET /static/app.js 200 1.3 228490
2026-10-13T08:00:00.021 GET /static/app.js 200 1.2 240593
$ python3 latency.py access.log             # CPython
$ pystachy build latency.py -o latency && ./latency access.log
1000000 requests to 7 endpoints (0 lines skipped); latencies in ms
endpoint               requests     mean by bytes   median      low     high  grouped      p90      p99    gmean  status    5xx
GET /api/search          120509   114.37   114.59    85.50     85.5     85.5    85.56    203.3    528.1    86.09     200   0.4%
POST /api/login           49813   159.27   159.31   140.70    140.7    140.7   140.71    209.1    385.5   142.89     200   0.1%
GET /api/orders          199984    33.72    33.74    28.20     28.2     28.2    28.16     51.2    115.3    28.61     200   0.1%
POST /api/orders          60199    76.83    76.96    65.20     65.2     65.2    65.27    111.0    319.4    66.04     200   0.3%
GET /api/users           299588    13.94    13.94    12.10     12.1     12.1    12.06     19.2     62.8    12.28     200   0.1%
GET /static/app.js       239907     2.02     2.02     1.80      1.8      1.8     1.93      2.5      4.5     1.84     200   0.0%
GET /healthz              30000     0.66     0.67     0.60      0.6      0.6     0.75      0.8      1.1     0.61     200   0.0%
all                     1000000    37.75     7.94    14.80     14.8     14.8    14.82    103.9    255.5    13.32     200   0.1%
```

CPython and the executable print the same report. The endpoints come in the order of the time
their requests took in all, the one to look at first at the top. A mean above the median and a
99th percentile several times it tell of a long tail of slow requests; the mean by bytes of all
requests is low, as most bytes are those of `/static/app.js`, which is fast. A request logged with
`-` for its latency (a gateway timeout) counts for the statuses alone, and a line that is no
request is skipped and counted. `--time` writes how long reading the log and the statistics took
to stderr.

`genlog.py` writes the log: each endpoint gets its share of the requests and latencies of its own,
log-normal around its median, with 1 request in 100 ten times slower, response sizes of its own and
errors (fast 503s, and 504s without a latency), drawn from a linear congruential generator, so that
the log is the same on every run (and the executable `genlog.py` compiles to writes the same bytes).

## What compiling buys

`bench.py`, on a 4-core x86-64 VM shared with other jobs: the median wall time of 7 runs with
process start-up, the medians of the times the runs report for reading the log and for the
statistics (`--time`), and the peak RSS of one run, on logs of 1,000,000 requests (55 MB) and
4,000,000 (218 MB), CPython's runs and the executable's in turn:

| log | CPython 3.13.16 | Pystachy AOT | speedup | reading, CPython | reading, AOT | statistics, CPython | statistics, AOT | CPython RSS | AOT RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1M requests | 2.322 s | 1.489 s | 1.56× | 0.693 s | 0.472 s | 1.629 s | 0.977 s | 137.2 MB | 162.3 MB |
| 4M requests | 12.223 s | 8.519 s | 1.43× | 3.813 s | 3.348 s | 8.029 s | 5.126 s | 512.5 MB | 668.2 MB |

- **The statistics are 1.6 times as fast compiled**, and most of their time is sorting, in
  CPython too: `median()`, `median_low()`, `median_high()`, `median_grouped()` and `quantiles()`
  each sort the latencies they are given, as CPython's do, so that the report sorts each
  endpoint's latencies five times, and all of them five times more. Pystachy's sort (CPython's
  timsort) compares the floats of a list without boxes; on 100,000 floats, `median()` takes 8.3 ms
  (CPython: 13.1 ms). The rest is the means: a weighted `fmean()` takes 0.95 ms on 100,000 floats
  with int weights (CPython: 1.31 ms), whose products `_sumprod()` adds in triple length as C's
  `math.sumprod()` does, `geometric_mean()` 2.4 ms (6.4).
- **Reading the log is 1.5 times as fast for 1M requests, 1.1 times for 4M**: each line is split
  into six strs, with two `int()`s and a `float()`, which CPython does in C too; and Pystachy's
  collector, which frees the lines and their fields in batches, marks the live heap at each
  collection: with the 4M requests' 337 MiB of it, its collections take 1.0 s in all, 0.08 s for
  1M (`PYSTACHY_GC=stats`).
- **Memory is higher compiled**: the lines and their fields are garbage that Pystachy's collector
  frees when its heap has grown, where CPython's reference counts free each at once; the latencies
  themselves take less (a list of floats holds them unboxed, 8 bytes each, where CPython's points to
  24-byte floats). Building the executable takes about 1.6 s.

## Tests

`tests/example_latency.py` reads 3,000 requests that `genlog.lines()` makes, as the lines of a log,
and prints their report, then that of a log with lines that are no request, an endpoint with one
request, one with timeouts alone and one whose responses are empty, as CPython prints them
(`tests/example_latency.path` puts this directory on the module path). `bench.py` runs the table
above: `python3 -I bench.py ../../pystachy 7`, from anywhere; it writes its logs and the executable
to `build/latency/`.
