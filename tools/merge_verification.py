#!/usr/bin/env python3
"""Fail closed when assembling the parallel CI jobs' verification reports."""
import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SUITE_STEPS = {"tests-cpython", "tests-native", "tests-opt-off", "runtime-cache",
               "python-free", "ubsan", "gc-jit", "gc-aot"}


def parse_groups(text):
    """Read the harness's public contract, checking that no check is omitted or repeated."""
    groups = {}
    for line in text.splitlines():
        words = line.split()
        if not words:
            continue
        name, *steps = words
        if name in groups:
            raise ValueError(f"duplicate group in --list: {name}")
        if not steps or steps[0] != "bootstrap" or len(set(steps)) != len(steps):
            raise ValueError(f"invalid step list for {name}: bootstrap must come first, once")
        groups[name] = steps
    if not groups or next(iter(groups)) != "all" or len(groups) < 2:
        raise ValueError("--list must begin with all, followed by the CI groups")
    covered = Counter(step for name, steps in groups.items() if name != "all"
                      for step in steps if step != "bootstrap")
    if covered != Counter(groups["all"][1:]):
        raise ValueError("CI groups must cover every all step exactly once, except bootstrap")
    return groups


def load_groups():
    result = subprocess.run([str(ROOT / "tests/verify.sh"), "--list"], cwd=ROOT,
                            check=True, capture_output=True, text=True, timeout=10)
    return parse_groups(result.stdout)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f"invalid JSON number: {value}")


def number(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label}: expected a finite, nonnegative duration")
    return value


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label}: expected an integer >= {minimum}")
    return value


def validate_report(report, group, expected):
    if not isinstance(report, dict) or report.get("project") != "Pystachy":
        raise ValueError(f"{group}: not a Pystachy verification report")
    if report.get("result") != "pass":
        raise ValueError(f"{group}: verification did not pass")
    summary, steps = report.get("summary"), report.get("steps")
    if not isinstance(summary, dict) or not isinstance(steps, list):
        raise ValueError(f"{group}: missing summary or steps")
    names = [step.get("name") if isinstance(step, dict) else None for step in steps]
    if names != expected:
        raise ValueError(f"{group}: step names/order differ: expected {expected}, got {names}")
    for key, value in (("steps", len(expected)), ("passed", len(expected)), ("failed", 0)):
        if integer(summary.get(key), f"{group}.summary.{key}") != value:
            raise ValueError(f"{group}: summary {key} must be {value}")
    number(summary.get("seconds"), f"{group}.summary.seconds")
    for step in steps:
        label = f"{group}.{step['name']}"
        if step.get("result") != "pass":
            raise ValueError(f"{label}: step did not pass")
        number(step.get("seconds"), f"{label}.seconds")
        if "failed" in step and integer(step["failed"], f"{label}.failed") != 0:
            raise ValueError(f"{label}: failed checks")
        if "failures" in step and step["failures"] != []:
            raise ValueError(f"{label}: nonempty failures")
        if step["name"] == "gc-self":
            if (step.get("ir_identical") is not True or
                    integer(step.get("compiler_interval"), f"{label}.compiler_interval", 1) != 5000):
                raise ValueError(f"{label}: missing GC-stressed IR identity or wrong interval")
        if step["name"] in {"gc-jit", "gc-aot"}:
            if (step.get("modes") != [step["name"][3:]] or
                    integer(step.get("tests_compiler_interval"), f"{label}.tests_compiler_interval", 1) != 1000 or
                    integer(step.get("tests_interval"), f"{label}.tests_interval", 1) != 1):
                raise ValueError(f"{label}: wrong GC stress mode or intervals")
        if step["name"] in SUITE_STEPS:
            expected_checks = integer(step.get("expected"), f"{label}.expected", 1)
            if integer(step.get("passed"), f"{label}.passed") != expected_checks:
                raise ValueError(f"{label}: check coverage differs from expected")
            if integer(step.get("failed"), f"{label}.failed") != 0:
                raise ValueError(f"{label}: failed checks")
    bootstrap = steps[0]
    if bootstrap.get("ir_identical") is not True or not re.fullmatch(
            r"[0-9a-f]{64}", str(bootstrap.get("ir_sha256", ""))):
        raise ValueError(f"{group}: missing successful bootstrap IR identity")
    for key in ("git", "sources", "toolchain"):
        if not isinstance(report.get(key), dict) or not report[key]:
            raise ValueError(f"{group}: missing {key} identity")
    if not re.fullmatch(r"[0-9a-f]{40}", str(report["git"].get("commit", ""))):
        raise ValueError(f"{group}: invalid git commit")


