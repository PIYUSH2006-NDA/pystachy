# Performance

For opt-in object, container, allocation and exception diagnostics with separate compiler,
JIT startup and warmed execution measurements, see the [extended subset prototype](extended-performance.md).

Pystachy compiles each program to native code through LLVM, so compute-bound Python runs one to
two orders of magnitude faster than under CPython, and code that spends its time in strings and
dicts runs a few times faster. This page has the numbers, what they include, and where the time
goes.

## Benchmarks

`bench/run.sh` on a 4-core x86-64 VM (Linux, CPython 3.13.16, LLVM 18), median of three warm
runs, October 2026. JIT times include compilation, and every output is checked against
CPython's.

| benchmark | CPython | Pystachy JIT | Pystachy AOT | AOT speedup |
|---|---:|---:|---:|---:|
| `fib.py`: fib(35), calls | 0.80 s | 0.08 s | 0.04 s | 23× |
| `mandel.py`: mandelbrot, float loops | 1.26 s | 0.09 s | 0.04 s | 34× |
| `nbody.py`: n-body, floats and objects | 1.82 s | 0.10 s | 0.03 s | 59× |
| `spectral.py`: spectral norm, nested loops | 1.07 s | 0.09 s | 0.02 s | 67× |
| `sieve.py`: a 4M-element list | 0.76 s | 0.21 s | 0.15 s | 5× |
| `words.py`: word count, strings and dicts | 0.17 s | 0.10 s | 0.05 s | 3× |
| `dictlookup.py`: dict lookups, int and str keys | 0.90 s | 0.47 s | 0.39 s | 2× |
| `dictkeys.py`: dict keys that defeat a weak hash | 0.50 s | 0.25 s | 0.16 s | 3× |
| `setdisplay.py`: set displays of constants in loops | 0.40 s | 0.20 s | 0.12 s | 3× |

