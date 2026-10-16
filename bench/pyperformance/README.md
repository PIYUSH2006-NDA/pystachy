# pyperformance benchmarks

These are 19 of the 52 benchmarks tried from [pyperformance](https://github.com/python/pyperformance)
1.14.0, adapted so that Pystachy compiles them. CPython runs the same adapted files, so each
comparison runs identical source in CPython, the JIT and AOT. The adaptations and smaller
inputs change the work, so these results are not comparable with published pyperformance numbers.
The measurements are in [pyperformance results](../../docs/pyperformance.md).

The 52 are the 31 benchmarks that this port set out to try, mostly CPU-bound and often cited,
and the 21 others that need no third-party package. The release's other 21 benchmarks list
packages in their `requirements.txt` that have no port: `asyncio_websockets`, `chameleon`,
`coverage`, `dask`, `django_template`, `docutils`, `dulwich_log`, `fastapi`, `genshi`,
`hg_startup`, `html5lib`, `mako`, `networkx`, `sphinx`, `sqlalchemy_declarative`,
`sqlalchemy_imperative`, `sqlglot_v2`, `sympy`, `tornado_http`, `xdsl` and `yaml`.

## Run

From the repository root, after building the compiler:

```sh
make bench-pyperformance-check
make bench-pyperformance
python3 tools/bench_pyperformance.py --benchmarks richards nbody --runs 3
python3 bench/pyperformance/richards.py 10
./pystachy run bench/pyperformance/richards.py 10
```

Each benchmark's main takes the number of loops as its first argument; some also take input
sizes. It prints its results to standard output and the seconds of the part that pyperf would
time to standard error. The check runs small inputs once and compares CPython, JIT and AOT
output, without timings. `make bench-pyperformance` runs five processes per mode and writes
`build/pyperformance.json`. Both targets accept `BENCH_COMPILER`; `BENCH_ARGS` adds options to
the measured run. `--compiler "python3 -m pystachy"` uses the CPython-hosted compiler.
`PYSTACHY_*` settings apply to the compiled runs: `PYSTACHY_OPT=-all` disables the typed-IR
passes, and `PYSTACHY_GC_STRESS_PROGRAM=1` collects at every allocation in JIT and AOT runs, as
in `tests/run.sh`.

## Provenance

The sources are `pyperformance/data-files/benchmarks/bm_NAME/run_benchmark.py` from the
pyperformance 1.14.0 sdist, `pyperformance-1.14.0.tar.gz`, SHA-256
`91f74393997b604375ad5b79bf569a24076d70181c076a53abad5383a238a8aa`. Given that sdist,
`python3 tools/bench_pyperformance.py --census pyperformance-1.14.0.tar.gz` checks these hashes,
checks that each changed hunk of a port carries a `# Pystachy port:` note and that each port
times what pyperf times, and compiles each upstream file with only pyperf's runner replaced,
reporting the first compiler error.

| Benchmark | Upstream SHA-256 | Status |
|---|---|---|
| `2to3` | `a491c6dfe070a073cae07fc07f903afcc6d795207f2c70ab96f0ac0d9363d916` | blocked |
| `argparse` | `f914991901e5a24d536753c3b2b5229b1e9e5d4d982ba82da2e1cfbbf3677feb` | blocked |
| `async_generators` | `0441979a5ffc49c1e44539f5cb5a082bb70fcef5627619872feb4f3901351de5` | blocked |
| `async_tree` | `7c1493bc27c5c41f70f51cbf46a33c77b791915364ce619231461441f042178b` | blocked |
| `asyncio_tcp` | `fa993861ad75dcd724d282442e671095ad708a9dcb87e4314831d04006ad4a23` | blocked |
| `barnes_hut` | `802a1c170b82a5d82ea69b7a893f09d4b50b4f232e20a8e1c1bb8b2c04e6af1d` | ported |
| `base64` | `e2f1e7d4dbfbb2c722833081496497344550e4367f85f67f373fb8aa22cd35ed` | blocked |
| `bpe_tokeniser` | `c7255345499e118181785370b0996e8cc1056491b9678b3fbeb02421e3f9b2df` | blocked |
| `chaos` | `5d20fd29c8ea89e0ebe4040ae4c05f26f1a620cd2a7fc654d9d7f8cb205651ac` | ported |
| `comprehensions` | `6047efc06287a24a646f00fc8a8d47429f7cdeab3e942230e13cf6d7cefa6343` | blocked |
| `concurrent_imap` | `d5bfb854e7a1d754f3033132dca397704ea7ed2aabfd6d625396b61b82a9e316` | blocked |
| `coroutines` | `9358a7d967ed16859b5a163a4e416d897d6f104b3603c56ad77903791211fc7f` | blocked |
| `crypto_pyaes` | `236222412fd81b5e13d9c818574b575809eccff17419d667f34cf0e9148aa724` | blocked |
| `decimal_factorial` | `0b88119beb7a2151ef59f0d7d969e655850d9aeef143426efd0e0a656b2bbcc6` | blocked |
| `decimal_pi` | `eb3974785e602143f16fcfbd07ffd8b742b326096d9fd914c59a79531175104c` | blocked |
| `deepcopy` | `9e1550442cbccfaff8a4988936487c091ac18bcc9c8ebdc41c1cb747c14ea078` | blocked |
| `deltablue` | `70da5e16cd5b14f2f398ccc066794b83a30d997c2d91150695b8f938f934dc30` | ported |
| `fannkuch` | `2a8e4bc4c5e7e8ac605a4ca8246cc4baeab5336ac986d976e33657162750e8bf` | ported |
| `float` | `b4f61a0978f5b0af2c0d07544ae26422868992e62b8f40e2967e3c694fc1b9a9` | ported |
| `gc_collect` | `7886042f07e517abb79c58643a4b488710f3079936c6990522624bfb9c2acb9b` | blocked |
| `gc_traversal` | `0798ab87ca12687c68e101d14ae9ac0c50eaa9b4f14ecee3882f7e499191828f` | blocked |
| `generators` | `46c59dc44cb63b2c0fed75e6d82875daa237a92d03c87861078513c7b10d4621` | blocked |
| `go` | `ea4c0ebaf32515f8549c64c9291ab13d47bb802e01a82203c37b5066d1bfb463` | ported |
| `hexiom` | `d7518220380d27449b8951bc9ca2e19593569d9bd9f5cb6d86867f354f22e115` | ported |
| `json_dumps` | `023c991ff827fdcbfcfb2b7e3cadf023352a61d1903643d8af0ef302a0db1bf7` | blocked |
| `json_loads` | `16c41ff06bf3173d30158c767340d389c459a656e997e306719891d50f09646f` | blocked |
| `logging` | `6ff62fdc4c6b520b01475407b526ed609299402ed8ad8d344038b559a120159a` | blocked |
| `mdp` | `3db5bfb8c9e2602f181cee809c24b2bd61e7c088e89e8e22867b8d46c4d0fcf1` | blocked |
| `meteor_contest` | `b616f5f87e129a6b35650452951f40a7812cf22efff5a0777e51287da13c2f48` | ported |
| `nbody` | `d1385e816d7cfea361b7915e2cf70138cd6b84f40df8bd5152638851f7bcac2b` | ported |
| `nqueens` | `f50ef0d82036790c99f5469b9cffc368e097de860231b328caa6652183af059e` | ported |
| `pathlib` | `113a1cbbec13165dfdb84db649d8114279460110733957a3749ffb9c9527612d` | blocked |
| `pickle` | `31c0e30be79514b45db0d4e858632eb429b0fea3edbac6463ad5f34d92f3cab8` | blocked |
| `pidigits` | `4bf89183acb8651623676ece6e10787b6c71eec549fe53ce17a62a812ef7447d` | blocked |
| `pprint` | `07ef57201c7919aedf9e340c7fb1561a40dfee698818c9694930f3e427091d6d` | blocked |
| `pyflate` | `ec5347c7045af86ba33e1b2c6f64bc4b506d0ade3b77391d7e41863fe25fb464` | blocked |
| `python_startup` | `4cc396c9fe32d633a5e902c8ca738391a4cfe80b6d7658a9d9048989fc796d0c` | blocked |
| `raytrace` | `88ef4d9060d8e8f6ce40f376477aaf89cc808fa44813225a3071a05a1467f017` | ported |
| `regex_compile` | `cdbc509e515840e469209ed5fc77ca3fe352278203cc1a7dad874db4e863dc6c` | blocked |
| `regex_dna` | `d820dbdf12262cd11a543ae3dc3fd85793a20220d5a15ef687d8ef57a75c97c6` | ported |
| `regex_effbot` | `0823b6507f8babea2238847562d9c9af31000ea57cbb695e5d47053321ea68c7` | ported |
| `regex_v8` | `c22f820cb9a031a892ec0341eecca81c758dc25ee5413613d18eddfdff54a491` | ported |
| `richards` | `a4512668525331960c54043b5150a3fff92badaeaba850a941893ac69a1028d8` | ported |
| `richards_super` | `665b3d5551171e147c127b6f8671edc9a7703c736d317cc4a991bb00f599dc36` | ported |
| `scimark` | `427b21b8a3802418ea3c2fe584335658a6c91c7f74fce4df9410efa60cd84d6e` | ported |
| `spectral_norm` | `a3390ec6d75606fec30c4b59ad5f77d5292cd8e36f445197232a34560a880b18` | ported |
| `sqlite_synth` | `dcba7a6889e66f08480f4332860208d624678fc42a03be5c8f3b6f1f894231fd` | blocked |
| `telco` | `a3acb202b3d4eb750aca977ce354f8ecc1f6adae17a695ed2e5be615e4797605` | blocked |
| `tomli_loads` | `a94f7368f9656044f45244eb71da4f29a785c154c4a75aa15ca5c0e3c609c0d0` | blocked |
| `typing_runtime_protocols` | `dfc0cbd25f2968ee6982ff93adde92a1fa2a56ffbed6dde2d1f9cb853c340961` | blocked |
| `unpack_sequence` | `0dafe97531abc4a5baf30fe011db7acb3bf1e64cd4e41acb0c7db2bb141a8382` | ported |
| `xml_etree` | `1d824c4d4dd92a7598e085dbdf7beed3809a75e4d6972c90377822c78f73477c` | blocked |

## License

pyperformance is distributed under the MIT License; [LICENSE](LICENSE) and [AUTHORS](AUTHORS)
are its `COPYING` and `AUTHORS` files. Each port keeps its upstream header. `regex_v8.py`'s
header carries the V8 project's BSD license, and `raytrace.py`'s states the MIT License.
`deltablue.py`'s docstring says the JavaScript original was licensed under the GPL;
pyperformance distributes this Python port under its MIT License. See
[THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES).

## Adaptations

Each edit is marked `# Pystachy port:` in the source. Every port has these changes:

- `import pyperf` is removed. A main that reads the loop count and sizes from `sys.argv`
  replaces `pyperf.Runner` and prints the results, or a checksum.
- The seconds the main prints are for the part that pyperf would time. Where the runner calls
  `bench_func()`, the main times a loop of calls of that function and nothing else. Where it
  calls `bench_time_func()`, each benchmark function keeps its own timer around the same loop,
  with `time.perf_counter()`, which is `pyperf.perf_counter()`. Instead of returning the
  seconds, it appends them to a list `TIMED`, whose sum the main prints, and returns its result,
  or a checksum when it discards its result. `TIMED_PART` in `tools/bench_pyperformance.py`
  records which function each port times; the unit tests check the ports against it, and
  `--census` checks it against the upstream files.
- `range_it = range(loops)` becomes a list: a `range` object is not a value.

| Benchmark | Other adaptations |
|---|---|
| `barnes_hut` | Integer zeros that become floats are float literals. Constructors, the particle list and the child nodes are annotated. |
| `chaos` | A Park–Miller generator replaces `random.seed()` and `randrange()`, so the points differ from upstream. `GVector` has float parameters and defaults; `__rmul__ = __mul__` becomes a method; fields are annotated; loops replace two-clause comprehensions; `length` starts as `0.0`; `x` and `y` are converted to int in one assignment each; an impossible `type()` message is a literal. `main()` returns the game, whose `create_image_chaos()` the main times with the default arguments. |
| `deltablue` | `OrderedCollection(list)` uses become annotated lists. `super(C, self).__init__()` calls of `object` are commented out, and `Strength` replaces `self.__class__`. `Constraint` declares the methods its subclasses define. `Variable.value` is `int \| float`, and other fields, parameters and recursive methods are annotated. |
| `fannkuch` | The reversing slice assignment uses a slice, `reverse()` and concatenation. |
| `float` | `self.x = x = sin(i)` is split so that fields can be annotated, and so are `__init__` and `points`. |
| `go` | The same generator replaces `random`, so the games differ from upstream. Fields set outside `__init__` are declared in the class body. `useful()` returns `bool(...)`, and `score()` counts in a float. `maxscore` starts as `-1.0`. The never-called `Board.check()`, whose sets hold `Square` objects, is commented out. |
| `hexiom` | A class-body default `HIGHEST_VALUE_STRATEGY` becomes its value, `2`. Conditional `range` values become lists, and `[None] * n` replaces `n * [None]`. Fields and constructors are annotated. `main()` returns the solution. |
| `meteor_contest` | `SE` is `51`, not `51.0`, because floats cannot be set elements or dict keys. Loops replace a two-clause comprehension and `dict()` of a generator expression. A list replaces another generator expression, and `''.join(reversed(s))` replaces `s[::-1]`. |
| `nbody` | None. |
| `nqueens` | `permutations()` and `n_queens()` return lists instead of yielding. `tuple()` takes a list comprehension. `reverse()` and concatenation replace a slice step and a slice assignment. |
| `raytrace` | A list replaces `array.array('B')`. `Vector` and `Point` have float coordinates, and the scene uses float literals. Class attributes are declared. Unreachable `Point` and `Vector` results are commented out of `Vector.__add__()` and `Point.__sub__()`. Raising a string becomes the `TypeError` it raises. Keyword parameters replace `**kwargs`, and the image is not written. |
| `regex_dna` | The sequence is an ASCII `str`, not bytes. The generator builds lists of strings, and the patterns are strings. |
| `regex_effbot` | A global replaces the function attribute `bench_regex_effbot.data`, and a loop replaces a dict comprehension. The `USE_BYTES` branches, never taken, are commented out. |
| `regex_v8` | None besides the checksum, computed after the timed loops because the blocks discard their results: each regex's substitution in each string. |
| `richards`, `richards_super` | Constructors, fields and the `Task` methods that inference needs are annotated. `BUFSIZE_RANGE` is a list. |
| `scimark` | Lists replace `array('d')` and `array('i')`. `Random`'s class constants are written out, and fields set by `initialize()` are declared. `ArrayList` no longer derives from `Array2D`, because its rows have a different type; its items are rows, and the inherited methods are copied. `indexes()` returns a list. `Array2D` is passed as `None` because classes are not values, and the `BENCHMARKS` table is replaced by the main. |
| `spectral_norm` | Accumulators and `u` start as floats. |
| `unpack_sequence` | A tuple literal replaces `tuple(range(10))`. The main runs upstream's default, `bench_all()`: the tuple and the list variants. |

The `random` substitutes produce 31-bit values, including `go`'s Zobrist hash strings.
Results within a benchmark are checked against CPython, not against upstream pyperformance.

## Blocked

`--census` reports these first errors with the compiler of main `bdc20a2`. Each upstream file
has only pyperf's import and runner replaced with a direct call of the benchmark. The last column
lists further blockers found by reading the upstream code; there may be others.

| Benchmark | First compiler error | Other blockers |
|---|---|---|
| `2to3` | `bm_2to3.py:1: error: module 'glob' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no glob.py on the module path` | None to port: `runner.bench_command()` times a CPython subprocess that runs `lib2to3` |
| `argparse` | `bm_argparse.py:9: error: module 'argparse' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no argparse.py on the module path` | The `argparse` module has no port |
| `async_generators` | `bm_async_generators.py:21: error: async functions are not supported` | Asynchronous generators (`async for`, `yield` in `async def`) and an event loop |
| `async_tree` | `bm_async_tree.py:20: error: module 'asyncio' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no asyncio.py on the module path` | `async def`, `await`, asyncio tasks and task groups, and `random` |
| `asyncio_tcp` | `bm_asyncio_tcp.py:9: error: module 'asyncio' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no asyncio.py on the module path` | `async def`, asyncio streams over a TCP connection, and `ssl` |
| `base64` | `bm_base64.py:10: error: module 'base64' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no base64.py on the module path` | The `base64` module, `bytes`, and `random.randbytes()` |
| `bpe_tokeniser` | `bm_bpe_tokeniser.py:16: error: module 'pathlib' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no pathlib.py on the module path` | `bytes` keys and values, `collections.Counter`, `max(key=...)` over a counter |
| `comprehensions` | `bm_comprehensions.py:8: error: module 'enum' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no enum.py on the module path` | Dict comprehensions, a slice step and `Iterable[Optional[Widget]]` parameters |
| `concurrent_imap` | `bm_concurrent_imap.py:6: error: module 'multiprocessing' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no multiprocessing.py on the module path` | Process and thread pools |
| `coroutines` | `bm_coroutines.py:10: error: async functions are not supported` | Coroutine objects and `send()` |
| `crypto_pyaes` | `bm_crypto_pyaes.py:13: error: bytes literals are not supported (there is no bytes type)` | The pyaes port's CTR mode encrypts `str` code points, while Pystachy iterates non-ASCII text by UTF-8 bytes |
| `decimal_factorial` | `bm_decimal_factorial.py:17: error: module 'decimal' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no decimal.py on the module path` | The `decimal` module |
| `decimal_pi` | `bm_decimal_pi.py:19: error: module 'decimal' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no decimal.py on the module path` | The `decimal` module |
| `deepcopy` | `bm_deepcopy.py:9: error: module 'copy' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no copy.py on the module path` | `__reduce__`, `__dict__`, and a dataclass field typed as bare `list` |
| `gc_collect` | `bm_gc_collect.py:2: error: module 'gc' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no gc.py on the module path` | It times CPython's cycle collector through `gc.collect()` |
| `gc_traversal` | `bm_gc_traversal.py:2: error: module 'gc' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no gc.py on the module path` | It times CPython's cycle collector through `gc.collect()` |
| `generators` | `bm_generators.py:21: error: 'yield' is not supported (there are no generator functions): __iter__ can return iter(xs) of a list xs of the items` | `yield from`, `range` values and their slices |
| `json_dumps` | `bm_json_dumps.py:1: error: module 'json' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no json.py on the module path` | `globals()`, and dicts whose values have different types |
| `json_loads` | `bm_json_loads.py:10: error: module 'json' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no json.py on the module path` | The `json` module, and `random.Random` |
| `logging` | `bm_logging.py:18: error: module 'logging' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no logging.py on the module path` | A dict of different functions; each function has its own type |
| `mdp` | `bm_mdp.py:2: error: 'defaultdict' from 'collections' is not supported: no definition or submodule was found on the module path` | `fractions.Fraction`, `namedtuple`, generators, and dict keys that are tuples of different shapes |
| `pathlib` | `bm_pathlib.py:10: error: module 'pathlib' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no pathlib.py on the module path` | `pathlib`, `shutil`, and a directory of files |
| `pickle` | `bm_pickle.py:15: error: module 'datetime' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no datetime.py on the module path` | The `pickle` module, and `datetime` values |
| `pidigits` | `bm_pidigits.py:11: error: module 'itertools' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no itertools.py on the module path` | Arbitrary-precision integers (Pystachy's are checked 64-bit) and generators |
| `pprint` | `bm_pprint.py:9: error: module 'pprint' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no pprint.py on the module path` | `PrettyPrinter` on a list of mixed tuples |
| `pyflate` | `bm_pyflate.py:19: error: module 'hashlib' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no hashlib.py on the module path` | `bytes`, `struct`, and a binary input file (bzip2 and gzip decoders) |
| `python_startup` | `bm_python_startup.py:19: error: module 'subprocess' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no subprocess.py on the module path` | None to port: `runner.bench_command()` times the startup of a CPython subprocess |
| `regex_compile` | `bm_regex_compile.py:23: error: cannot infer the type of 'regexes', which capture_compile() reads, where it is defined: annotate it (regexes: T = ...)` | Replacing `re.compile`, `re.search` and `re.sub` with closures, and importing the other two regex benchmarks as modules |
| `sqlite_synth` | `bm_sqlite_synth.py:9: error: module 'sqlite3' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no sqlite3.py on the module path` | The `sqlite3` module |
| `telco` | `bm_telco.py:18: error: module 'decimal' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no decimal.py on the module path` | The `decimal` module, `struct.unpack()`, and a binary input file |
| `tomli_loads` | `bm_tomli_loads.py:12: error: module 'pathlib' is not supported: it is not a builtin module (sys, os, os.path, math, tempfile, typing, dataclasses, __future__, builtins, time, errno) and there is no pathlib.py on the module path` | The `tomli` package, which has no port; `ports/tomli_w` is the writer |
| `typing_runtime_protocols` | `bm_typing_runtime_protocols.py:38: error: unsupported base class: single inheritance requires a previously declared ordinary class or a supported exception class` | `typing.Protocol` classes, and `isinstance()` checks against them |
| `xml_etree` | `bm_xml_etree.py:15: error: 'defaultdict' from 'collections' is not supported: no definition or submodule was found on the module path` | `xml.etree.ElementTree`, `globals()`, and temporary files |

The ported benchmarks' upstream files stop at these first errors before adaptation:

| Benchmark | First compiler error of the upstream file |
|---|---|
| `barnes_hut` | `bm_barnes_hut.py:281: error: expected int, got float` |
| `chaos` | `bm_chaos.py:7: error: module 'random' is not supported` |
| `deltablue` | `bm_deltablue.py:26: error: unsupported base class: single inheritance requires a previously declared ordinary class or a supported exception class` |
| `fannkuch` | `bm_fannkuch.py:34: error: assignment to a slice is not supported` |
| `float` | `bm_float.py:47: error: cannot infer the type of a list of None; add a type annotation (xs: list[T] = [], or -> list[T] on a function returning the list)` |
| `go` | `bm_go.py:5: error: module 'random' is not supported` |
| `hexiom` | `bm_hexiom.py:151: error: class attribute 'HIGHEST_VALUE_STRATEGY' of 'Done' used in a class-body default is not supported` |
| `meteor_contest` | `bm_meteor_contest.py:88: error: expected int, got float` |
| `nbody`, `spectral_norm`, `unpack_sequence` | `range() is only supported in a for loop, after 'in', or as the argument of list(), sorted(), sum(), min(), max(), any(), all(), math.fsum(), math.prod() or str.join()` |
| `nqueens` | `bm_nqueens.py:54: error: 'yield' is not supported (there are no generator functions)` |
| `raytrace`, `scimark` | `module 'array' is not supported` |
| `regex_dna` | `bm_regex_dna.py:152: error: bytes literals are not supported (there is no bytes type)` |
| `regex_effbot` | `bm_regex_effbot.py:156: error: type <function bench_regex_effbot> has no attribute 'data'` |
| `regex_v8` | None: it compiles with only the runner replaced |
| `richards`, `richards_super` | `inheritance with generic class templates is not supported: annotate __init__ parameters` |

The module messages in this second table are abbreviated after `is not supported`; the
census reports the complete messages and line numbers.
