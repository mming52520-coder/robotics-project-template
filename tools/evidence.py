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
    from .workflow_contracts import CATALOG, load_catalog
except ImportError:
    from change_contracts import current_change_contract
    from workflow_contracts import CATALOG, load_catalog

ROOT = Path(__file__).resolve().parents[1]
JUNIT = Path("build/robotics_sim/test_results/robotics_sim/pytest.xml")
UNIT_RESULTS = Path("build/unit/test-results.json")
PYTHON = "python3"
DESIGN = Path("examples/warehouse-tote/design-package.json")
INPUT_PATTERNS = (
    "contracts/**",
    "tools/**",
    "scripts/**",
    "tests/unit/**",
    "src/robotics_sim/test/**",
    ".github/workflows/**",
    ".opencodereview/**",
    "changes/**",
    "requirements-dev.txt",
    "AGENTS.md",
)


def _git_raw(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def _git(*args: str) -> bytes:
    return _git_raw(*args).strip()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: Path) -> str:
    return _sha(path.read_bytes())


def _staged_worktree_diverged() -> bool:
    """Catch staged bytes or deletions that differ from the files being tested."""
    names = _git_raw("diff", "--cached", "--name-only", "--no-renames", "-z", "HEAD", "--").split(
        b"\0"
    )
    for raw_name in names:
        if not raw_name:
            continue
        name = raw_name.decode("utf-8", "surrogateescape")
        path = ROOT / name
        entry = _git_raw("ls-files", "--stage", "-z", "--", name)
        if not entry:
            if path.exists() or path.is_symlink():
                return True
            continue
        metadata = entry.split(b"\t", 1)[0].split(b" ")
        if len(metadata) != 3 or metadata[2] != b"0":
            return True
        mode = metadata[0]
        if mode == b"120000":
            if not path.is_symlink():
                return True
            working = os.readlink(path).encode("utf-8", "surrogateescape")
        elif mode in (b"100644", b"100755"):
            if path.is_symlink() or not path.is_file():
                return True
            working = path.read_bytes()
            if (mode == b"100755") != bool(path.stat().st_mode & 0o111):
                return True
        else:
            return True
        if working != _git_raw("show", f":{name}"):
            return True
    return False


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
    index_diff = _git_raw("diff", "--cached", "HEAD", "--binary")
    index_diff_sha256 = _sha(index_diff)
    digest_input = json.dumps(
        {"files": content, "index_diff_sha256": index_diff_sha256},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    untracked = [
        name.decode("utf-8", "surrogateescape")
        for name in _git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
        if name
    ]
    return {
        "digest": _sha(digest_input),
        "dirty": bool(_git("status", "--porcelain", "--untracked-files=all")),
        "workspace_diff_sha256": _sha(_git_raw("diff", "HEAD", "--binary")),
        "index_diff_sha256": index_diff_sha256,
        "index_worktree_diverged": _staged_worktree_diverged(),
        "untracked_inputs": sorted(untracked),
        "policy_and_test_hashes": {
            name: content[name]
            for name in paths
            if any(fnmatch.fnmatchcase(name, pattern) for pattern in INPUT_PATTERNS)
        },
    }


def _utc() -> str:
    return datetime.now(UTC).isoformat()


def _selected_design(change: dict[str, Any] | None) -> Path:
    """Use the candidate's validated relative design reference, or the baseline sample."""
    if change is None:
        return DESIGN
    value = change.get("design_package_ref")
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("design_package_ref must be a repository-relative path")
    selected = (ROOT / value).resolve()
    if not selected.is_relative_to(ROOT.resolve()) or not selected.is_file():
        raise ValueError("design_package_ref must name a repository file")
    return selected.relative_to(ROOT.resolve())


def _commands(
    suite: str, change: Path | None, purpose: str = "change", design: Path = DESIGN
) -> list[tuple[str, list[str]]]:
    design_pairs = [
        (
            f"design-{name}",
            [
                PYTHON,
                "tools/validate_design_package.py",
                f"examples/{name}/design-brief.json",
                f"examples/{name}/design-package.json",
            ],
        )
        for name in ("warehouse-tote", "narrow-delivery", "indoor-inspection")
    ]
    if design not in {
        Path(f"examples/{name}/design-package.json")
        for name in ("warehouse-tote", "narrow-delivery", "indoor-inspection")
    }:
        design_pairs.append(
            (
                "design-active",
                [
                    PYTHON,
                    "tools/validate_design_package.py",
                    str(design.with_name("design-brief.json")),
                    str(design),
                ],
            )
        )
    if suite == "offline":
        return [
            ("template", [PYTHON, "tools/validate_template.py"]),
            ("skills", [PYTHON, "tools/validate_skills.py"]),
            ("eval-fixtures", [PYTHON, "tools/validate_evals.py"]),
            ("public-content", [PYTHON, "tools/validate_public_content.py"]),
            *design_pairs,
            *(
                [
                    (
                        "change-contract",
                        [
                            PYTHON,
                            "tools/validate_change_contract.py",
                            str(change),
                        ],
                    )
                ]
                if purpose == "change"
                else []
            ),
            (
                "unit",
                [
                    PYTHON,
                    "tools/run_unit_tests.py",
                    "--results",
                    str(UNIT_RESULTS),
                ],
            ),
            (
                "ruff",
                [
                    PYTHON,
                    "-m",
                    "ruff",
                    "check",
                    "tools",
                    "src/robotics_sim",
                    "tests/unit",
                ],
            ),
            ("yamllint", ["yamllint", "--config-file", ".yamllint.yaml", "."]),
            ("pymarkdown", ["pymarkdown", "--config", ".pymarkdown.json", "scan", "."]),
            ("shellcheck", ["bash", "-c", "shellcheck scripts/*.sh"]),
        ]
    source = "source /opt/ros/jazzy/setup.bash && "
    installed = source + "source install/setup.bash && "
    return [
        ("ros-build", ["bash", "-c", source + "colcon build --packages-select robotics_sim"]),
        (
            "ros-pytest",
            [
                "bash",
                "-c",
                installed
                + "python3 -m pytest -q src/robotics_sim/test/test_*.py --junitxml="
                + str(JUNIT),
            ],
        ),
        (
            "ros-trace",
            [
                "bash",
                "-c",
                installed + "python3 tools/validate_design_package.py "
                "examples/warehouse-tote/design-brief.json "
                "examples/warehouse-tote/design-package.json --evidence " + str(JUNIT),
            ],
        ),
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
        "path": str(JUNIT),
        "sha256": _file_sha(path),
        "cases": len(cases),
        "failures": sum(case.find("failure") is not None for case in cases),
        "errors": sum(case.find("error") is not None for case in cases),
        "skipped": sum(case.find("skipped") is not None for case in cases),
    }


def _unit_summary() -> dict[str, Any] | None:
    path = ROOT / UNIT_RESULTS
    if not path.is_file():
        return None
    summary: dict[str, Any] = {"path": str(UNIT_RESULTS), "sha256": _file_sha(path)}
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError("unittest result must be an object")
        rows = report["tests"]
        if (
            report.get("schema_version") != "v1"
            or report.get("runner") != "unittest"
            or type(report.get("cases")) is not int
            or report["cases"] <= 0
            or not isinstance(rows, list)
            or len(rows) != report["cases"]
            or any(
                not isinstance(row, dict)
                or set(row) != {"node", "status"}
                or not isinstance(row["node"], str)
                or not row["node"].strip()
                or row["status"]
                not in {
                    "pass",
                    "skipped",
                    "failure",
                    "error",
                    "expected_failure",
                    "unexpected_success",
                    "running",
                }
                for row in rows
            )
            or len({row["node"] for row in rows}) != len(rows)
        ):
            raise ValueError("invalid unittest result rows")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        summary["parse_error"] = True
        return summary
    summary["cases"] = report["cases"]
    summary["tests"] = rows
    return summary


def _trace_results(design: Path = DESIGN) -> list[dict[str, Any]]:
    """Bind each implemented design check to its actual JUnit case."""
    package = json.loads((ROOT / design).read_text(encoding="utf-8"))
    report = ROOT / JUNIT
    cases = list(ET.parse(report).iter("testcase")) if report.is_file() else []
    results: list[dict[str, Any]] = []
    for check in package["verification_plan"]["checks"]:
        if check["status"] != "implemented":
            continue
        node = check["test_node"]
        if node.startswith("tests/unit/"):
            continue
        parts = node.split("::")
        source = Path(parts[0])
        in_ros_suite = (
            len(parts) == 3
            and source.parent == Path("src/robotics_sim/test")
            and source.name.startswith("test_")
            and source.suffix == ".py"
        )
        classname = f"test.{source.stem}.{parts[1]}"
        matches = [
            case
            for case in cases
            if in_ros_suite
            and case.get("classname") == classname
            and case.get("name") == parts[2]
        ]
        status = "missing" if not matches else "duplicate" if len(matches) != 1 else "pass"
        if len(matches) == 1:
            for tag in ("failure", "error", "skipped"):
                if matches[0].find(tag) is not None:
                    status = tag
        results.append(
            {
                "test_id": check["id"],
                "requirement_ids": check["requirement_ids"],
                "test_node": node,
                "status": status,
                "junit_sha256": _file_sha(report) if report.is_file() else None,
            }
        )
    return results


def _offline_trace_results(design: Path) -> list[dict[str, Any]]:
    """Resolve workflow and selected-design unit IDs against actual runner cases."""
    summary = _unit_summary()
    if not summary or summary.get("parse_error"):
        return []
    outcomes = {row["node"]: row["status"] for row in summary["tests"]}
    _, workflow_checks = load_catalog(ROOT)
    package = json.loads((ROOT / design).read_text(encoding="utf-8"))
    selected = [
        check
        for check in package["verification_plan"]["checks"]
        if check["status"] == "implemented" and check["test_node"].startswith("tests/unit/")
    ]
    entries = [
        (check["id"], check["requirement_ids"], check["test_node"]) for check in selected
    ] + [
        (identifier, check["requirement_ids"], check["test_node"])
        for identifier, check in workflow_checks.items()
    ]
    return [
        {
            "test_id": identifier,
            "requirement_ids": requirements,
            "test_node": node,
            "status": outcomes.get(node, "missing"),
            "results_sha256": summary["sha256"],
        }
        for identifier, requirements, node in entries
    ]


def run_suite(suite: str, purpose: str = "change") -> int:
    if purpose not in {"baseline", "change"}:
        raise ValueError("purpose must be baseline or change")
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
        if purpose == "baseline":
            if before["dirty"]:
                raise ValueError("baseline verification requires a clean worktree")
            change_path = None
            change = None
        else:
            change_path = current_change_contract()
            change = json.loads(change_path.read_text(encoding="utf-8"))
        selected_design = _selected_design(change)
    except (ValueError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        failure = {
            "schema_version": "v1",
            "run_id": run_id,
            "suite": suite,
            "purpose": purpose,
            "status": "fail",
            "started_at": _utc(),
            "finished_at": _utc(),
            "tested_sha": head,
            "snapshot": before,
            "blocker": f"{purpose} preflight failed: {error}",
            "checks": [],
        }
        (directory / "manifest.json").write_text(json.dumps(failure, indent=2) + "\n")
        print(f"evidence: {directory.relative_to(ROOT)}; status=fail")
        return 1
    manifest: dict[str, Any] = {
        "schema_version": "v1",
        "run_id": run_id,
        "suite": suite,
        "purpose": purpose,
        "status": "fail",
        "started_at": _utc(),
        "base_sha": head
        if purpose == "baseline"
        else os.environ.get("BASE_SHA") or change["base_revision"],
        "pr_head_sha": head if purpose == "baseline" else os.environ.get("PR_HEAD_SHA") or head,
        "pr_head_source": "event" if os.environ.get("PR_HEAD_SHA") else "local_head",
        "tested_sha": head,
        "snapshot": before,
        "design_package_ref": selected_design.as_posix(),
        "design_package_sha256": _file_sha(ROOT / selected_design),
        "workflow_catalog_sha256": _file_sha(ROOT / CATALOG),
        "ros_regression_design_ref": DESIGN.as_posix(),
        "change_contract_path": change_path.relative_to(ROOT).as_posix() if change_path else None,
        "change_contract_sha256": _file_sha(change_path) if change_path else None,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "ros_distro": os.environ.get("ROS_DISTRO"),
            "ros_container_image": os.environ.get("ROS_CONTAINER_IMAGE"),
            "github_job": os.environ.get("GITHUB_JOB"),
        },
        "checks": [],
    }
    if suite == "ros":
        (ROOT / JUNIT).unlink(missing_ok=True)
    else:
        (ROOT / UNIT_RESULTS).unlink(missing_ok=True)
    if before["index_worktree_diverged"]:
        manifest["status"] = "blocked"
        manifest["blocker"] = "staged index differs from the tested worktree"
    elif suite == "ros" and not Path("/opt/ros/jazzy/setup.bash").is_file():
        manifest["status"] = "blocked"
        manifest["blocker"] = "ROS 2 Jazzy setup.bash unavailable"
    else:
        env = os.environ.copy()
        if suite == "ros":
            env.setdefault("ROS_DOMAIN_ID", "187")
            env["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
        commands = _commands(
            suite,
            change_path.relative_to(ROOT) if change_path else None,
            purpose,
            selected_design,
        )
        for index, (name, command) in enumerate(commands, start=1):
            log_path = directory / f"{index:02d}-{name}.log"
            print(f"[{suite}] {name}: {' '.join(command)}", flush=True)
            started = time.monotonic()
            with log_path.open("w", encoding="utf-8") as log:
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=ROOT,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        errors="replace",
                    )
                    assert process.stdout is not None
                    for line in process.stdout:
                        print(line, end="", flush=True)
                        log.write(line)
                    exit_code = process.wait()
                except OSError as error:
                    log.write(f"command could not start: {error}\n")
                    exit_code = 127
            manifest["checks"].append(
                {
                    "id": name,
                    "command": command,
                    "exit_code": exit_code,
                    "duration_s": round(time.monotonic() - started, 3),
                    "log": log_path.relative_to(ROOT).as_posix(),
                    "log_sha256": _file_sha(log_path),
                }
            )
            if exit_code != 0:
                break
        else:
            manifest["status"] = "pass"
    manifest["junit"] = _junit_summary() if suite == "ros" else None
    manifest["unit_results"] = _unit_summary() if suite == "offline" else None
    if (
        suite == "offline"
        and manifest["unit_results"]
        and not manifest["unit_results"].get("parse_error")
    ):
        try:
            manifest["offline_trace_results"] = _offline_trace_results(selected_design)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            manifest["status"] = "fail"
            manifest["blocker"] = f"offline trace invalid: {error}"
    if suite == "ros" and manifest["junit"] and not manifest["junit"].get("parse_error"):
        manifest["trace_results"] = _trace_results()
        manifest["selected_ros_trace_results"] = _trace_results(selected_design)
    manifest["finished_at"] = _utc()
    if snapshot()["digest"] != before["digest"]:
        manifest["status"] = "fail"
        manifest["snapshot_changed_during_run"] = True
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    errors = validate_manifest(directory) if manifest["status"] == "pass" else []
    if errors:
        manifest["status"] = "fail"
        manifest["validation_errors"] = errors
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    for error in errors:
        print(error, file=sys.stderr)
    print(f"evidence: {manifest_path.relative_to(ROOT)}; status={manifest['status']}")
    if manifest["status"] == "blocked":
        return 2
    return 0 if manifest["status"] == "pass" else 1


def validate_manifest(directory: Path, expected_purpose: str | None = None) -> list[str]:
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
    purpose = manifest.get("purpose")
    if purpose not in {"baseline", "change"}:
        return ["evidence purpose must be baseline or change"]
    if expected_purpose is not None and purpose != expected_purpose:
        errors.append(f"{purpose} evidence cannot satisfy {expected_purpose} acceptance")
    if manifest.get("status") != "pass":
        errors.append("evidence run did not pass")
    if manifest.get("tested_sha") != _git("rev-parse", "HEAD").decode():
        errors.append("tested_sha differs from current HEAD")
    current_snapshot = snapshot()
    recorded_snapshot = manifest.get("snapshot")
    if (
        not isinstance(recorded_snapshot, dict)
        or recorded_snapshot.get("digest") != current_snapshot["digest"]
    ):
        errors.append("evidence is stale for the current workspace snapshot")
    if current_snapshot["index_worktree_diverged"]:
        errors.append("staged index differs from the tested worktree")
    if purpose == "baseline" and current_snapshot["dirty"]:
        errors.append("baseline evidence requires a clean worktree")
    if purpose == "baseline" and (
        manifest.get("base_sha") != manifest.get("tested_sha")
        or manifest.get("pr_head_sha") != manifest.get("tested_sha")
    ):
        errors.append("baseline evidence must name only its tested HEAD")
    change: Path | None = None
    if purpose == "change":
        change_value = manifest.get("change_contract_path")
        if not isinstance(change_value, str) or not re.fullmatch(
            r"changes/[^/]+/change\.json", change_value
        ):
            errors.append("invalid change contract path in manifest")
            return errors
        change = Path(change_value)
        try:
            if ROOT / change != current_change_contract():
                errors.append("evidence does not name the current ChangeContract")
        except ValueError as error:
            errors.append(f"current ChangeContract is invalid: {error}")
    elif (
        manifest.get("change_contract_path") is not None
        or manifest.get("change_contract_sha256") is not None
    ):
        errors.append("baseline evidence must not claim a ChangeContract")
    try:
        document = json.loads((ROOT / change).read_text(encoding="utf-8")) if change else None
        selected_design = _selected_design(document)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        return errors + [f"selected design is invalid: {error}"]
    if manifest.get("design_package_ref") != selected_design.as_posix():
        errors.append("evidence selected design differs from the ChangeContract")
    if manifest.get("ros_regression_design_ref") != DESIGN.as_posix():
        errors.append("ROS regression design reference was changed")
    if manifest.get("workflow_catalog_sha256") != _file_sha(ROOT / CATALOG):
        errors.append("workflow requirement catalog differs from current input")
    sources = [("design_package_sha256", selected_design)]
    if change is not None:
        sources.append(("change_contract_sha256", change))
    for field, source in sources:
        if manifest.get(field) != _file_sha(ROOT / source):
            errors.append(f"{field} differs from current input")
    if manifest.get("suite") not in {"offline", "ros"}:
        return errors + ["unknown evidence suite"]
    required = _commands(manifest["suite"], change, purpose, selected_design)
    required_ids = set(document["required_test_ids"]) if document else set()
    checks = manifest.get("checks", [])
    if not isinstance(checks, list) or any(not isinstance(check, dict) for check in checks):
        return errors + ["required check list must contain objects"]
    if [(check.get("id"), check.get("command")) for check in checks] != required:
        errors.append("required check commands are incomplete, changed, or out of order")
    for check in checks:
        log = ROOT / str(check.get("log", ""))
        if not log.resolve().is_relative_to(directory.resolve()) or not log.is_file():
            errors.append(f"missing check log: {check.get('id')}")
        elif check.get("log_sha256") != _file_sha(log):
            errors.append(f"modified check log: {check.get('id')}")
        if check.get("exit_code") != 0:
            errors.append(f"failed check: {check.get('id')}")
    if manifest.get("suite") == "offline":
        unit = manifest.get("unit_results")
        current_unit = _unit_summary()
        if not isinstance(unit, dict) or unit != current_unit:
            errors.append("unittest result evidence missing or modified")
        elif unit.get("parse_error") or not unit.get("cases"):
            errors.append("unittest result evidence has no valid executed cases")
        elif any(row["status"] != "pass" for row in unit["tests"]):
            errors.append("unittest result has skipped, failed, or unexecuted cases")
        try:
            current_trace = _offline_trace_results(selected_design)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            errors.append(f"offline trace result evidence invalid: {error}")
        else:
            if manifest.get("offline_trace_results") != current_trace:
                errors.append("offline trace results missing or modified")
            if any(result["status"] != "pass" for result in current_trace):
                errors.append("selected design or workflow unit test is missing or not passing")
            try:
                workflow_ids = set(load_catalog(ROOT)[1])
                package = json.loads((ROOT / selected_design).read_text(encoding="utf-8"))
                design_unit_ids = {
                    check["id"]
                    for check in package["verification_plan"]["checks"]
                    if check["status"] == "implemented"
                    and check["test_node"].startswith("tests/unit/")
                }
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                errors.append(f"offline required-test policy is invalid: {error}")
            else:
                offline_required = required_ids & (workflow_ids | design_unit_ids)
                if not offline_required.issubset(
                    {result["test_id"] for result in current_trace if result["status"] == "pass"}
                ):
                    errors.append("required offline test IDs lack passing executed cases")
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
            selected_trace = _trace_results(selected_design)
            if manifest.get("selected_ros_trace_results") != selected_trace:
                errors.append("selected design ROS trace results missing or modified")
            if any(result["status"] != "pass" for result in selected_trace):
                errors.append("selected design ROS test is missing or not passing")
            try:
                offline_ids = set(load_catalog(ROOT)[1]) | {
                    check["id"]
                    for check in json.loads((ROOT / selected_design).read_text(encoding="utf-8"))[
                        "verification_plan"
                    ]["checks"]
                    if check["status"] == "implemented"
                    and check["test_node"].startswith("tests/unit/")
                }
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                errors.append(f"ROS required-test policy is invalid: {error}")
                offline_ids = set()
            if not (required_ids - offline_ids).issubset(
                {
                    result["test_id"]
                    for result in current_trace + selected_trace
                    if result["status"] == "pass"
                }
            ):
                errors.append("required test IDs lack passing JUnit cases")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("suite", choices=("offline", "ros"))
    run.add_argument("--purpose", choices=("baseline", "change"), default="change")
    check = sub.add_parser("validate")
    check.add_argument("directory", type=Path)
    check.add_argument("--purpose", choices=("baseline", "change"))
    args = parser.parse_args()
    if args.action == "run":
        return run_suite(args.suite, purpose=args.purpose)
    errors = validate_manifest(args.directory.resolve(), expected_purpose=args.purpose)
    for error in errors:
        print(error)
    if errors:
        return 1
    print("execution evidence matches the current tested snapshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