The speedup column is computed by `bench/run.sh` from the unrounded times. The first `run` after a
build also compiles and caches the runtime, which adds one to two seconds once. `bench/dictcount.py`
is measured [below](#optimizations-on-the-typed-ir).

Run them yourself with `make bench` (`bench/run.sh`): each program runs once under CPython, under
the JIT and as an AOT executable, and the script reports any output that differs from CPython's;
the benchmarks step of `make verify` fails on one.

## Where the gains are smaller

The sieve is memory-bound, and string- and dict-heavy code spends its time in the C runtime, as
CPython does, so their gains are smaller. Integer arithmetic is overflow-checked, which costs
most on call-heavy integer code: `fib` took 0.050 s instead of the 0.024 s of Ouro v1's
wrapping arithmetic when the two were compared, because LLVM can no longer turn
`fib(n - 1) + fib(n - 2)` into a loop; the other benchmarks are unaffected.

## Optimizations on the typed IR

The passes on the typed IR ([internals.md](internals.md#the-typed-ir)) remove repeated work: a
for loop reads the items of a list it steps through without a bounds check (`listget`), and a
dict lookup that a membership test or a read of the same key made is reused (`dictfuse`), so
`if k in d: d[k] += 1` hashes `k` once. `bench/dictcount.py` counts keys that way; best of 11
runs, with the dict lookup fusion turned off (`PYSTACHY_OPT=-dictfuse`) and on:

| `bench/dictcount.py` | CPython | Pystachy JIT | Pystachy AOT |
|---|---:|---:|---:|
| without `dictfuse` | 0.85–0.93 s | 0.254 s | 0.162 s |
| with `dictfuse` | 0.85–0.93 s | 0.183 s | 0.112 s |

The fused lookups make it 31% faster AOT and 28% faster under the JIT. `PYSTACHY_OPT=-all` turns
every pass off, for comparisons like this one.

## Tuples made in the frame

A call of a function with `*args` makes the tuple of its extra arguments in the caller's frame,
not on the heap, where the function keeps it nowhere a copy before each statement does not see
(`Gen.stack_ok`): not in a closure, a generator, a global or a while loop's test. The function
gives a local that holds the tuple (`args`, `key = args`) its heap copy, made once per call, before
any statement that uses it other than to look it up (`x in d`, `d[x]`, `d.get(x)`, `x in xs`) or to
read its items (`f(*x)`, `len(x)`, `x[i]`, `for`, `if x`) (`Gen.keep_stack`). A tuple display that a
lookup takes as its key (`(i, j) in memo`, `memo[(i, j)]`, `memo.get((i, j), d)`) is made in the
frame too. So a hit of `lib/functools`' caches, whose `__call__(self, *args)` only looks its key up,
and of a memo dict allocates nothing; a miss allocates the key it stores, once, as before.

`bench/memo.py`, a memoized dynamic program (the fewest scalar multiplications of a chain of 220
matrices, `@cache` over two ints, 3.5 million hits), median of 5 runs:

| `bench/memo.py` | CPython | Pystachy AOT |
|---|---:|---:|
| tuples on the heap | 0.355 s | 0.147 s (2 collections, 36.4 MiB peak) |
| tuples in the frame | 0.355 s | 0.068 s (none, 6.1 MiB peak) |

An `lru_cache` hit takes 17 ns instead of 22 (an `int` argument), 12 instead of 14 (unbounded),
and 19 instead of 23 (`str` and `int`); CPython's C `lru_cache` takes 60 to 84 ns.

## The first part of a split

`s.split(sep)[0]`, `s.split(sep, n)[0]` and `s.split()[0]`, where `s` is a str, make the first
part alone (`pys_str_split_first`): the text before the first `sep`, or the first word, without
the list or the other parts. It raises what the list's `[0]` would: `ValueError` for an empty
`sep`, `IndexError` where `s` has no word. Taking the name off each of 1,000,000 tab-separated
lines, best of 5 runs, AOT:

| per line | CPython | before | now |
|---|---:|---:|---:|
| `line.split("\t", 1)[0]` | 81.5 ns | 31.4 ns | 12.2 ns |
| `line.split("\t")[0]` | 104.3 ns | 42.3 ns | 12.8 ns |
| `line[:line.find("\t")]`, -1 tested | 66.8 ns | 13.5 ns | 13.8 ns |

## Inlining under the JIT

`lli` compiles each function as it is, so a small helper called in a hot loop stays a call under
the JIT, where the AOT tier's `-O2` inlines it. `pystachy run` therefore runs LLVM's inliner
(`cgscc(inline, ...)`) on a program of up to 20,000 lines of IR (#211). Best of 5, `pystachy run`
with its compilation:

| | without | with the inliner |
|---|---:|---:|
| `dot3()` of six floats, 50M calls (#211) | 0.249 s | 0.095 s |
| `bench/spectral.py` | 0.144 s | 0.085 s |
| hello world | 0.044 s | 0.043 s |
| the other `bench/*.py` | | within 2% |

The inliner's own time grows with the IR: about 2 to 3 ms per 1,000 lines (+24 ms on 9,948 lines,
+28 ms on 16,860). Above 20,000 lines, which a program that imports `lib/re` passes (35,000), and
the compiler's 277,000, where it would add 0.55 s to `opt`'s 0.7 s, the JIT keeps its start-up.
`PYSTACHY_JIT_INLINE` sets the limit, and `0` turns the inliner off.

## The cost of exceptions

Code that does not raise pays nothing for a `try` statement (under the JIT, two runtime calls as
it is entered), and a raise that a `try` of the same function catches is a branch, which costs
tens of nanoseconds. A raise that leaves its function unwinds the stack with the Itanium C++
ABI's unwinder, which reads each frame's tables and is slower than CPython: a `KeyError` raised
in a callee and caught by its caller, 500,000 times, takes 0.44 s AOT and 0.54 s under the JIT,
against 0.11 s under CPython, about a microsecond per raise
([internals.md](internals.md#exceptions-by-table-driven-unwinding)).

## Start-up and memory

The JIT tier starts a program in under 0.1 s: `pystachy run` of a hello world takes about 46 ms
on the machine above, compilation included, and peaks at 58 MiB, most of it `lli`; the AOT
executable takes 1 ms and 1.8 MiB (CPython: 9 ms and 8.5 MiB). The collector keeps peak memory
near the live set: ten million short-lived strings (`str(i)` in a loop) peak at 35 MiB instead
of 155 MiB with Ouro v1's bump allocator, and building and discarding fifty 2M-element lists at
50 MiB instead of 1.5 GiB, while running faster (0.47 s instead of 0.52 s, and 0.30 s instead of
2.0 s). Sorting is CPython's timsort: 2M random ints sort in 0.32 s, against 0.53 s with the
earlier merge sort.

Each `str` caches its dict hash, so a key that is looked up again is not hashed again (#99):
500,000 lookups of a 1 KB key take 1.8 ms AOT instead of 519 ms (CPython: 14 ms), and of a tuple
holding one, 14 ms instead of 540 ms. The cache costs 8 bytes per string, which moves short
strings from 16- to 24-byte slots: a million retained short strings hold 30.9 MiB live instead
of 23.3 MiB, and the native compiler's peak RSS, translating the same 16,757 lines, rose from
125.7 MiB to 142.1 MiB (+13%), its CPU time unchanged. A baseline of every benchmark's time and
peak RSS, start-up and the compiler's own build, at commit 0ffadca, is in
[#4](https://github.com/den-run-ai/pystachy/issues/4#issuecomment-6126004947).

## Compile time

The native compiler translates its own 17,300 lines to LLVM IR in about 0.57 s of CPU time,
peaking at 153 MiB, against 2.8 s when CPython runs it, and a full AOT build of itself, with
clang -O2, takes about 17.4 s of CPU. Before the typed IR and exceptions, its 11,000 lines took
0.2 s, 1.4 s and 12 s on the same machine, and the compiler of 7,000 lines took 0.09 s to
translate itself and 7.5 s to build. Per source line, translation to LLVM IR has grown from
about 13 µs (7,000 lines) to 18 µs (11,000 lines, which added CPython's syntax checks and the
definition-time checks of imported modules) and 33 µs now, with the typed IR built, optimized
and lowered as steps of their own; the clang build stays near 1 ms per line.

Compile time grows linearly with the program: `tools/scaling.py` generates programs that grow in
one dimension at a time (functions, globals, classes, modules, fields, call and import chains,
`elif` chains, comprehensions), and `make verify` fails if what the CPython-hosted compiler
executes grows faster than the program. Dict lookups stay fast for adversarial keys too:
`make verify`'s dict-probes step counts the table slots visited for twelve key patterns that
defeat a weak hash, so no timing threshold is needed ([testing.md](testing.md#make-verify)).
