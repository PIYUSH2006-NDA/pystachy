"""Ported pyperformance 1.14.0 benchmarks; see bench/pyperformance/README.md.

The controller runs on CPython. Each benchmark is an adapted upstream file whose main prints
deterministic results to stdout and, to stderr, the seconds of the part that pyperf would time
(TIMED_PART). Every JIT and AOT run must print exactly what CPython printed, or the run fails.
Timings are advisory: there are no thresholds. --census reads the pinned sdist, replaces each
upstream file's pyperf runner with a direct call of its benchmark, reports the first compiler
error, and checks each port's notes and timed part against the upstream file.
"""
import argparse
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import shlex
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time

from bench_extended import execute

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "pyperformance"
SDIST_SHA256 = "91f74393997b604375ad5b79bf569a24076d70181c076a53abad5383a238a8aa"
SDIST_DIR = "pyperformance-1.14.0/pyperformance/data-files/benchmarks/"

# The ported benchmarks: the arguments of a measured run (sized for most of a second of
# CPython 3.13 on an idle 2.1 GHz x86-64 core), and of a --smoke run (correctness only).
# bench/pyperformance/NAME.py's main reads them; each starts with the number of loops.
BENCHMARKS = {
    "barnes_hut": (["1"], ["1", "5", "50"]),
    "chaos": (["10"], ["1", "200"]),
    "deltablue": (["200"], ["1", "20"]),
    "fannkuch": (["2"], ["1", "7"]),
    "float": (["10"], ["1", "1000"]),
    "go": (["4"], ["1"]),
    "hexiom": (["100"], ["1"]),
    "meteor_contest": (["6"], ["1"]),
    "nbody": (["10"], ["1", "100"]),
    "nqueens": (["10"], ["1", "6"]),
    "raytrace": (["4"], ["1", "20", "20"]),
    "regex_dna": (["4"], ["1", "1000"]),
    "regex_effbot": (["20"], ["1"]),
    "regex_v8": (["4"], ["1"]),
    "richards": (["20"], ["1"]),
    "richards_super": (["20"], ["1"]),
    "scimark": (["2"], ["1"]),
    "spectral_norm": (["10"], ["1"]),
    "unpack_sequence": (["50000"], ["1"]),
}

