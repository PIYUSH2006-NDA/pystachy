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

CONTRACT = """all bootstrap tests-native check-ir
native bootstrap tests-native
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
        if name in ("gc-aot-0", "gc-aot-1", "tests-cpython-0", "tests-cpython-1"):
            step.update(passed=5, expected=5)   # halves of a 10-check suite
        if name == "gc-self":
            step.update(compiler_interval=5000, ir_identical=True)
        if name in ("gc-jit", "gc-aot-0", "gc-aot-1"):
            step.update(tests_compiler_interval=1000, tests_interval=1,
                        modes=["jit" if name == "gc-jit" else "aot"])
        if name in merge.SHARDED_STEPS:
            step.update(shard_index=int(name[-1]), shard_count=2)
        checks.append(step)
    return {"project": "Pystachy", "group": group, "result": "pass",
            "summary": {"steps": len(steps), "passed": len(steps), "failed": 0, "seconds": 6.0},
            "git": {"commit": COMMIT, "dirty": False},
            "sources": {"pystachy.py": {"sha256": "c" * 64}, "test_programs": 5},
            "toolchain": {"llvm": "LLVM 18", "python": "Python 3.13"},
            "platform": {"machine": "x86_64"}, "steps": checks}


class ContractTests(unittest.TestCase):
    def test_real_plan_requires_native_suites_and_every_gc_job(self):
        groups = merge.load_groups()
        self.assertEqual(groups["native"], ["bootstrap", "tests-native"])
        self.assertEqual(groups["opt-off"], ["bootstrap", "tests-opt-off"])
        for alias in ("gc-stress", "gc-aot", "hosted", "ubsan"):
            self.assertNotIn(alias, groups)  # Compatibility aliases must not duplicate CI work.
        for group in ("gc-self", "gc-jit", "gc-aot-0", "gc-aot-1", "ubsan-0", "ubsan-1"):
            self.assertEqual(groups[group], ["bootstrap", group])
        for shard in ("0", "1"):
            self.assertEqual(groups["hosted-" + shard], ["bootstrap", "tests-cpython-" + shard])
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for group, steps in groups.items():
                if group == "all":
                    continue
                path = directory / f"verification-{group}" / "verification.json"
                path.parent.mkdir()
                path.write_text(json.dumps(report(group, steps)))
            result = merge.merge_reports(directory, groups, COMMIT)
            self.assertEqual([step["name"] for step in result["steps"]], groups["all"])
            for group in ("opt-off", "gc-self", "gc-jit", "gc-aot-0", "gc-aot-1", "hosted-0", "hosted-1",
                          "ubsan-0", "ubsan-1"):
                path = directory / f"verification-{group}" / "verification.json"
                original = path.read_text()
                path.unlink()
                with self.subTest(missing=group), self.assertRaisesRegex(ValueError, f"missing report groups.*{group}"):
                    merge.merge_reports(directory, groups, COMMIT)
                path.write_text(original)
            for group in ("gc-aot-0", "hosted-1", "ubsan-0"):
                path = directory / f"verification-{group}" / "verification.json"
                original = path.read_text()
                for delta in (-1, 1):
                    data = report(group, groups[group])
                    count = data["steps"][-1]["expected"] + delta
                    data["steps"][-1].update(passed=count, expected=count)
                    path.write_text(json.dumps(data))
                    with self.subTest(group=group, delta=delta), \
                            self.assertRaisesRegex(ValueError, "same full-suite check count"):
                        merge.merge_reports(directory, groups, COMMIT)
                path.write_text(original)

    def test_gc_reports_require_original_stress_mode_ir_and_complete_counts(self):
        groups = merge.load_groups()
        mutations = {
            "gc-self": [lambda step: step.update(compiler_interval=5001),
                        lambda step: step.pop("compiler_interval"),
                        lambda step: step.update(ir_identical=False),
                        lambda step: step.pop("ir_identical")],
            "gc-jit": [lambda step: step.update(tests_compiler_interval=1001),
                       lambda step: step.update(tests_interval=2),
                       lambda step: step.pop("tests_interval"),
                       lambda step: step.update(modes=["aot"]),
                       lambda step: step.update(modes=["jit", "aot"]),
                       lambda step: step.pop("modes"),
                       lambda step: step.update(passed=9),
                       lambda step: step.pop("expected")],
        }
        shard_mutations = [lambda step: step.update(shard_index=1 - step["shard_index"]),
                           lambda step: step.update(shard_index=False),
                           lambda step: step.pop("shard_index"),
                           lambda step: step.update(shard_count=3),
                           lambda step: step.update(shard_count="2"),
                           lambda step: step.pop("shard_count")]
        for group in ("hosted-0", "hosted-1", "ubsan-0", "ubsan-1"):
            mutations[group] = shard_mutations + [lambda step: step.update(passed=step["expected"] - 1),
                                                  lambda step: step.update(failed=1),
                                                  lambda step: step.pop("expected")]
        for group in ("gc-aot-0", "gc-aot-1"):
            mutations[group] = [lambda step: step.update(tests_compiler_interval=1001),
                                lambda step: step.update(tests_interval=2),
                                lambda step: step.pop("tests_compiler_interval"),
                                lambda step: step.update(modes=["jit"]),
                                lambda step: step.update(modes=[]),
                                lambda step: step.update(failed=1),
                                lambda step: step.pop("passed"),
                                lambda step: step.update(shard_index=1 - step["shard_index"]),
                                lambda step: step.update(shard_index=False),
                                lambda step: step.pop("shard_index"),
                                lambda step: step.update(shard_count=3),
                                lambda step: step.update(shard_count="2"),
                                lambda step: step.pop("shard_count")]
        for group, changes in mutations.items():
            valid = report(group, groups[group])
            merge.validate_report(valid, group, groups[group])
            for index, mutate in enumerate(changes):
                data = copy.deepcopy(valid)
                mutate(data["steps"][-1])
                with self.subTest(group=group, mutation=index), self.assertRaises(ValueError):
                    merge.validate_report(data, group, groups[group])

    def test_missing_duplicate_or_unknown_checks_cannot_weaken_the_gate(self):
        contracts = [CONTRACT.replace("contracts bootstrap check-ir", "contracts bootstrap"),
                     CONTRACT + "extra bootstrap check-ir\n",
                     CONTRACT.replace("contracts bootstrap check-ir", "contracts bootstrap unknown"),
                     CONTRACT + "native bootstrap tests-native\n",
                     CONTRACT.replace("native bootstrap", "native tests-native"),
                     CONTRACT.replace("all bootstrap tests-native", "all bootstrap bootstrap tests-native")]
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
        self.assertEqual(merged["git"], self.reports["native"]["git"])
        self.assertEqual(merged["sources"], self.reports["native"]["sources"])
        self.assertEqual(merged["steps"][0]["ci_group"], "native")
        self.assertTrue(merged["steps"][2]["log"].endswith("verification-contracts/verify/check-ir.log"))

    def test_missing_group_cannot_report_success(self):
        (self.directory / "verification-contracts/verification.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing report groups"):
            self.merged()

    def test_failed_skipped_missing_reordered_and_unexpected_steps_are_rejected(self):
        original = copy.deepcopy(self.reports["native"])
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
            self.reports["native"] = copy.deepcopy(original)
            mutation(self.reports["native"])
            self.write_reports()
            with self.subTest(report=self.reports["native"]), self.assertRaises(ValueError):
                self.merged()

    def test_unexpected_and_duplicate_groups_are_rejected(self):
        self.reports["unknown"] = report("unknown", ["bootstrap", "check-ir"])
        self.write_reports()
        with self.assertRaisesRegex(ValueError, "unexpected group"):
            self.merged()
        (self.directory / "verification-unknown/verification.json").unlink()
        duplicate = self.directory / "verification-native-copy"
        duplicate.mkdir()
        (duplicate / "verification.json").write_text(json.dumps(self.reports["native"]))
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
