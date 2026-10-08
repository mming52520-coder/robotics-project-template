#!/usr/bin/env python3
"""Inventory and verify a local Agent review against the actual candidate snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

try:
    from .change_contracts import changed_paths, current_change_contract, trusted_candidate_base
    from .evidence import snapshot, validate_manifest
except ImportError:
    from change_contracts import changed_paths, current_change_contract, trusted_candidate_base
    from evidence import snapshot, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
REVIEW_MODES = {"self", "separate_agent", "ocr"}
FINDING_STATES = {"OPEN", "PENDING", "FIXED", "FALSE_POSITIVE", "DUPLICATE", "OUT_OF_SCOPE"}
CONTEXT_FIELDS = (
    "base_sha", "head_sha", "snapshot_digest", "change_contract_path",
    "change_contract_sha256", "changed_paths",
)
RECORD_FIELDS = {
    "schema_version", *CONTEXT_FIELDS, "reviewer_mode", "reviewed_paths",
    "skipped_paths", "findings", "evidence_runs",
}


def review_context() -> dict[str, object]:
    """Reuse the trusted diff and evidence snapshot used by the existing gates."""
    base = trusted_candidate_base(ROOT)
    contract = current_change_contract(ROOT)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {
        "base_sha": base,
        "head_sha": head,
        "snapshot_digest": snapshot()["digest"],
        "change_contract_path": contract.relative_to(ROOT).as_posix(),
        "change_contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
        "changed_paths": sorted(changed_paths(base, ROOT)),
    }


def new_record() -> dict[str, object]:
    return {
        "schema_version": "v1",
        **review_context(),
        "reviewer_mode": "self",
        "reviewed_paths": [],
        "skipped_paths": [],
        "findings": [],
        "evidence_runs": {"offline": None, "ros": None},
    }


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence_errors(suite: str, value: object, context: dict[str, object]) -> list[str]:
    if not _text(value):
        return [f"{suite} evidence is missing or NOT_RUN"]
    try:
        directory = (ROOT / value).resolve()
        if not directory.is_relative_to((ROOT / "artifacts").resolve()):
            return [f"{suite} evidence must be under ignored artifacts/"]
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("suite") != suite:
            return [f"{suite} evidence has the wrong suite"]
        errors = [f"{suite} evidence: {error}" for error in validate_manifest(directory)]
        for manifest_field, context_field in (
            ("base_sha", "base_sha"), ("pr_head_sha", "head_sha"),
            ("change_contract_path", "change_contract_path"),
            ("change_contract_sha256", "change_contract_sha256"),
        ):
            if manifest.get(manifest_field) != context[context_field]:
                errors.append(f"{suite} evidence {manifest_field} differs from the review target")
        return errors
    except (OSError, ValueError, TypeError, KeyError) as error:
        return [f"{suite} evidence is unreadable: {error}"]


def validate_record(record: object) -> list[str]:
    """Fail closed on incomplete coverage, unresolved findings, or stale execution proof."""
    if not isinstance(record, dict):
        return ["review record must be an object"]
    if record.get("schema_version") != "v1":
        return ["review record schema_version must be v1"]
    errors: list[str] = []
    if set(record) != RECORD_FIELDS:
        errors.append("review record has missing or unknown fields")
    current = review_context()
    for field in CONTEXT_FIELDS:
        if record.get(field) != current[field]:
            errors.append(f"review {field} differs from the current candidate")
    mode = record.get("reviewer_mode")
    if not isinstance(mode, str) or mode not in REVIEW_MODES:
        errors.append("reviewer_mode must be self, separate_agent, or ocr")
    paths = current["changed_paths"]
    reviewed = record.get("reviewed_paths")
    if not isinstance(reviewed, list) or reviewed != paths:
        errors.append("reviewed_paths must list every changed path exactly once in sorted order")
    skipped = record.get("skipped_paths")
    if not isinstance(skipped, list):
        errors.append("skipped_paths must be a list")
    elif skipped:
        errors.append("review is incomplete while any changed path is skipped")
    findings = record.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
    else:
        seen: set[str] = set()
        for index, finding in enumerate(findings):
            label = f"findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{label} must be an object")
                continue
            identifier = finding.get("id")
            if not _text(identifier) or identifier in seen:
                errors.append(f"{label}.id must be non-empty and unique")
            else:
                seen.add(identifier)
            if finding.get("path") not in paths:
                errors.append(f"{label}.path must name a changed file")
            if type(finding.get("line")) is not int or finding["line"] <= 0:
                errors.append(f"{label}.line must be positive")
            for field in ("contract", "trigger"):
                if not _text(finding.get(field)):
                    errors.append(f"{label}.{field} must be non-empty")
            state = finding.get("status")
            if not isinstance(state, str) or state not in FINDING_STATES:
                errors.append(f"{label}.status is invalid")
            elif state in {"OPEN", "PENDING"}:
                errors.append(f"{label} remains {state}")
            elif not _text(finding.get("resolution")):
                errors.append(f"{label}.resolution must explain the disposition")
            if state == "FIXED" and not _text(finding.get("verification")):
                errors.append(f"{label}.verification must identify regression evidence")
    runs = record.get("evidence_runs")
    if not isinstance(runs, dict) or set(runs) != {"offline", "ros"}:
        errors.append("evidence_runs must name offline and ros")
    else:
        for suite in ("offline", "ros"):
            errors.extend(_evidence_errors(suite, runs[suite], current))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("create", help="write an ignored record with the exact review inventory")
    validate = sub.add_parser("validate", help="validate a filled review record")
    validate.add_argument("record", type=Path)
    args = parser.parse_args()
    if args.action == "create":
        directory = ROOT / "artifacts" / (
            f"review-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{os.getpid()}"
        )
        directory.mkdir(parents=True, exist_ok=False)
        path = directory / "record.json"
        path.write_text(json.dumps(new_record(), indent=2, ensure_ascii=False) + "\n")
        print(path.relative_to(ROOT))
        return 0
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        errors = validate_record(record)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        errors = [f"review validation failed: {error}"]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("review coverage and execution evidence match the current candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
