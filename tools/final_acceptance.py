#!/usr/bin/env python3
"""Combine bounded scope, executed tests, and review coverage for one candidate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from .change_contracts import (
        current_change_contract,
        trusted_candidate_base,
        validate_change_contract,
    )
    from .review_coverage import new_record, validate_record
except ImportError:
    from change_contracts import (
        current_change_contract,
        trusted_candidate_base,
        validate_change_contract,
    )
    from review_coverage import new_record, validate_record

ROOT = Path(__file__).resolve().parents[1]
REVIEW_BEGIN = "<!-- ALL_IN_CODE_REVIEW_V2\n"
REVIEW_END = "\nEND_ALL_IN_CODE_REVIEW_V2 -->"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _event_review(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    event = json.loads(path.read_text(encoding="utf-8"))
    body = event["pull_request"]["body"]
    if not isinstance(body, str) or body.count(REVIEW_BEGIN) != 1 or body.count(REVIEW_END) != 1:
        raise ValueError("PR body needs exactly one v2 review record block")
    payload = body.split(REVIEW_BEGIN, 1)[1].split(REVIEW_END, 1)[0]
    if len(payload) > 100_000:
        raise ValueError("PR review record is too large")
    record = json.loads(payload)
    if not isinstance(record, dict) or record.get("schema_version") != "v2":
        raise ValueError("PR body review record must be v2")
    return event, record


def _merge_errors(event: dict[str, Any]) -> list[str]:
    """Verify the PR merge test really combines this event's target and head."""
    try:
        target = event["pull_request"]["base"]["sha"]
        candidate = event["pull_request"]["head"]["sha"]
        tested = _git("rev-parse", "HEAD")
        parents = _git("rev-list", "--parents", "-n", "1", "HEAD").split()
        base = _git("merge-base", target, candidate)
    except (KeyError, TypeError, subprocess.CalledProcessError) as error:
        return [f"PR merge relationship cannot be resolved: {error}"]
    errors = []
    if parents != [tested, target, candidate]:
        errors.append("tested SHA is not the merge of the event target and candidate head")
    if os.environ.get("GITHUB_SHA") and tested != os.environ["GITHUB_SHA"]:
        errors.append("tested SHA differs from the GitHub event checkout")
    if os.environ.get("BASE_SHA") != target or os.environ.get("PR_HEAD_SHA") != candidate:
        errors.append("trusted event base/head environment differs from the PR payload")
    if trusted_candidate_base(ROOT) != base:
        errors.append("diff merge-base differs from the trusted event range")
    return errors


def validate_final(
    record: dict[str, Any],
    runs: dict[str, str] | None,
    event: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if event is not None:
        errors.extend(_merge_errors(event))
        if record.get("schema_version") != "v2":
            errors.append("PR final acceptance requires a v2 review record")
        expected_run = os.environ.get("GITHUB_RUN_ID")
        expected_attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
        if not expected_run or not expected_attempt:
            errors.append("GitHub run identity is missing")
        elif runs is not None:
            for suite in ("offline", "ros"):
                expected = f"{suite}-{expected_run}-{expected_attempt}"
                if Path(runs[suite]).name != expected:
                    errors.append(f"{suite} evidence is not from this CI run")
    try:
        contract_path = current_change_contract()
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        errors.extend(validate_change_contract(contract, ROOT, phase="final"))
        errors.extend(validate_record(record, runs))
        actual_runs = runs or record.get("evidence_runs")
        if not isinstance(actual_runs, dict) or set(actual_runs) != {"offline", "ros"}:
            errors.append("offline and ROS execution evidence are both required")
        else:
            passing: set[str] = set()
            for suite in ("offline", "ros"):
                manifest_path = ROOT / actual_runs[suite] / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if event is not None and manifest.get("run_id") != Path(actual_runs[suite]).name:
                    errors.append(f"{suite} manifest run ID differs from the current CI run")
                traces = (
                    manifest.get("offline_trace_results", [])
                    if suite == "offline"
                    else manifest.get("trace_results", [])
                    + manifest.get("selected_ros_trace_results", [])
                )
                passing.update(
                    row["test_id"]
                    for row in traces
                    if isinstance(row, dict) and row.get("status") == "pass"
                )
            missing = set(contract["required_test_ids"]) - passing
            if missing:
                errors.append(f"required test IDs lack passing execution: {sorted(missing)}")
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        errors.append(f"final acceptance inputs are invalid: {error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--record", type=Path, help="local ignored review JSON")
    source.add_argument("--event", type=Path, help="GitHub PR event JSON with review block")
    parser.add_argument("--offline", help="current offline artifact directory")
    parser.add_argument("--ros", help="current ROS artifact directory")
    args = parser.parse_args()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "artifacts" / f"final-{stamp}-{os.getpid()}"
    output.mkdir(parents=True, exist_ok=False)
    runs = {"offline": args.offline, "ros": args.ros} if args.offline and args.ros else None
    try:
        if args.event:
            try:
                event, record = _event_review(args.event)
            except ValueError:
                template = new_record("v2")
                (output / "review-template.json").write_text(
                    json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                raise
            if runs is None:
                raise ValueError("PR acceptance needs --offline and --ros from this run")
        else:
            event = None
            record = json.loads(args.record.read_text(encoding="utf-8"))
        errors = validate_final(record, runs, event)
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors = [f"final acceptance input failed: {error}"]
    report = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "tested_sha": _git("rev-parse", "HEAD"),
        "candidate_head_sha": os.environ.get("PR_HEAD_SHA") or _git("rev-parse", "HEAD"),
        "reviewer_mode_is_a_claim": True,
        "human_approval": "not_asserted",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for error in errors:
        print(error, file=sys.stderr)
    print(f"final acceptance: {report['status']}; report: {output.relative_to(ROOT)}/report.json")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
