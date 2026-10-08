#!/usr/bin/env python3
"""Run deterministic gates and bind their raw results to the tested repository snapshot."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from .change_contracts import current_change_contract
except ImportError:
    from change_contracts import current_change_contract

ROOT = Path(__file__).resolve().parents[1]
JUNIT = Path("build/robotics_sim/test_results/robotics_sim/pytest.xml")
DESIGN = Path("examples/warehouse-tote/design-package.json")
INPUT_PATTERNS = (
    "contracts/**", "tools/**", "scripts/**", "tests/unit/**",
    "src/robotics_sim/test/**", ".github/workflows/**", ".opencodereview/**",
    "changes/**", "requirements-dev.txt", "AGENTS.md",
)


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True
    ).stdout.strip()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: Path) -> str:
    return _sha(path.read_bytes())


def snapshot() -> dict[str, Any]:
    """Hash every tracked or untracked non-ignored input, including dirty files."""
    names = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    paths = sorted({name.decode("utf-8", "surrogateescape") for name in names.split(b"\0") if name})
    content: dict[str, str] = {}
    for name in paths:
        path = ROOT / name
        if path.is_symlink():
            content[name] = _sha(("symlink:" + os.readlink(path)).encode())
        elif path.is_file():
            content[name] = _file_sha(path)
        else:
            content[name] = "DELETED"
    digest_input = json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    untracked = [
        name.decode("utf-8", "surrogateescape") for name in
        _git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if name
    ]
    return {
        "digest": _sha(digest_input),
        "dirty": bool(_git("status", "--porcelain", "--untracked-files=all")),
        "workspace_diff_sha256": _sha(_git("diff", "HEAD", "--binary")),
        "untracked_inputs": sorted(untracked),
        "policy_and_test_hashes": {
            name: content[name] for name in paths
            if any(fnmatch.fnmatchcase(name, pattern) for pattern in INPUT_PATTERNS)
        },
    }


def _utc() -> str:
    return datetime.now(UTC).isoformat()


def _commands(suite: str, change: Path) -> list[tuple[str, list[str]]]:
    design_pairs = [
        (f"design-{name}", [
            sys.executable, "tools/validate_design_package.py",
            f"examples/{name}/design-brief.json", f"examples/{name}/design-package.json",
        ]) for name in ("warehouse-tote", "narrow-delivery", "indoor-inspection")
    ]
    if suite == "offline":
        return [
            ("template", [sys.executable, "tools/validate_template.py"]),
            ("skills", [sys.executable, "tools/validate_skills.py"]),
            ("eval-fixtures", [sys.executable, "tools/validate_evals.py"]),
            ("public-content", [sys.executable, "tools/validate_public_content.py"]),
            *design_pairs,
            ("change-contract", [
                sys.executable, "tools/validate_change_contract.py", str(change),
            ]),
            ("unit", [
                sys.executable, "-m", "unittest", "discover", "-s", "tests/unit",
                "-p", "test_*.py",
            ]),
            ("ruff", [
                sys.executable, "-m", "ruff", "check", "tools", "src/robotics_sim",
                "tests/unit",
            ]),
            ("yamllint", ["yamllint", "--config-file", ".yamllint.yaml", "."]),
            ("pymarkdown", ["pymarkdown", "--config", ".pymarkdown.json", "scan", "."]),
            ("shellcheck", ["bash", "-c", "shellcheck scripts/*.sh"]),
        ]
    source = "source /opt/ros/jazzy/setup.bash && "
    installed = source + "source install/setup.bash && "
    return [
        ("ros-build", ["bash", "-c", source + "colcon build --packages-select robotics_sim"]),
        ("ros-pytest", ["bash", "-c", installed +
         "python3 -m pytest -q src/robotics_sim/test/test_*.py --junitxml=" + str(JUNIT)]),
        ("ros-trace", ["bash", "-c", installed +
         "python3 tools/validate_design_package.py "
         "examples/warehouse-tote/design-brief.json "
         "examples/warehouse-tote/design-package.json --evidence " + str(JUNIT)]),
        ("ros-results", ["bash", "-c", installed + "colcon test-result --verbose"]),
    ]


def _junit_summary() -> dict[str, Any] | None:
    path = ROOT / JUNIT
    if not path.is_file():
        return None
    try:
        cases = list(ET.parse(path).iter("testcase"))
    except ET.ParseError:
        return {"path": str(JUNIT), "sha256": _file_sha(path), "parse_error": True}
    return {
        "path": str(JUNIT), "sha256": _file_sha(path), "cases": len(cases),
        "failures": sum(case.find("failure") is not None for case in cases),
        "errors": sum(case.find("error") is not None for case in cases),
        "skipped": sum(case.find("skipped") is not None for case in cases),
    }


def _trace_results() -> list[dict[str, Any]]:
    """Bind each implemented design check to its actual JUnit case."""
    package = json.loads((ROOT / DESIGN).read_text(encoding="utf-8"))
    report = ROOT / JUNIT
    cases = list(ET.parse(report).iter("testcase")) if report.is_file() else []
    results: list[dict[str, Any]] = []
    for check in package["verification_plan"]["checks"]:
        if check["status"] != "implemented":
            continue
        node = check["test_node"]
        parts = node.split("::")
        matches = [
            case for case in cases
            if len(parts) >= 3
            and case.get("classname", "").endswith(f"{Path(parts[0]).stem}.{parts[-2]}")
            and case.get("name") == parts[-1]
        ]
        status = "missing" if not matches else "duplicate" if len(matches) != 1 else "pass"
        if len(matches) == 1:
            for tag in ("failure", "error", "skipped"):
                if matches[0].find(tag) is not None:
                    status = tag
        results.append({
            "test_id": check["id"], "requirement_ids": check["requirement_ids"],
            "test_node": node, "status": status, "junit_sha256": _file_sha(report)
            if report.is_file() else None,
        })
    return results


def run_suite(suite: str) -> int:
    run_id = os.environ.get("EVIDENCE_RUN_ID") or (
        f"{suite}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{os.getpid()}"
    )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id) or ".." in run_id:
        raise ValueError("EVIDENCE_RUN_ID must be a simple directory name")
    directory = ROOT / "artifacts" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    before = snapshot()
    head = _git("rev-parse", "HEAD").decode()
    try:
        change_path = current_change_contract()
        change = json.loads(change_path.read_text(encoding="utf-8"))
    except (ValueError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        failure = {
            "schema_version": "v1", "run_id": run_id, "suite": suite,
            "status": "fail", "started_at": _utc(), "finished_at": _utc(),
            "tested_sha": head, "snapshot": before,
            "blocker": f"ChangeContract preflight failed: {error}", "checks": [],
        }
        (directory / "manifest.json").write_text(json.dumps(failure, indent=2) + "\n")
        print(f"evidence: {directory.relative_to(ROOT)}; status=fail")
        return 1
    manifest: dict[str, Any] = {
        "schema_version": "v1", "run_id": run_id, "suite": suite,
        "status": "fail", "started_at": _utc(),
        "base_sha": os.environ.get("BASE_SHA") or change["base_revision"],
        "pr_head_sha": os.environ.get("PR_HEAD_SHA") or head,
        "pr_head_source": "event" if os.environ.get("PR_HEAD_SHA") else "local_head",
        "tested_sha": head, "snapshot": before,
        "design_package_sha256": _file_sha(ROOT / DESIGN),
        "change_contract_path": change_path.relative_to(ROOT).as_posix(),
        "change_contract_sha256": _file_sha(change_path),
        "environment": {
            "platform": platform.platform(), "python": platform.python_version(),
            "ros_distro": os.environ.get("ROS_DISTRO"),
            "ros_container_image": os.environ.get("ROS_CONTAINER_IMAGE"),
            "github_job": os.environ.get("GITHUB_JOB"),
        },
        "checks": [],
    }
    if suite == "ros":
        (ROOT / JUNIT).unlink(missing_ok=True)
    if suite == "ros" and not Path("/opt/ros/jazzy/setup.bash").is_file():
        manifest["status"] = "blocked"
        manifest["blocker"] = "ROS 2 Jazzy setup.bash unavailable"
    else:
        env = os.environ.copy()
        if suite == "ros":
            env.setdefault("ROS_DOMAIN_ID", "187")
            env["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
        commands = _commands(suite, change_path.relative_to(ROOT))
        for index, (name, command) in enumerate(commands, start=1):
            log_path = directory / f"{index:02d}-{name}.log"
            print(f"[{suite}] {name}: {' '.join(command)}", flush=True)
            started = time.monotonic()
            with log_path.open("w", encoding="utf-8") as log:
                try:
                    process = subprocess.Popen(
                        command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, errors="replace",
                    )
                    assert process.stdout is not None
                    for line in process.stdout:
                        print(line, end="", flush=True)
                        log.write(line)
                    exit_code = process.wait()
                except OSError as error:
                    log.write(f"command could not start: {error}\n")
                    exit_code = 127
            manifest["checks"].append({
                "id": name, "command": command, "exit_code": exit_code,
                "duration_s": round(time.monotonic() - started, 3),
                "log": log_path.relative_to(ROOT).as_posix(),
                "log_sha256": _file_sha(log_path),
            })
            if exit_code != 0:
                break
        else:
            manifest["status"] = "pass"
    manifest["junit"] = _junit_summary() if suite == "ros" else None
    if suite == "ros" and manifest["junit"] and not manifest["junit"].get("parse_error"):
        manifest["trace_results"] = _trace_results()
    manifest["finished_at"] = _utc()
    if snapshot()["digest"] != before["digest"]:
        manifest["status"] = "fail"
        manifest["snapshot_changed_during_run"] = True
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"evidence: {manifest_path.relative_to(ROOT)}; status={manifest['status']}")
    if manifest["status"] != "pass":
        return 2 if manifest["status"] == "blocked" else 1
    errors = validate_manifest(directory)
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


def validate_manifest(directory: Path) -> list[str]:
    """Reject missing, stale, skipped, or mismatched execution evidence."""
    path = directory / "manifest.json"
    if not path.is_file():
        return ["missing evidence manifest"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid evidence manifest: {error}"]
    if not isinstance(manifest, dict):
        return ["evidence manifest must be an object"]
    errors: list[str] = []
    if manifest.get("status") != "pass":
        errors.append("evidence run did not pass")
    if manifest.get("tested_sha") != _git("rev-parse", "HEAD").decode():
        errors.append("tested_sha differs from current HEAD")
    if manifest.get("snapshot", {}).get("digest") != snapshot()["digest"]:
        errors.append("evidence is stale for the current workspace snapshot")
    change = Path(manifest.get("change_contract_path", ""))
    if not re.fullmatch(r"changes/[^/]+/change\.json", change.as_posix()):
        errors.append("invalid change contract path in manifest")
        return errors
    for field, source in (("design_package_sha256", DESIGN), ("change_contract_sha256", change)):
        if manifest.get(field) != _file_sha(ROOT / source):
            errors.append(f"{field} differs from current input")
    if manifest.get("suite") not in {"offline", "ros"}:
        return errors + ["unknown evidence suite"]
    required = _commands(manifest["suite"], change)
    checks = manifest.get("checks", [])
    if not isinstance(checks, list) or any(not isinstance(check, dict) for check in checks):
        return errors + ["required check list must contain objects"]
    if [
        (check.get("id"), check.get("command")) for check in checks
    ] != required:
        errors.append("required check commands are incomplete, changed, or out of order")
    for check in checks:
        log = ROOT / str(check.get("log", ""))
        if not log.resolve().is_relative_to(directory.resolve()) or not log.is_file():
            errors.append(f"missing check log: {check.get('id')}")
        elif check.get("log_sha256") != _file_sha(log):
            errors.append(f"modified check log: {check.get('id')}")
        if check.get("exit_code") != 0:
            errors.append(f"failed check: {check.get('id')}")
    if manifest.get("suite") == "ros":
        junit = manifest.get("junit")
        current = _junit_summary()
        if not isinstance(junit, dict) or junit != current:
            errors.append("JUnit evidence missing or modified")
        elif junit.get("cases", 0) <= 0 or any(
            junit.get(key) for key in ("failures", "errors", "skipped")
        ):
            errors.append("JUnit has zero, failed, erroneous, or skipped tests")
        try:
            current_trace = _trace_results()
        except (OSError, ET.ParseError, ValueError, KeyError) as error:
            errors.append(f"trace result evidence invalid: {error}")
        else:
            if manifest.get("trace_results") != current_trace:
                errors.append("trace results missing or modified")
            required_ids = set(json.loads((ROOT / change).read_text())["required_test_ids"])
            if not required_ids.issubset({
                result["test_id"] for result in current_trace if result["status"] == "pass"
            }):
                errors.append("required test IDs lack passing JUnit cases")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("suite", choices=("offline", "ros"))
    check = sub.add_parser("validate")
    check.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.action == "run":
        return run_suite(args.suite)
    errors = validate_manifest(args.directory.resolve())
    for error in errors:
        print(error)
    if errors:
        return 1
    print("execution evidence matches the current tested snapshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
