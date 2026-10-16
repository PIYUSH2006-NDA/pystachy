"""Checks of the pyperformance controller and of the ports' records; LLVM is not required."""
import contextlib
import io
import os
import re
import subprocess
import sys
import unittest
from unittest import mock

import bench_pyperformance as bench


class CensusTests(unittest.TestCase):
    UPSTREAM = ("import math\n\nimport pyperf\n\n\ndef bench_x(loops):\n    t0 = pyperf.perf_counter()\n"
                "    return pyperf.perf_counter() - t0\n\n\nif __name__ == \"__main__\":\n"
                "    runner = pyperf.Runner()\n    runner.bench_time_func('x', bench_x)\n")

    def test_runner_is_replaced_by_the_call_and_lines_are_kept(self):
        source = bench.census_source(self.UPSTREAM, "a = 1\nbench_x(a)")
        lines = source.split("\n")
        self.assertNotIn("pyperf", source.replace("time.perf_counter", ""))
        self.assertEqual(lines[5], "def bench_x(loops):")  # (line 6, as upstream)
        self.assertEqual(lines[6], "    t0 = time.perf_counter()")
        self.assertTrue(source.endswith("if __name__ == \"__main__\":\n    a = 1\n    bench_x(a)\n"))
        compile(source, "bm_x.py", "exec")

    def test_first_error_drops_the_chain_of_calls(self):
        output = ("bm_x.py:7: error: expected int, got float (compiling f(int) for the call at bm_x.py:9; "
                  "compiling g() for the call at bm_x.py:12)\nmore\n")
        self.assertEqual(bench.first_error(output), "bm_x.py:7: error: expected int, got float")
        self.assertEqual(bench.first_error(""), "")

    def test_every_changed_hunk_needs_a_note(self):
        upstream = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\ng = 7\nh = 8\n"
        marked = upstream.replace("b = 2", "b = 2.0  # Pystachy port: a float")
        self.assertEqual(bench.unmarked_hunks(upstream, marked), [])
        unmarked = marked.replace("g = 7", "g = 7.0")
        self.assertEqual(bench.unmarked_hunks(upstream, unmarked), ["7-7"])
        main = unmarked.replace("e = 5", "# Pystachy port: a deterministic main replaces pyperf.Runner")
        self.assertEqual(bench.unmarked_hunks(upstream, main), [])


class TimingTests(unittest.TestCase):
    """The seconds a port prints are for what pyperf would time (TIMED_PART)."""

    def port(self, name):
        return (bench.BENCH / f"{name}.py").read_text()

    def test_every_port_times_what_pyperf_times(self):
        self.assertEqual(set(bench.TIMED_PART), set(bench.BENCHMARKS))
        for name in sorted(bench.BENCHMARKS):
            with self.subTest(name=name):
                self.assertEqual(bench.timing_errors(name, self.port(name)), [])

    def test_work_inside_a_functions_timer_is_reported(self):
        # regex_v8's checksum belongs after the timed loops, as upstream times only the blocks
        text = self.port("regex_v8")
        stop = "    TIMED.append(time.perf_counter() - t0)  # Pystachy port: the seconds, which upstream returns\n"
        self.assertIn(stop, text)
        moved = text.replace(stop, "").replace("    return total\n", stop + "    return total\n")
        self.assertEqual(bench.timing_errors("regex_v8", moved), ["bench_regex_v8(): the timer is not around one loop"])
        self.assertIn("the main does not print sum(TIMED), without a timer of its own",
                      bench.timing_errors("regex_v8", text.replace("sum(TIMED)", "time.perf_counter() - t0")))

    def test_setup_inside_the_mains_timer_is_reported(self):
        # chaos builds its game once, outside the timed loop, as upstream's runner does
        text = self.port("chaos")
        setup = "    chaos = main()\n    t0 = time.perf_counter()\n"
        self.assertIn(setup, text)
        timed = text.replace(setup, "    t0 = time.perf_counter()\n    chaos = main()\n")
        self.assertEqual(bench.timing_errors("chaos", timed), ["the main times more than one loop of one statement"])
        other = text.replace("im = chaos.create_image_chaos(", "im = chaos.create_image(")
        self.assertEqual(bench.timing_errors("chaos", other), ["the main's timed loop does not call create_image_chaos()"])

    def test_upstream_timed_part(self):
        time_func = CensusTests.UPSTREAM.replace("    return pyperf", "    for _ in range(loops):\n        pass\n"
                                                 "    return pyperf")
        self.assertEqual(bench.upstream_timed_part(time_func), (["bench_x"], []))
        self.assertEqual(bench.upstream_timed_part(CensusTests.UPSTREAM),
                         (["bench_x"], ["bench_x(): its timer is not around one loop"]))
        func = "import pyperf\n\n\ndef f(n):\n    return n\n\n\nrunner = pyperf.Runner()\nrunner.bench_func('f', game.f, 1)\n"
        self.assertEqual(bench.upstream_timed_part(func), ("f", []))

    def test_unpack_sequence_runs_upstreams_default_both_variants(self):
        # bench_all(): 400 unpackings of a tuple and of a list of 0..9 per loop
        result = subprocess.run([sys.executable, str(bench.BENCH / "unpack_sequence.py"), "1"],
                                capture_output=True, text=True, check=True, timeout=60)
        self.assertEqual(result.stdout, "unpack_sequence 1 90\n")
        self.assertGreaterEqual(bench.seconds(result.stderr), 0)