# SHA-256 of each upstream bm_NAME/run_benchmark.py tried, ported or not.
UPSTREAM = {
    "barnes_hut": "802a1c170b82a5d82ea69b7a893f09d4b50b4f232e20a8e1c1bb8b2c04e6af1d",
    "bpe_tokeniser": "c7255345499e118181785370b0996e8cc1056491b9678b3fbeb02421e3f9b2df",
    "chaos": "5d20fd29c8ea89e0ebe4040ae4c05f26f1a620cd2a7fc654d9d7f8cb205651ac",
    "comprehensions": "6047efc06287a24a646f00fc8a8d47429f7cdeab3e942230e13cf6d7cefa6343",
    "coroutines": "9358a7d967ed16859b5a163a4e416d897d6f104b3603c56ad77903791211fc7f",
    "crypto_pyaes": "236222412fd81b5e13d9c818574b575809eccff17419d667f34cf0e9148aa724",
    "deepcopy": "9e1550442cbccfaff8a4988936487c091ac18bcc9c8ebdc41c1cb747c14ea078",
    "deltablue": "70da5e16cd5b14f2f398ccc066794b83a30d997c2d91150695b8f938f934dc30",
    "fannkuch": "2a8e4bc4c5e7e8ac605a4ca8246cc4baeab5336ac986d976e33657162750e8bf",
    "float": "b4f61a0978f5b0af2c0d07544ae26422868992e62b8f40e2967e3c694fc1b9a9",
    "generators": "46c59dc44cb63b2c0fed75e6d82875daa237a92d03c87861078513c7b10d4621",
    "go": "ea4c0ebaf32515f8549c64c9291ab13d47bb802e01a82203c37b5066d1bfb463",
    "hexiom": "d7518220380d27449b8951bc9ca2e19593569d9bd9f5cb6d86867f354f22e115",
    "json_dumps": "023c991ff827fdcbfcfb2b7e3cadf023352a61d1903643d8af0ef302a0db1bf7",
    "logging": "6ff62fdc4c6b520b01475407b526ed609299402ed8ad8d344038b559a120159a",
    "mdp": "3db5bfb8c9e2602f181cee809c24b2bd61e7c088e89e8e22867b8d46c4d0fcf1",
    "meteor_contest": "b616f5f87e129a6b35650452951f40a7812cf22efff5a0777e51287da13c2f48",
    "nbody": "d1385e816d7cfea361b7915e2cf70138cd6b84f40df8bd5152638851f7bcac2b",
    "nqueens": "f50ef0d82036790c99f5469b9cffc368e097de860231b328caa6652183af059e",
    "pidigits": "4bf89183acb8651623676ece6e10787b6c71eec549fe53ce17a62a812ef7447d",
    "pprint": "07ef57201c7919aedf9e340c7fb1561a40dfee698818c9694930f3e427091d6d",
    "raytrace": "88ef4d9060d8e8f6ce40f376477aaf89cc808fa44813225a3071a05a1467f017",
    "regex_dna": "d820dbdf12262cd11a543ae3dc3fd85793a20220d5a15ef687d8ef57a75c97c6",
    "regex_effbot": "0823b6507f8babea2238847562d9c9af31000ea57cbb695e5d47053321ea68c7",
    "regex_v8": "c22f820cb9a031a892ec0341eecca81c758dc25ee5413613d18eddfdff54a491",
    "richards": "a4512668525331960c54043b5150a3fff92badaeaba850a941893ac69a1028d8",
    "richards_super": "665b3d5551171e147c127b6f8671edc9a7703c736d317cc4a991bb00f599dc36",
    "scimark": "427b21b8a3802418ea3c2fe584335658a6c91c7f74fce4df9410efa60cd84d6e",
    "spectral_norm": "a3390ec6d75606fec30c4b59ad5f77d5292cd8e36f445197232a34560a880b18",
    "tomli_loads": "a94f7368f9656044f45244eb71da4f29a785c154c4a75aa15ca5c0e3c609c0d0",
    "unpack_sequence": "0dafe97531abc4a5baf30fe011db7acb3bf1e64cd4e41acb0c7db2bb141a8382",
}

# --census: the statements that stand in for each upstream main, calling what its pyperf
# runner would time with the default arguments.
CENSUS_CALLS = {
    "barnes_hut": "bench_quadtree_nbody(1, DEFAULT_PARTICLES, DEFAULT_ITERATIONS, DEFAULT_THETA)",
    "bpe_tokeniser": "bench_bpe_tokeniser(1)",
    "chaos": "main(None, None)",
    "comprehensions": "bench_comprehensions(1)",
    "coroutines": "bench_coroutines(1)",
    "crypto_pyaes": "bench_pyaes(1)",
    "deepcopy": "benchmark(1)\nbenchmark_reduce(1)\nbenchmark_memo(1)",
    "deltablue": "delta_blue(100)",
    "fannkuch": "fannkuch(DEFAULT_ARG)",
    "float": "benchmark(POINTS)",
    "generators": "bench_generators(1)",
    "go": "versus_cpu()",
    "hexiom": "main(1, DEFAULT_LEVEL)",
    "json_dumps": "bench_json_dumps([(obj, range(count)) for obj, count in [EMPTY, SIMPLE, NESTED, HUGE]])",
    "logging": ("stream = io.StringIO()\nhandler = logging.StreamHandler(stream=stream)\n"
                "logger = logging.getLogger('benchlogger')\nlogger.propagate = False\n"
                "logger.addHandler(handler)\nlogger.setLevel(logging.WARNING)\n"
                "for bench in sorted(BENCHMARKS):\n    BENCHMARKS[bench](1, logger, stream)"),
    "mdp": "bench_mdp(1)",
    "meteor_contest": ("board, cti, pieces = get_puzzle(WIDTH, HEIGHT)\n"
                       "bench_meteor_contest(1, board, pieces, SOLVE_ARG,\n"
                       "                     get_footprints(board, cti, pieces), get_senh(board, cti))"),
    "nbody": "bench_nbody(1, DEFAULT_REFERENCE, DEFAULT_ITERATIONS)",
    "nqueens": "bench_n_queens(8)",
    "pidigits": "calc_ndigits(DEFAULT_DIGITS)",
    "pprint": "p.pformat(printable)",
    "raytrace": "bench_raytrace(1, DEFAULT_WIDTH, DEFAULT_HEIGHT, None)",
    "regex_dna": "bench_regex_dna(1, init_benchmarks(DEFAULT_INIT_LEN, DEFAULT_RNG_SEED), None)",
    "regex_effbot": "bench_regex_effbot(1)",
    "regex_v8": "bench_regex_v8(1)",
    "richards": "Richards().run(1)",
    "richards_super": "Richards().run(1)",
    "scimark": "for bench in sorted(BENCHMARKS):\n    BENCHMARKS[bench][0](1, *BENCHMARKS[bench][1:])",
    "spectral_norm": "bench_spectral_norm(1)",
    "tomli_loads": "bench_tomli_loads(1)",
    "unpack_sequence": "bench_all(1)",
}

