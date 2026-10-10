# Extended subset performance prototype

`tools/bench_extended.py` adds seven small, original workloads to the numeric and dict
benchmarks in [`bench/run.sh`](../bench/run.sh). It needs no runtime/compiler changes and no
third-party Python packages. The controller runs on CPython; the generated drivers and
[`kernels.py`](../bench/extended/kernels.py) use Pystachy's supported subset.

The purpose is to find expensive paths worth profiling, redesigning or simplifying. These
are diagnostic kernels, not a pyperformance port, a representative application score, or
numbers comparable to published upstream results. Existing n-body, spectral norm, Mandelbrot,
Fibonacci, sieve and word-count programs already cover the obvious numeric starting points.

| Case | Work exercised | Default N |
|---|---|---:|
| `object_dispatch` | Field reads/writes and method calls on 64 persistent objects | 20,000 |
| `text_pipeline` | Split/strip/lower, integer conversion, temporary containers and dict aggregation | 10,000 |
| `list_churn` | Append growth, slices, extend, pop, sum, clear and allocation/GC | 10,000 |
| `exception_local` | A raise every eight iterations, handled in the same function | 2,000,000 |
| `exception_unwind` | Same raise rate and result, with a function boundary | 2,000,000 |
| `long_string_keys` | Repeated lookups using the same 64 roughly 1 KiB string objects | 5,000 |
| `sort_records` | Object allocation, `__lt__` callbacks and stable sorting of duplicate keys | 2,000 |

N counts batches within a case; it is not a common unit across cases. Each call includes
its setup and returns a deterministic integer checksum. Live input sizes stay bounded while
N grows. This tests sustained work and allocation churn, not growing-data asymptotics.
Checksums catch many mistakes but do not replace the differential correctness suite.

## Run

Use the existing LLVM 18 setup (`PYSTACHY_LLVM` if needed), then:

```sh
make
make bench-extended-check
python3 tools/bench_extended.py --json build/extended-performance.json --keep build/extended
python3 tools/bench_extended.py --cases text_pipeline long_string_keys --scale 4 --processes 5 --samples 5 --warmups 2 --json build/extended-large.json
```

`--smoke` uses N=2, one process per execution mode and two measured samples. It checks
compilation, execution and agreement with CPython; its tiny timings are not performance
evidence. `--scale` multiplies each default N (ignored by smoke). `--cases` accepts
space-separated names. `--keep` must name a new directory; it retains generated drivers,
the copied kernels, LLVM IR and AOT executables. Without it those files are temporary.
`--compiler` accepts a shell-split command, such as `--compiler './pystachy'`, without shell
evaluation. `--timeout` bounds each command and its LLVM children (default 120 seconds).

The default JSON destination is `build/extended-performance.json`. It records raw outputs,
commands, samples, first-call times, wall times, median/min/max/MAD summaries, checksums,
source and driver hashes, revision/dirty status, toolchain/platform information, compiler
binary hash when resolvable, and relevant environment settings. Failures produce a nonzero
exit and a report with `status: failed`; failed or partial reports are not benchmark results.
`make bench-extended BENCH_ARGS='--scale 2'` is the optional timing entry point. CI runs only
`bench-extended-check`: controller failure tests plus all seven small differential cases.

## What the measurements include

| Measurement | Included work |
|---|---|
| `hosted_ir` | CPython startup plus `python -m pystachy ir`, including loading/lowering and IR output |
| `native_ir` | Native compiler startup plus the same IR generation/output |
| `aot_build` | Native frontend, linking runtime bitcode, LLVM optimization/code generation and executable link |
| `jit` wall | Fresh process, frontend, LLVM cleanup/ORC compilation, all calls and output |
| `aot` / `cpython` wall | Fresh process, all calls and output; AOT compilation is excluded |
| `first` | First kernel call inside that process; excludes frontend/process startup and printing |
| `hot` | Median of subsequent timed calls inside each process, then median across processes |

Each driver imports the same full kernels module, even when it calls only one case.
Compile measurements therefore include that shared module and the driver: they are not
isolated costs of compiling one function. Do not subtract independently measured phases
to claim an exact backend or JIT compilation cost.

Pystachy's current JIT uses LLVM ORC after a small fixed cleanup pipeline, with a precompiled
runtime object. It has no adaptive interpreter-to-JIT tiering. AOT instead optimizes the
linked program and runtime together at `-O2`; the JIT does not inline the runtime. Thus an
AOT/JIT execution gap can suggest optimization or call-boundary costs, but a profile is
needed to attribute it. First/hot differences can also reflect allocator, cache and GC state;
they do not establish adaptive JIT warmup or convergence.