class OutputTests(unittest.TestCase):
    def test_one_nonnegative_seconds_line_is_required(self):
        self.assertEqual(bench.seconds("warning\nseconds 0.25\n"), 0.25)
        for stderr in ("", "seconds 1\nseconds 2\n", "seconds -1\n", "seconds nan\n", "seconds x\n"):
            with self.subTest(stderr=stderr), self.assertRaises(ValueError):
                bench.seconds(stderr)

    def test_output_must_be_cpythons(self):
        code = "import sys; print('result 1'); print('seconds 0.5', file=sys.stderr)"
        command = [sys.executable, "-c", code]
        record = bench.run(command, dict(os.environ), 30, "result 1\n")
        self.assertEqual(record["loop_s"], 0.5)
        self.assertGreaterEqual(record["cpu_s"], 0)
        with self.assertRaisesRegex(ValueError, "differs"):
            bench.run(command, dict(os.environ), 30, "result 2\n")


class RecordTests(unittest.TestCase):
    def test_ports_tables_and_files_agree(self):
        files = sorted(p.stem for p in bench.BENCH.glob("*.py"))
        self.assertEqual(files, sorted(bench.BENCHMARKS))
        self.assertLessEqual(set(bench.BENCHMARKS), set(bench.UPSTREAM))
        self.assertEqual(set(bench.CENSUS_CALLS), set(bench.UPSTREAM))
        for name in files:
            text = (bench.BENCH / f"{name}.py").read_text()
            self.assertIn("Pystachy port: a deterministic main replaces pyperf.Runner", text, name)
            self.assertNotIn("import pyperf", text, name)

    def test_readme_records_every_upstream_hash(self):
        readme = (bench.BENCH / "README.md").read_text()
        self.assertIn(bench.SDIST_SHA256, readme)
        for name, sha in bench.UPSTREAM.items():
            row = re.search(rf"^\| `{name}` \|.*$", readme, re.M)
            self.assertIsNotNone(row, name)
            self.assertIn(sha, row.group(0), name)
            self.assertIn("ported" if name in bench.BENCHMARKS else "blocked", row.group(0), name)


class ArgumentTests(unittest.TestCase):
    def test_invalid_settings_fail_before_execution(self):
        for arguments in (["--runs", "0"], ["--timeout", "inf"], ["--timeout", "-1"], ["--compiler", ""],
                          ["--benchmarks", "pidigits"]):
            with self.subTest(arguments=arguments), mock.patch.object(bench, "execute") as execute:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    bench.main(arguments)
                self.assertEqual(caught.exception.code, 2)
                execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
