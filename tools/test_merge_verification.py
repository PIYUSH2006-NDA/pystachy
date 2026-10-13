"""The final CI gate must reject incomplete or inconsistent verification artifacts."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import merge_verification as merge

CONTRACT = """all bootstrap tests-cpython check-ir
hosted bootstrap tests-cpython
contracts bootstrap check-ir
"""
COMMIT = "a" * 40


def report(group, steps):
    checks = []
    for name in steps:
        step = {"name": name, "result": "pass", "seconds": 2.0,
                "log": f"build/verify/{name}.log"}
        if name == "bootstrap":
            step.update(ir_identical=True, ir_sha256="b" * 64)
        if name in merge.SUITE_STEPS:
            step.update(passed=10, failed=0, expected=10, failures=[])
        checks.append(step)
    return {"project": "Pystachy", "group": group, "result": "pass",
            "summary": {"steps": len(steps), "passed": len(steps), "failed": 0, "seconds": 6.0},
            "git": {"commit": COMMIT, "dirty": False},
            "sources": {"pystachy.py": {"sha256": "c" * 64}, "test_programs": 5},
            "toolchain": {"llvm": "LLVM 18", "python": "Python 3.13"},
            "platform": {"machine": "x86_64"}, "steps": checks}


class ContractTests(unittest.TestCase):
    def test_missing_duplicate_or_unknown_checks_cannot_weaken_the_gate(self):
        contracts = [CONTRACT.replace("contracts bootstrap check-ir", "contracts bootstrap"),
                     CONTRACT + "extra bootstrap check-ir\n",
                     CONTRACT.replace("contracts bootstrap check-ir", "contracts bootstrap unknown"),
                     CONTRACT + "hosted bootstrap tests-cpython\n",
                     CONTRACT.replace("hosted bootstrap", "hosted tests-cpython"),
                     CONTRACT.replace("all bootstrap tests-cpython", "all bootstrap bootstrap tests-cpython")]
        for contract in contracts:
            with self.subTest(contract=contract), self.assertRaises(ValueError):
                merge.parse_groups(contract)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.groups = merge.parse_groups(CONTRACT)
        self.reports = {group: report(group, steps) for group, steps in self.groups.items() if group != "all"}
        self.write_reports()

    def write_reports(self):
        for group, data in self.reports.items():
            path = self.directory / f"verification-{group}" / "verification.json"
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(data))

    def merged(self):
        return merge.merge_reports(self.directory, self.groups, COMMIT)

    def test_valid_reports_preserve_checks_and_distinguish_parallel_from_runner_time(self):
        self.reports["contracts"]["summary"]["seconds"] = 9.0
        self.write_reports()
        merged = self.merged()
        self.assertEqual([step["name"] for step in merged["steps"]], self.groups["all"])
        self.assertEqual(merged["result"], "pass")
        self.assertEqual(merged["summary"], {"steps": 3, "passed": 3, "failed": 0, "seconds": 9.0})
        self.assertEqual(merged["ci"]["runner_seconds"], 15.0)
        self.assertEqual(merged["ci"]["max_group_seconds"], 9.0)
        self.assertEqual(merged["git"], self.reports["hosted"]["git"])
        self.assertEqual(merged["sources"], self.reports["hosted"]["sources"])
        self.assertEqual(merged["steps"][0]["ci_group"], "hosted")
        self.assertTrue(merged["steps"][2]["log"].endswith("verification-contracts/verify/check-ir.log"))

    def test_missing_group_cannot_report_success(self):
        (self.directory / "verification-contracts/verification.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing report groups"):
            self.merged()

    def test_failed_skipped_missing_reordered_and_unexpected_steps_are_rejected(self):
        original = copy.deepcopy(self.reports["hosted"])
        mutations = [lambda data: data.update(result="fail"),
                     lambda data: data["steps"][1].update(result="skip"),
                     lambda data: data["steps"].pop(),
                     lambda data: data["steps"].reverse(),
                     lambda data: data["steps"].append({"name": "extra", "result": "pass", "seconds": 0}),
                     lambda data: data["summary"].update(failed=1),
                     lambda data: data["summary"].update(passed=1),
                     lambda data: data["steps"][1].update(passed=9),
                     lambda data: data["steps"][1].update(failed=1),
                     lambda data: data["steps"][1].update(failures=["lost case"]),
                     lambda data: data["steps"][1].update(seconds=float("nan"))]
        for mutation in mutations:
            self.reports["hosted"] = copy.deepcopy(original)
            mutation(self.reports["hosted"])
            self.write_reports()
            with self.subTest(report=self.reports["hosted"]), self.assertRaises(ValueError):
                self.merged()

    def test_unexpected_and_duplicate_groups_are_rejected(self):
        self.reports["unknown"] = report("unknown", ["bootstrap", "check-ir"])
        self.write_reports()
        with self.assertRaisesRegex(ValueError, "unexpected group"):
            self.merged()
        (self.directory / "verification-unknown/verification.json").unlink()
        duplicate = self.directory / "verification-hosted-copy"
        duplicate.mkdir()
        (duplicate / "verification.json").write_text(json.dumps(self.reports["hosted"]))
        with self.assertRaisesRegex(ValueError, "duplicate report group"):
            self.merged()

    def test_commit_source_toolchain_and_bootstrap_drift_are_rejected(self):
        original = copy.deepcopy(self.reports["contracts"])
        changes = [("git", "commit", "d" * 40), ("sources", "test_programs", 4),
                   ("toolchain", "llvm", "LLVM 19")]
        for field, key, value in changes:
            self.reports["contracts"] = copy.deepcopy(original)
            self.reports["contracts"][field][key] = value
            self.write_reports()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "identity differs"):
                self.merged()
        self.reports["contracts"] = copy.deepcopy(original)
        self.reports["contracts"]["steps"][0]["ir_sha256"] = "e" * 64
        self.write_reports()
        with self.assertRaisesRegex(ValueError, "bootstrap IR hash differs"):
            self.merged()

    def test_all_reports_from_a_previous_commit_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "differs from checkout"):
            merge.merge_reports(self.directory, self.groups, "f" * 40)

    def test_failed_cli_overwrites_a_stale_success_report_and_exits_nonzero(self):
        output = self.directory / "combined.json"
        output.write_text('{"result": "pass"}')
        (self.directory / "verification-contracts/verification.json").unlink()
        with mock.patch.object(merge, "load_groups", return_value=self.groups), \
                mock.patch.object(merge.subprocess, "run", return_value=mock.Mock(stdout=COMMIT)), \
                contextlib.redirect_stderr(io.StringIO()):
            status = merge.main([str(self.directory), "-o", str(output)])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(output.read_text())["result"], "fail")


if __name__ == "__main__":
    unittest.main()