The runner first executes an empty program to prime the runtime cache. That invocation is
saved separately as `cache_prime` and excluded from timing summaries. Subsequent empty JIT
processes are saved as `startup_jit`. Builds and JIT runs therefore use a warm runtime cache,
not a clean-install cost. `frontend_prime` also warms the hosted compiler's bytecode cache
before collecting its IR timings. A measured first call precedes `--warmups` additional calls; timed
samples follow within the same process. Each mode gets a fresh process for each repetition.
Execution order rotates between modes, and work runs sequentially.

Before timing is accepted, a CPython run establishes the expected checksum. Every first,
warmup and sample result must match it, including an additional AOT run with
`PYSTACHY_GC=stats`. This separate probe stores collection count/time, peak managed heap and
last-collection live bytes in `aot_gc_probe.stderr`; it is not part of timing summaries.
The probe forces `PYSTACHY_GC=stats`, even when the timed experiment uses `off`; it describes
normal collection in that separate process. Last-live is not final live memory and may be
zero if no collection occurred.
Managed heap is not process RSS. This runner has no RSS measurement or `--rss` option.

Default sample counts are modest and there is no automatic duration calibration. Increase
N until calls last long enough to measure, inspect the raw variation, and repeat on an idle
machine with the same CPU affinity and toolchain. Environment optimization/GC overrides are
honored and recorded, so remove accidental overrides before a baseline run. Timings are
diagnostic only: there is no speed threshold, aggregate score or new timing gate in CI.

## Compare and investigate

For before/after work, use two worktrees at explicit revisions and place identical copies
of this runner and the kernels in both. Build each worktree's native compiler there, and run
its controller from that worktree with `PYSTACHY_HOME` pointing to that same checkout. Each
side must use its own `pystachy.py`, `runtime.c`, `runtime.py`, `lib/` and runtime cache.
Pointing only `--compiler` at another checkout is insufficient: `hosted_ir` and recorded
source hashes still refer to the controller's checkout. Record any copied suite files as
the intentional dirty changes. Keep N, samples, flags and workload/driver hashes identical;
alternate before/after runs to check drift.

After the `--keep build/extended` run above, these existing tools can narrow a hotspot:

```sh
# Compiler shape growth; --ops requires CPython 3.12+ and records deterministic work counts.
python3 tools/scaling.py -s funcs,fields,lookups,gdicts -n 500,1000,2000 -r 3 --ops

# CPython-hosted frontend profile, not the native compiler or compiled runtime.
python3 -m cProfile -o build/frontend.prof -m pystachy ir build/extended/text_pipeline.py -o build/frontend.ll
python3 -m pstats build/frontend.prof

# Optional Linux native sampling, where perf is available and permitted.
perf record -g -- build/extended/text_pipeline.exe 10000 1 3
perf report
```

For a separate profiling build, `PYSTACHY_CFLAGS='-g -fno-omit-frame-pointer'` supplies clang
flags to the runtime and AOT compilation/link. It does not add Python source-level debug
information to generated IR. Keep instrumented runs separate from baseline timings.
`PYSTACHY_OPT=-dictfuse`, `-listget` or `-all` can test an optimization hypothesis using the
same runner and separate reports. Optional host-side pyperf can provide more rigorous
command statistics later; neither pyperf nor ASV needs to run inside the supported subset.

## Relationship to existing work

Keep [`performance.md`](performance.md), [`testing.md`](testing.md), `bench/run.sh`,
`tools/scaling.py`, and the deterministic dict/list/container-comparison probes as the
existing baselines and regression checks. This suite complements them with mixed runtime
work and first/hot-call measurements; it does not replace them.

