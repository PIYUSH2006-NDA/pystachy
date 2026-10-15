# pyperformance results

Pystachy compiles 19 of the 31 benchmarks tried from pyperformance 1.14.0, after the localized
adaptations listed in the [port notes](../bench/pyperformance/README.md). CPython runs the same
adapted files, and every JIT and AOT run must print exactly what CPython printed. These are
comparisons on that source, not pyperformance scores: some inputs, random number generators and
data types differ from upstream.

## Snapshot

Advisory snapshot of 2026-10-15: commit `da24d12`, with the native compiler built from main
`bdc20a2`, CPython 3.13.16 and LLVM 18.1.3 on a 4-core x86-64 VM (Intel Xeon at 2.10 GHz) shared
with other jobs. The load average was between 1 and 4, and each process used CPU for 85–99% of
its wall time. Each value is the median of five processes; the fastest and slowest of the five
differed by up to about 60% of the median, and more for `unpack_sequence`'s 3 ms AOT runs.
Ratios above 1 mean faster than CPython. The
[raw samples](benchmarks/pyperformance-2026-10-15-da24d12.json) include each process's wall, CPU
and timed seconds, the outputs and the source hashes.

Whole-process wall time:

| Benchmark | Arguments | CPython | JIT | AOT | CPython/AOT |
|---|---|---:|---:|---:|---:|
| `barnes_hut` | 1 | 0.86 s | 0.19 s | 0.039 s | 22.2× |
| `chaos` | 10 | 0.68 s | 0.25 s | 0.040 s | 16.9× |
| `deltablue` | 200 | 0.62 s | 0.50 s | 0.045 s | 13.9× |
| `fannkuch` | 2 | 0.86 s | 0.33 s | 0.246 s | 3.5× |
| `float` | 10 | 0.79 s | 0.17 s | 0.055 s | 14.4× |
| `go` | 4 | 0.65 s | 0.23 s | 0.045 s | 14.5× |
| `hexiom` | 100 | 0.62 s | 0.34 s | 0.081 s | 7.7× |
| `meteor_contest` | 6 | 0.69 s | 0.59 s | 0.469 s | 1.5× |
| `nbody` | 10 | 0.86 s | 0.19 s | 0.062 s | 13.8× |
| `nqueens` | 10 | 0.70 s | 0.35 s | 0.222 s | 3.1× |
| `raytrace` | 4 | 0.92 s | 0.26 s | 0.061 s | 15.0× |
| `regex_dna` | 4 | 0.89 s | 3.36 s | 2.094 s | 0.4× |
| `regex_effbot` | 20 | 0.49 s | 2.57 s | 1.243 s | 0.4× |
| `regex_v8` | 4 | 0.31 s | 2.99 s | 0.878 s | 0.4× |
| `richards` | 20 | 1.02 s | 0.28 s | 0.013 s | 81.0× |
| `richards_super` | 20 | 1.10 s | 0.28 s | 0.014 s | 79.2× |
| `scimark` | 2 | 0.84 s | 0.21 s | 0.039 s | 21.6× |
| `spectral_norm` | 10 | 0.95 s | 0.11 s | 0.019 s | 49.8× |
| `unpack_sequence` | 100000 | 0.77 s | 1.23 s | 0.003 s | n/a |

The timed part, which excludes startup and compilation, and the AOT build time:

| Benchmark | CPython | JIT | AOT | CPython/JIT | CPython/AOT | AOT build |
|---|---:|---:|---:|---:|---:|---:|
| `barnes_hut` | 0.842 s | 0.047 s | 0.0353 s | 17.9× | 23.9× | 0.7 s |
| `chaos` | 0.659 s | 0.060 s | 0.0350 s | 11.0× | 18.8× | 1.3 s |
| `deltablue` | 0.603 s | 0.044 s | 0.0406 s | 13.7× | 14.9× | 1.3 s |
| `fannkuch` | 0.845 s | 0.241 s | 0.2421 s | 3.5× | 3.5× | 0.5 s |
| `float` | 0.767 s | 0.078 s | 0.0512 s | 9.8× | 15.0× | 0.5 s |
| `go` | 0.625 s | 0.043 s | 0.0415 s | 14.6× | 15.1× | 1.0 s |
| `hexiom` | 0.599 s | 0.082 s | 0.0772 s | 7.3× | 7.8× | 1.5 s |
| `meteor_contest` | 0.669 s | 0.466 s | 0.4616 s | 1.4× | 1.4× | 1.3 s |
| `nbody` | 0.840 s | 0.093 s | 0.0600 s | 9.1× | 14.0× | 0.7 s |
| `nqueens` | 0.678 s | 0.255 s | 0.2178 s | 2.7× | 3.1× | 0.8 s |
| `raytrace` | 0.896 s | 0.058 s | 0.0568 s | 15.4× | 15.8× | 0.9 s |
| `regex_dna` | 0.778 s | 2.354 s | 2.0626 s | 0.3× | 0.4× | 4.4 s |
| `regex_effbot` | 0.463 s | 1.587 s | 1.2383 s | 0.3× | 0.4× | 3.8 s |
| `regex_v8` | 0.256 s | 1.119 s | 0.8600 s | 0.2× | 0.3× | 8.3 s |
| `richards` | 1.001 s | 0.017 s | 0.0108 s | 59.1× | 92.8× | 1.2 s |
| `richards_super` | 1.075 s | 0.017 s | 0.0119 s | 63.3× | 90.5× | 1.1 s |
| `scimark` | 0.814 s | 0.047 s | 0.0330 s | 17.3× | 24.7× | 1.0 s |
| `spectral_norm` | 0.935 s | 0.025 s | 0.0130 s | 37.6× | 72.1× | 0.6 s |
| `unpack_sequence` | 0.752 s | 0.745 s | 0.0003 s | 1.0× | n/a | 13.6 s |

## Reading the results

- AOT ran 15 of the 18 comparable benchmarks faster than CPython, by 1.5× to 81× in
  whole-process time. Object and numeric code gained most: `richards`, `richards_super` and
  `spectral_norm`.
- The three regex benchmarks were 2.4–2.8× slower AOT. `lib/re` is written in the supported
  subset, while CPython matches in its C `_sre` module. The JIT is slower still, because each run
  also compiles `lib/re`: about 1.9 of `regex_v8`'s 3.0 wall seconds.
- `fannkuch`, `nqueens` and `meteor_contest` gained 1.4–3.5× in the timed part. Their inner
  loops mostly slice and insert into lists, build tuples and sets, or combine frozensets, which
  are runtime calls; they were not profiled. The `fannkuch` and `nqueens` adaptations also replace
  slice assignment with new lists.
- JIT whole-process time includes compiling the program; besides the regex benchmarks, it
  exceeded CPython's time for `unpack_sequence`.
- `unpack_sequence` does not measure unpacking under AOT: its timed part took 0.3 ms, far too
  little for 40 million unpackings, because optimization removed the repeated unpacking of an
  unchanged list. Its AOT ratios are omitted. The JIT's timed part matched CPython's.
- The `random` substitutes in `chaos` and `go`, the `str` data of `regex_dna` and the other
  adaptations make the work differ from upstream pyperformance. Rerun on an idle machine before
  relying on a difference between two Pystachy revisions.

## Reproduce

```sh
make
make bench-pyperformance-check
make bench-pyperformance
python3 tools/bench_pyperformance.py --benchmarks regex_v8 richards --runs 9 --json build/pyperformance-two.json
```

The check runs small inputs once and compares outputs without keeping timings. A measured run
starts five processes per mode for each benchmark, rotates the order of the modes, and writes
the raw samples, outputs, commands and source hashes to `build/pyperformance.json`. Whole-process
time includes interpreter or executable startup; the JIT's includes compiling the program and its
library modules with a primed runtime cache. The timed part is what each benchmark's main reports:
the work that pyperf would time, without startup or compilation. AOT build time is measured once.

The [port notes](../bench/pyperformance/README.md#blocked) list the first compiler error of each
benchmark that remains blocked, and `--census` reproduces that table from the pinned sdist.