def merge_reports(directory, groups, expected_commit=None):
    reports, paths = {}, {}
    for path in sorted(directory.rglob("verification.json")):
        report = json.loads(path.read_text(), object_pairs_hook=unique_object,
                            parse_constant=invalid_constant)
        group = report.get("group") if isinstance(report, dict) else None
        if not isinstance(group, str) or group == "all" or group not in groups:
            raise ValueError(f"{path}: unexpected group {group!r}")
        if group in reports:
            raise ValueError(f"duplicate report group: {group}")
        if path != directory / f"verification-{group}" / "verification.json":
            raise ValueError(f"{group}: unexpected report path {path}")
        validate_report(report, group, groups[group])
        reports[group], paths[group] = report, path
    wanted = [name for name in groups if name != "all"]
    if set(reports) != set(wanted):
        raise ValueError(f"missing report groups: {sorted(set(wanted) - set(reports))}")
    first = reports[wanted[0]]
    commit = first["git"]["commit"]
    if expected_commit is not None and commit != expected_commit:
        raise ValueError(f"report commit {commit} differs from checkout {expected_commit}")
    identity = {"git.commit": commit, "sources": first["sources"], "toolchain": first["toolchain"]}
    steps, timings = {}, []
    for group in wanted:
        report = reports[group]
        current = {"git.commit": report["git"]["commit"], "sources": report["sources"],
                   "toolchain": report["toolchain"]}
        for key, value in identity.items():
            if json.dumps(current[key], sort_keys=True) != json.dumps(value, sort_keys=True):
                raise ValueError(f"{group}: {key} identity differs between groups")
        if report["steps"][0]["ir_sha256"] != first["steps"][0]["ir_sha256"]:
            raise ValueError(f"{group}: bootstrap IR hash differs between groups")
        for step in report["steps"]:
            if step["name"] in steps:
                continue  # Only bootstrap is repeated: the --list contract checked this.
            step = copy.deepcopy(step)
            step["ci_group"] = group
            if isinstance(step.get("log"), str) and step["log"].startswith("build/"):
                step["log"] = str(paths[group].parent / step["log"][len("build/"):])
            steps[step["name"]] = step
        timings.append({"group": group, "seconds": report["summary"]["seconds"],
                        "steps": report["summary"]["steps"], "report": str(paths[group]),
                        "platform": report.get("platform", {})})
    result = copy.deepcopy(first)
    result["group"] = "all"
    result["steps"] = [steps[name] for name in groups["all"]]
    maximum = round(max(timing["seconds"] for timing in timings), 3)
    result["summary"] = {"steps": len(result["steps"]), "passed": len(result["steps"]),
                         "failed": 0, "seconds": maximum}
    result["timestamp_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result["ci"] = {"groups": timings, "max_group_seconds": maximum,
                    "runner_seconds": round(sum(timing["seconds"] for timing in timings), 3),
                    "timing_scope": "verification only; excludes queue, setup and artifact transfer"}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="downloaded verification artifacts")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        groups = load_groups()
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                capture_output=True, text=True, timeout=10).stdout.strip()
        result = merge_reports(args.directory, groups, commit)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {"project": "Pystachy", "group": "all", "result": "fail", "error": str(exc),
                  "summary": {"steps": 0, "passed": 0, "failed": 1, "seconds": 0}, "steps": []}
        print(f"verification merge: {exc}", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if result["result"] != "pass":
        return 1
    print(f"verification: {len(result['steps'])} checks passed across {len(result['ci']['groups'])} groups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