# What pyperf times in each ported benchmark, which --census reads from the upstream main: the
# function that runner.bench_func() calls, whose calls the port's main times in one loop; or the
# functions that time themselves for runner.bench_time_func(), each around one loop. The ports
# keep those timers in place with time.perf_counter(), which is pyperf.perf_counter(), and add
# their seconds to a list TIMED, whose sum the main prints.
TIMED_PART = {
    "barnes_hut": ["bench_quadtree_nbody"],
    "chaos": "create_image_chaos",
    "deltablue": "delta_blue",
    "fannkuch": "fannkuch",
    "float": "benchmark",
    "go": "versus_cpu",
    "hexiom": ["main"],
    "meteor_contest": ["bench_meteor_contest"],
    "nbody": ["bench_nbody"],
    "nqueens": "bench_n_queens",
    "raytrace": ["bench_raytrace"],
    "regex_dna": ["bench_regex_dna"],
    "regex_effbot": ["bench_regex_effbot"],
    "regex_v8": ["bench_regex_v8"],
    "richards": "run",
    "richards_super": "run",
    "scimark": ["SparseCompRow_matmult", "bench_FFT", "bench_LU", "bench_MonteCarlo", "bench_SOR"],
    "spectral_norm": ["bench_spectral_norm"],
    "unpack_sequence": ["do_unpacking"],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def census_source(text, call):
    """The upstream file without pyperf's import and main, calling its benchmark instead.

    Line numbers are kept up to the main, so the first error names the upstream line."""
    out = []
    for line in text.split("\n"):
        if re.match(r"if __name__ == ['\"]__main__['\"]:", line):
            break
        out.append("" if re.match(r"\s*(import pyperf|from pyperf import)", line) else line)
    body = "\n".join(out).rstrip().replace("pyperf.perf_counter()", "time.perf_counter()")
    return body + "\n\n\nimport time  # noqa: E402\n\nif __name__ == \"__main__\":\n" + \
        "".join("    " + line + "\n" for line in call.split("\n"))


def first_error(output):
    """The first line of a compiler's messages, without the chain of calls that reached it."""
    line = output.strip().split("\n")[0] if output.strip() else ""
    return re.sub(r" \(compiling .*\)$", "", line).replace(" (specializing ", " (")


def unmarked_hunks(upstream, port):
    """Hunks of the port's diff from upstream that no "Pystachy port" line explains.

    A note explains its own hunk and one that starts within three lines; the note of the
    main that replaces pyperf's runner explains every change after it."""
    old, new = upstream.split("\n"), port.split("\n")
    main = [i for i, line in enumerate(new) if "Pystachy port: a deterministic main replaces" in line]
    out = []
    for group in difflib.SequenceMatcher(None, old, new, autojunk=False).get_grouped_opcodes(1):
        changed = [(j1, j2) for tag, _, _, j1, j2 in group if tag != "equal"]
        lo, hi = changed[0][0], max(j2 for _, j2 in changed)
        if not any("Pystachy port" in line for line in new[max(0, lo - 3):hi + 1]) and not (main and lo > main[0]):
            out.append(f"{lo + 1}-{max(hi, lo + 1)}")
    return out


def called(node):
    """The names of the functions and methods that NODE calls."""
    return {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            for n in ast.walk(node) if isinstance(n, ast.Call)}


def timers(tree, clock):
    """{function: (timer statements, statements between the first and the last)} for each function
    whose body calls CLOCK.perf_counter()."""
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            marks = [i for i, s in enumerate(node.body) if f"{clock}.perf_counter()" in ast.unparse(s)]
            if marks:
                out[node.name] = (len(marks), node.body[marks[0] + 1:marks[-1]])
    return out


def upstream_timed_part(text):
    """TIMED_PART's entry for an upstream file, and what keeps its timers from fitting the rule."""
    tree = ast.parse(text)
    targets = {ast.unparse(n.args[1]).split(".")[-1] for n in ast.walk(tree) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "bench_func" and len(n.args) > 1}
    own = timers(tree, "pyperf")
    problems = [f"{name}(): its timer is not around one loop" for name, (count, between) in sorted(own.items())
                if count != 2 or len(between) != 1 or not isinstance(between[0], ast.For)]
    if targets and own or len(targets) > 1:
        problems.append("both bench_func() and its own timers, or several bench_func() targets")
    return (min(targets) if targets else sorted(own)), problems


def timing_errors(name, text):
    """How port NAME's printed seconds differ from what pyperf times (TIMED_PART); empty if not."""
    spec, tree, errors = TIMED_PART[name], ast.parse(text), []
    own = timers(tree, "time")
    value, region = None, None
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        for k, stmt in enumerate(body if isinstance(body, list) else []):
            if isinstance(stmt, ast.Expr) and ast.unparse(stmt).startswith("print('seconds', "):
                value = ast.unparse(stmt.value.args[1])
                starts = [i for i in range(k) if ast.unparse(body[i]) == "t0 = time.perf_counter()"]
                region = body[starts[-1] + 1:k] if starts else None
    if isinstance(spec, str):
        if own:
            errors.append(f"functions with their own timer: {', '.join(sorted(own))}")
        if value != "time.perf_counter() - t0" or region is None:
            errors.append("the main does not print the seconds since its t0 = time.perf_counter()")
        elif len(region) != 1 or not isinstance(region[0], ast.For) or len(region[0].body) != 1:
            errors.append("the main times more than one loop of one statement")
        elif spec not in called(region[0].body[0]):
            errors.append(f"the main's timed loop does not call {spec}()")
    else:
        if sorted(own) != sorted(spec):
            errors.append(f"functions with their own timer: {', '.join(sorted(own)) or 'none'}; "
                          f"expected {', '.join(spec)}")
        for function, (count, between) in sorted(own.items()):
            if count != 2 or len(between) != 1 or not isinstance(between[0], ast.For):
                errors.append(f"{function}(): the timer is not around one loop")
        if value != "sum(TIMED)" or region is not None:
            errors.append("the main does not print sum(TIMED), without a timer of its own")
        if "TIMED.append(" not in text:
            errors.append("no function adds its seconds to TIMED")
    return errors


def census(args, compiler, env):
    data = Path(args.census).read_bytes()
    if digest(data) != SDIST_SHA256:
        raise RuntimeError(f"{args.census}: SHA-256 {digest(data)}, expected {SDIST_SHA256}")
    rows = []
    with tarfile.open(args.census) as tar, tempfile.TemporaryDirectory(prefix="pyperformance-census-") as tmp:
        for name in sorted(UPSTREAM):
            text = tar.extractfile(SDIST_DIR + f"bm_{name}/run_benchmark.py").read()
            if digest(text) != UPSTREAM[name]:
                raise RuntimeError(f"bm_{name}/run_benchmark.py: SHA-256 {digest(text)}, expected {UPSTREAM[name]}")
            source = text.decode("utf-8")
            path = Path(tmp) / f"bm_{name}.py"
            path.write_text(census_source(source, CENSUS_CALLS[name]))
            # (from the root, as tests/run.sh runs a compiler: "python3 -m pystachy" works too)
            result = subprocess.run(compiler + ["ir", str(path), "-o", os.devnull], cwd=ROOT, env=env,
                                    capture_output=True, text=True, timeout=args.timeout)
            output = (result.stdout + result.stderr).replace(str(path.parent) + os.sep, "")
            row = {"name": name, "ported": name in BENCHMARKS,
                   "first_error": first_error(output) if result.returncode else "",
                   "returncode": result.returncode}
            if name in BENCHMARKS:
                port = (BENCH / f"{name}.py").read_text()
                row["unmarked_hunks"] = unmarked_hunks(source, port)
                spec, problems = upstream_timed_part(source)
                if spec != TIMED_PART[name]:
                    problems.append(f"pyperf times {spec}, not {TIMED_PART[name]} (TIMED_PART)")
                row["timing"] = problems + timing_errors(name, port)
            rows.append(row)
    print("| Benchmark | Status | First compiler error of the upstream file |")
    print("|---|---|---|")
    for row in rows:
        error = row["first_error"].replace("|", "\\|") or "none: compiles"
        print(f"| `{row['name']}` | {'ported' if row['ported'] else 'blocked'} | `{error}` |")
    failures = [f"{r['name']}: hunks without a 'Pystachy port' note at lines {', '.join(r['unmarked_hunks'])}"
                for r in rows if r.get("unmarked_hunks")]
    failures += [f"{r['name']}: {problem}" for r in rows for problem in r.get("timing", [])]
    for failure in failures:
        print(failure, file=sys.stderr)
    return {"sdist_sha256": SDIST_SHA256, "benchmarks": rows}, not failures


def seconds(stderr):
    """The timed part's seconds that a benchmark's main prints to stderr."""
    found = re.findall(r"^seconds (\S+)$", stderr, re.M)
    if len(found) != 1:
        raise ValueError(f"expected one 'seconds' line on stderr: {stderr[-500:]!r}")
    value = float(found[0])
    if not value >= 0:
        raise ValueError(f"invalid seconds: {found[0]}")
    return value


def run(command, env, timeout, expected=None):
    """Run a benchmark process: wall, CPU (user + system) and in-process seconds."""
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = execute(command, env, timeout)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    record["cpu_s"] = after.ru_utime - before.ru_utime + after.ru_stime - before.ru_stime
    record["loop_s"] = seconds(record["stderr"])
    if expected is not None and record["stdout"] != expected:
        raise ValueError(f"output differs from CPython's: {shlex.join(command)}\n"
                         f"expected: {expected[-500:]!r}\ngot: {record['stdout'][-500:]!r}")
    return record


def median(records, key):
    return statistics.median(r[key] for r in records)


def metadata(compiler, env, timeout):
    def info(command):
        try:
            return execute(command, env, timeout)["stdout"].strip()
        except (OSError, RuntimeError) as exc:
            return str(exc)
    return {
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_revision": info(["git", "rev-parse", "HEAD"]),
        "git_status": info(["git", "status", "--porcelain"]),
        "platform": platform.platform(), "machine": platform.machine(), "cpu_count": os.cpu_count(),
        "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        "host_python": sys.version, "compiler_command": compiler,
        "compiler_binary_sha256": digest(Path(compiler[0]).read_bytes()) if Path(compiler[0]).is_file() else None,
        "environment": {k: v for k, v in env.items() if k.startswith("PYSTACHY_") or k == "PYTHONHASHSEED"},
        "sources_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes())
                           for p in sorted(BENCH.glob("*.py")) + [Path(__file__).resolve()]},
    }


