# urlstats: what the requests of an access log asked for, with urllib.parse

`urlstats.py` reads a web server's access log, in Common or Combined Log Format, and reports what
its requests asked for: the most requested paths, each query parameter with the number of requests
that give it, its number of distinct values and its most common ones, the values whose escapes are
no UTF-8, and the most requested canonical URLs. It splits each request's target with
`urlsplit()`, decodes the path with `unquote()` and the query with `parse_qsl()`, and makes the
canonical URL with `quote()` and `urlencode()`: each segment of the path decoded and quoted again
(an escaped `/` stays one), and the query's pairs sorted and encoded again, so that
`/caf%c3%a9?b=2&a=1` and `/caf%C3%A9?a=1&b=2` are one URL, as a cache would key them. It is
ordinary Python, which CPython runs as it is and Pystachy compiles as it is, with
[`lib/urllib/parse.py`](../../lib/README.md#urllibparse-a-port-of-cpythons), CPython's `urllib.parse`
with marked edits.

```
$ python3 genlog.py 1000000 > access.log    # 131 MB: 207.93.69.226 - - [13/Oct/2026:00:00:00 +0000] "GET /api/v1/...
$ python3 urlstats.py access.log             # CPython
$ pystachy build urlstats.py -o urlstats && ./urlstats access.log
1000000 requests (0 lines without one); 2026 distinct paths, 87081 distinct canonical URLs
most requested paths:
    320335 /search
     80392 /
     80184 /api/v1/items
     40266 /login
     30139 /category/sport
     ...
query parameters: requests that give them, distinct values, the most common values:
  q            320335     35  'lamp' (13005), 'tent' (12987), 'red dress' (12953)
  filter       179928      9  'color:black' (36220), 'color:red' (36028), 'color:blue' (36018)
  page         166917      9  '6' (28338), '4' (28096), '2' (28074)
  ref          152736      3  'home' (73496), 'search' (72895), '%zz' (6345)
  ...
  ids           80184  62144  '908' (23), '1158' (21), '436' (21)
  ...
values whose escapes are no UTF-8 (decoded with U+FFFD): 2106
most requested canonical URLs:
     80392 /
     20250 /login?next=%2Faccount%2Forders%3Ftab%3Dall
     20016 /login?next=%2Faccount%2Forders%3Ftab%3Dopen
      6402 /search?q=tent
      ...
```

CPython and the executable print the same report. `--canon` prints each request's canonical URL
instead (`./urlstats --canon access.log | sort | uniq -c` counts them as the report does), `--top
N` lists N paths and URLs, and `--time` writes how long the reading and the report took to stderr.

`genlog.py` writes a log of a shop's requests: the front page, searches (`q`, `page`, `sort`),
products (with `ref` and `utm_*` tracking), categories (`filter`, given twice, and `page`), an API,
a login page with a `next` URL and static files. Search terms mix ASCII and other scripts, and
characters that must be escaped; clients encode them as they do, with `quote_plus()` or `quote()`,
upper or lower case hex digits, the parameters in any order, a few in Latin-1 (whose escapes are
no UTF-8, decoded with U+FFFD) or with a broken escape (`%zz`), which `unquote()` leaves as it is.
Its choices come from a linear congruential generator, so the log is the same on every run, and
the same compiled as under CPython.

## Speed

`bench.py`, on a 4-core x86-64 VM shared with other jobs: the median wall time of 7 runs with
process start-up, the median of the times the runs report for reading the log (`--time`), and the
peak RSS of one run, on a log of 200,000 requests (26 MB) and one of 1,000,000 (131 MB; 87,081
distinct canonical URLs):

| log | mode | CPython 3.13.16 | Pystachy AOT | reading, CPython | reading, AOT | CPython RSS | AOT RSS |
|---|---|---:|---:|---:|---:|---:|---:|
| 200k | report | 2.389 s | 0.433 s | 2.312 s | 0.405 s | 21.5 MB | 43.1 MB |
| 200k | `--canon` | 2.514 s | 0.462 s | 2.468 s | 0.456 s | 16.9 MB | 40.8 MB |
| 1M | report | 12.926 s | 2.196 s | 12.732 s | 2.095 s | 40.8 MB | 58.2 MB |
| 1M | `--canon` | 13.369 s | 2.482 s | 13.230 s | 2.396 s | 28.4 MB | 50.5 MB |

- **The executable is 5.4 to 5.9 times as fast**: about 2 µs a request, where CPython takes 13,
  for a `urlsplit()`, an `unquote()`, a `parse_qsl()` of two or three fields, a `sorted()`, an
  `urlencode()` of the pairs with `quote()` and a few dict updates. Most of the executable's time
  is the runtime's: reading the lines, allocating, the str methods that `urlsplit()` and
  `parse_qsl()` call (`lstrip()`, `replace()`, `split()`, `find()`) and the dicts; the port's own
  code, the quoting tables and the UTF-8 decoder, is a small part of it (callgrind). Start-up is
  about a millisecond, where CPython takes some 20 to start and import `urllib.parse`.
- CPython's `urlsplit()` keeps its last 128 results (`functools.lru_cache`), and the log repeats some
  targets (the front page, the login page); the port caches nothing, and is faster anyway.
- **Memory is higher**: Pystachy's collector lets the heap grow by at least 32 MB between
  collections, where CPython frees each string as its last reference goes; the difference shrinks
  as the data the report keeps grows. Building the executable takes about 4 s.

## Tests

`tests/example_urlstats.py` counts 400 generated requests and a few lines without one in-process,
prints the report and the canonical URLs of some targets (parameters in another order, lower case
hex digits, Latin-1, `+` and `%2B`, blank values, an absolute URL, a broken escape), and compares
them with CPython's (`tests/example_urlstats.path` puts this directory on the module path).
`bench.py` runs the table above: `python3 -I bench.py ../../pystachy 7`, from anywhere; it writes
its logs and executable to `build/urlstats/`.