The repository review for this prototype (2026-10-10) included tracking issue
[#4](https://github.com/den-run-ai/pystachy/issues/4), nightly/trend workflow
[#45](https://github.com/den-run-ai/pystachy/issues/45), command timeouts
[#49](https://github.com/den-run-ai/pystachy/issues/49), repeated string-key hashing
[#80](https://github.com/den-run-ai/pystachy/issues/80), no-op strip/full-slice allocations
[#82](https://github.com/den-run-ai/pystachy/issues/82), and retained capacity in small
nonempty lists [#87](https://github.com/den-run-ai/pystachy/issues/87). `long_string_keys`
directly stresses repeated key hashing. The text/list workloads provide broader context;
they are not specific regressions for every case in #82 or #87. The reviewed open PR list
had no conflicting performance-suite implementation; [#53](https://github.com/den-run-ai/pystachy/pull/53)
concerned CI. These are review-time observations, not a claim that the trackers stay unchanged.

## Source review and scope

All seven kernels are original implementations; no upstream benchmark code is vendored.
If future work copies an upstream case, pin its source revision, retain its per-file license
and attribution, and list subset adaptations. A family name alone does not imply equivalent
work or comparable results.

| Reference reviewed | Decision for this prototype |
|---|---|
| [pyperformance](https://github.com/python/pyperformance) | Useful workload corpus and metadata model; full harness/app dependencies exceed this subset. Existing numeric cases already cover common candidates. |
| [PyPy performance](https://pypy.org/performance.html) | Measure and profile first; distinguish runtime-heavy work and startup. Its adaptive-JIT warmup advice needs the ORC qualification above. |
| [PyPy speed](https://speed.pypy.org/) / [Python speed](https://speed.python.org/) | Historical dashboards are useful later; no dashboard dependency is needed to collect samples now. |
| [CinderX](https://facebookincubator.github.io/cinderx/) | Its ordinary/static/primitive configurations motivate distinguishing code-generation modes; retain object dispatch coverage rather than import a large Richards implementation. |
| [Python Interpreters Benchmarks](https://pybenchmarks.org/u64q/cython.php) | Workload inspiration only; source transformations and single/multicore differences prevent importing headline ratios. |
| [GraalPy JDK23 performance](https://www.graalvm.org/jdk23/reference-manual/python/Performance/index.html) | Separates execution from loading; this explicitly old documentation is not a current speed baseline. |
| [Optimization Ladder](https://cemrehancavdar.com/2026/03/10/optimization-ladder/) | Mixed records/strings complement numeric loops. The small text pipeline avoids adding a JSON dependency or copying published scores. |
| [numba-benchmark](https://github.com/numba/numba-benchmark) | ASV history and compilation/runtime separation are useful ideas; its numeric-library/tooling setup is unnecessary here. |
| [Exaloop/Codon benchmarks](https://www.exaloop.io/#benchmarks) | Broad numeric/container coverage; reuse existing numeric families and avoid comparing against differently threaded implementations. |
| [Nuitka performance](https://nuitka.net/user-documentation/performance.html) | Compiler flags matter; the supplied old Pystone results and minimum-run reporting are not a baseline for this suite. |

[pyperf's methodology](https://pyperf.readthedocs.io/en/stable/run_benchmark.html) additionally
motivates multiple processes, raw samples and explicit warmup accounting. The prototype
uses those principles without claiming pyperf's calibration or statistical guarantees.

## Measured observations

Initial local run on main `3542d63`, Linux x86-64, LLVM 18.1.3, CPython 3.12.14,
three processes per mode and three timed calls per process, default N. These are shared-host
diagnostics, not published speed claims. [Compact raw samples](../bench/extended/baseline-3542d63.json)
retain all measured wall/first/hot times, checksums, GC output and run-time source hashes;
repeated command paths/stdout are omitted. The snapshot predates small controller input-validation
and metadata fixes made during review; kernel sources and generated driver hashes are unchanged.

| Case | CPython hot, ms | JIT hot, ms | AOT hot, ms |
|---|---:|---:|---:|
| object_dispatch | 128.7 | 3.95 | 2.68 |
| text_pipeline | 129.9 | 49.76 | 52.30 |
| list_churn | 124.0 | 15.57 | 10.83 |
| exception_local | 149.0 | 11.46 | 5.40 |
| exception_unwind | 217.4 | 249.09 | 172.06 |
| long_string_keys | 9.94 | 498.38 | 512.96 |
| sort_records | 137.0 | 19.97 | 14.17 |

- Reused long string keys are about 50x slower than CPython in both compiled paths,
  consistent with #80. A hash-cache experiment is a higher-priority lead than numeric loop tuning.
  It needs its own before/after results and correctness checks; this PR does not implement it.
- Cross-function exceptions are about 22x/32x the local-handler case for JIT/AOT. This includes
  the helper-call cost and different generated code, so it is not a pure unwinder measurement.
  Avoid exception-driven hot paths where appropriate; profile before changing exception semantics.
- The string/dict pipeline has similar JIT/AOT times here; the GC probe reports only 2.1 ms
  collection time across all five calls. Profile parsing, allocations and runtime calls before
  blaming collection or assuming whole-program optimization will solve it.
- Cached empty JIT startup is about 65 ms; native IR generation is 5–6 ms versus hosted
  56–63 ms; full AOT builds are 0.43–0.79 s. Those independently measured phases are useful
  controls, not additive components of one measured process.

Several compiled kernels are still short; increase `--scale` for optimization decisions and
inspect dispersion in the generated report. Local bootstrap fixed points, controller tests and
all small/full-workload checksum comparisons passed. CI separately checks the repository's
supported Python 3.13 configuration.

The existing compiler scaling guard also passed for `funcs,lookups`, N=500/1,000, with
`--ops --check`: executed-line and copied/scanned-item counts grew approximately 2x.
This reuses the current generator and deterministic guard rather than adding a second
compiler-scaling framework.