def measure(name, arguments, args, compiler, env, directory):
    source = str(BENCH / f"{name}.py")
    exe = str(directory / name)
    commands = {"cpython": [sys.executable, source] + arguments,
                "jit": compiler + ["run", source] + arguments,
                "aot": [exe] + arguments}
    oracle = run(commands["cpython"], env, args.timeout)
    build = execute(compiler + ["build", source, "-o", exe], env, args.timeout)
    # PYSTACHY_GC_STRESS_PROGRAM=N stresses the JIT's program; an executable reads
    # PYSTACHY_GC_STRESS, as tests/run.sh sets it
    stress = env.get("PYSTACHY_GC_STRESS_PROGRAM", "")
    envs = {"cpython": env, "jit": env, "aot": dict(env, PYSTACHY_GC_STRESS=stress) if stress else env}
    runs = {mode: [] for mode in commands}
    for repeat in range(args.runs):
        # rotate the order of the modes from one repetition to the next; never in parallel
        modes = ["cpython", "jit", "aot"]
        for mode in modes[repeat % 3:] + modes[:repeat % 3]:
            runs[mode].append(run(commands[mode], envs[mode], args.timeout, oracle["stdout"]))
    summary = {mode: {key: median(records, key) for key in ("wall_s", "cpu_s", "loop_s")}
               for mode, records in runs.items()}
    return {"name": name, "arguments": arguments, "output": oracle["stdout"],
            "aot_build_s": build["wall_s"], "summary": summary, "runs": runs}


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default=str(ROOT / "pystachy"), help="shell-split command, no shell evaluation")
    parser.add_argument("--benchmarks", nargs="+", choices=sorted(BENCHMARKS), default=sorted(BENCHMARKS))
    parser.add_argument("--runs", type=positive, default=5, help="processes per mode and benchmark")
    parser.add_argument("--smoke", action="store_true", help="small sizes, one run: correctness only")
    parser.add_argument("--census", metavar="SDIST", help="pyperformance-1.14.0.tar.gz: first errors of the upstream files")
    parser.add_argument("--timeout", type=float, default=300.0, help="seconds per command, including LLVM children")
    parser.add_argument("--json", type=Path, help="report (default build/pyperformance.json, or -smoke/-census)")
    args = parser.parse_args(argv)
    if not args.timeout > 0 or args.timeout == float("inf"):
        parser.error("timeout must be positive and finite")
    compiler = shlex.split(args.compiler)
    if not compiler:
        parser.error("empty compiler command")
    if "/" in compiler[0]:
        compiler[0] = str((ROOT / compiler[0]).resolve())
    if args.smoke:
        args.runs = 1
    suffix = "-census" if args.census else "-smoke" if args.smoke else ""
    args.json = args.json or ROOT / "build" / f"pyperformance{suffix}.json"
    env = dict(os.environ)
    env.setdefault("PYTHONHASHSEED", "0")
    if args.census:
        env["PYSTACHY_PATH"] = str(ROOT / "ports")  # (pyaes, for crypto_pyaes)
    report = {"schema_version": 1, "status": "running", "settings": {
        k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}}
    args.json.parent.mkdir(parents=True, exist_ok=True)
    try:
        report["metadata"] = metadata(compiler, env, args.timeout)
        if args.census:
            result, ok = census(args, compiler, env)
            report.update(result)
            report["status"] = "ok" if ok else "failed"
        else:
            report["benchmarks"] = []
            with tempfile.TemporaryDirectory(prefix="pyperformance-") as tmp:
                warm = Path(tmp) / "warm.py"
                warm.write_text("pass\n")
                # (the first run may build the runtime cache: it is not timed)
                execute(compiler + ["run", str(warm)], env, args.timeout)
                print("| Benchmark | Arguments | CPython | JIT | AOT | CPython/AOT | "
                      "CPython timed | JIT timed | AOT timed | AOT build |")
                print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
                for name in args.benchmarks:
                    arguments = BENCHMARKS[name][1 if args.smoke else 0]
                    report["active"] = name
                    result = measure(name, arguments, args, compiler, env, Path(tmp))
                    report["benchmarks"].append(result)
                    s = result["summary"]
                    cells = [s[m]["wall_s"] for m in ("cpython", "jit", "aot")]
                    ratio = cells[0] / cells[2] if cells[2] > 0 else 0.0
                    timed = [s[m]["loop_s"] for m in ("cpython", "jit", "aot")]
                    print(f"| `{name}` | {' '.join(arguments)} | " + " | ".join(f"{v:.3f}" for v in cells) +
                          f" | {ratio:.1f}x | " + " | ".join(f"{v:.4f}" for v in timed) +
                          f" | {result['aot_build_s']:.1f} |", flush=True)
                del report["active"]
            report["status"] = "ok"
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        report["status"], report["error"] = "failed", str(exc)
        print(f"pyperformance benchmark failed: {exc}", file=sys.stderr)
    finally:
        args.json.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Raw report: {args.json}", file=sys.stderr)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
