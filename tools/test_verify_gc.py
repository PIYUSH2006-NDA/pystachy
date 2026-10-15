"""Exercise the real GC verification shell with deterministic compiler/test doubles."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
TIMEOUT = shutil.which("timeout")


@unittest.skipUnless(TIMEOUT, "GNU timeout is required by verification")
class GCVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("tests", "tests/deviations", "tests/errors", "src", "lib", "ryu", "bin"):
            (self.root / name).mkdir()
        shutil.copy(ROOT / "tests/verify.sh", self.root / "tests/verify.sh")
        for name in ("pystachy.py", "runtime.py", "runtime.c", "tests/example.py",
                     "tests/syntax_example.py", "tests/deviations/example.py"):
            (self.root / name).write_text("# fixture\n")
        (self.root / "tests/errors/example.py").write_text("# error: mock rejection\n")
        (self.root / "tests/errors/syntax_example.py").write_text("# error: syntax_example.py: mock syntax\n")
        compiler = self.root / "bin/compiler"
        compiler.write_text(f"#!{sys.executable}\n" + '''import os
from pathlib import Path
import shutil
import signal
import sys
import time
args = sys.argv[1:]
if args == ["-"]:
    os.execv(sys.executable, [sys.executable, "-"])
if args == ["--version"]:
    print("mock compiler")
    sys.exit(0)
if args[0] == "pystachy.py":
    args = args[1:]
output = Path(args[args.index("-o") + 1])
if args[0] == "build":
    shutil.copy(__file__, output)
    output.chmod(0o755)
else:
    text = "fixed point\\n"
    if os.environ.get("PYSTACHY_GC_STRESS"):
        assert os.environ["PYSTACHY_GC_STRESS"] == "5000"
        assert os.environ["PYSTACHY_GC"] == "stats"
        Path("gc-child.pid").write_text(str(os.getpid()))
        mode = os.environ["VERIFY_MOCK_MODE"]
        if mode == "timeout-kill":
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if mode in ("timeout", "timeout-kill", "signal"):
            time.sleep(30)
        if mode == "failure":
            print("mock compiler failed", file=sys.stderr)
            sys.exit(7)
        if mode == "mismatch":
            text = "wrong IR\\n"
        print("gc statistics", file=sys.stderr)
    output.write_text(text)
''')
        compiler.chmod(0o755)
        suite = self.root / "tests/run.sh"
        suite.write_text('''#!/bin/sh
[ "$PYSTACHY_GC_STRESS" = 1000 ] || exit 9
[ "$PYSTACHY_GC_STRESS_PROGRAM" = 1 ] || exit 9
case "$2" in jit|aot) ;; *) echo "invalid mode: $2"; exit 9 ;; esac
echo "suite mode: $2"
# Three program/deviation executions, two rejections and two syntax checks per mode.
if [ "$VERIFY_MOCK_MODE" = "suite-$2-failure" ]; then
  echo '6 passed, 1 failed'
  exit 1
fi
if [ "$VERIFY_MOCK_MODE" = short-suite ]; then
  echo '6 passed, 0 failed'
  exit 0
fi
echo '7 passed, 0 failed'
''')
        suite.chmod(0o755)
        timeout = self.root / "bin/timeout"
        timeout.write_text(f"#!{sys.executable}\n" + f'''import os
import sys
assert sys.argv[1:4] == ["--verbose", "--kill-after=10s", "10m"]
limit = "0.2s" if os.environ["VERIFY_MOCK_MODE"].startswith("timeout") else "10s"
os.execv({TIMEOUT!r}, [{TIMEOUT!r}, "--verbose", "--kill-after=0.2s", limit, *sys.argv[4:]])
''')
        timeout.chmod(0o755)
        self.env = {**os.environ, "PY": str(compiler),
                    "PATH": str(self.root / "bin") + os.pathsep + os.environ["PATH"]}

    def run_group(self, group, mode="pass"):
        result = subprocess.run(["sh", "tests/verify.sh", group], cwd=self.root,
                                env={**self.env, "VERIFY_MOCK_MODE": mode},
                                text=True, capture_output=True, timeout=15)
        report = json.loads((self.root / "build/verification.json").read_text())
        logs = {step["name"]: (self.root / step["log"]).read_text() for step in report["steps"]}
        return result, report, logs

    def test_self_compile_preserves_ir_stress_and_gc_diagnostics(self):
        result, report, logs = self.run_group("gc-self")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["result"], "pass")
        self.assertEqual([step["name"] for step in report["steps"]], ["bootstrap", "gc-self"])
        step = report["steps"][-1]
        self.assertTrue(step["ir_identical"])
        self.assertEqual(step["compiler_interval"], 5000)
        self.assertNotIn("expected", step)
        for text in ("gc-self: started", "limit 10m", "gc-self: finished after", "gc statistics"):
            self.assertIn(text, logs["gc-self"])

    def test_each_suite_runs_all_checks_in_its_mode_at_original_stress(self):
        for mode in ("jit", "aot"):
            group = f"gc-{mode}"
            with self.subTest(group=group):
                result, report, logs = self.run_group(group)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(report["result"], "pass")
                self.assertEqual([step["name"] for step in report["steps"]], ["bootstrap", group])
                step = report["steps"][-1]
                self.assertEqual((step["passed"], step["failed"], step["expected"]), (7, 0, 7))
                self.assertEqual(step["modes"], [mode])
                self.assertEqual((step["tests_compiler_interval"], step["tests_interval"]), (1000, 1))
                self.assertIn(f"suite mode: {mode}", logs[group])
                self.assertFalse((self.root / "gc-child.pid").exists())

    def test_local_gc_stress_alias_runs_self_and_both_modes(self):
        result, report, logs = self.run_group("gc-stress")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["result"], "pass")
        self.assertEqual([step["name"] for step in report["steps"]],
                         ["bootstrap", "gc-self", "gc-jit", "gc-aot"])
        self.assertIn("gc statistics", logs["gc-self"])
        for mode in ("jit", "aot"):
            step = next(step for step in report["steps"] if step["name"] == f"gc-{mode}")
            self.assertEqual((step["passed"], step["expected"]), (7, 7))
            self.assertEqual(step["modes"], [mode])
            self.assertIn(f"suite mode: {mode}", logs[f"gc-{mode}"])

    def test_failure_timeout_and_mismatched_ir_cannot_pass(self):
        for mode, text in (("failure", "mock compiler failed"),
                           ("timeout", "sending signal TERM"),
                           ("timeout-kill", "sending signal KILL"),
                           ("mismatch", "differ")):
            with self.subTest(mode=mode):
                result, report, logs = self.run_group("gc-self", mode)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(report["result"], "fail")
                self.assertEqual(report["steps"][-1]["result"], "fail")
                self.assertIn(text, logs["gc-self"])

    def test_failed_and_incomplete_suites_cannot_pass(self):
        for mode in ("jit", "aot"):
            for failure in (f"suite-{mode}-failure", "short-suite"):
                with self.subTest(mode=mode, failure=failure):
                    result, report, _ = self.run_group(f"gc-{mode}", failure)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(report["result"], "fail")
                    self.assertEqual(report["steps"][-1]["result"], "fail")

    def test_local_alias_reports_failure_and_still_runs_remaining_modes(self):
        for failure in ("failure", "suite-jit-failure", "suite-aot-failure"):
            with self.subTest(failure=failure):
                result, report, logs = self.run_group("gc-stress", failure)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(report["result"], "fail")
                self.assertEqual([step["name"] for step in report["steps"]],
                                 ["bootstrap", "gc-self", "gc-jit", "gc-aot"])
                self.assertIn("suite mode: jit", logs["gc-jit"])
                self.assertIn("suite mode: aot", logs["gc-aot"])

    def test_cancellation_terminates_the_background_compiler(self):
        process = subprocess.Popen(["sh", "tests/verify.sh", "gc-self"], cwd=self.root,
                                   env={**self.env, "VERIFY_MOCK_MODE": "signal"},
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   start_new_session=True)
        try:
            deadline = time.monotonic() + 5
            pidfile = self.root / "gc-child.pid"
            while not pidfile.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(pidfile.exists())
            child = int(pidfile.read_text())
            process.terminate()
            process.communicate(timeout=5)
            self.assertEqual(process.returncode, 130)
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()


if __name__ == "__main__":
    unittest.main()
