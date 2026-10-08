#!/usr/bin/env python3
"""Preview OCR coverage and optionally save a read-only model review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CRITICAL_PREFIXES = (
    "src/", "tests/", "tools/", "scripts/", "contracts/", "changes/",
    ".github/", ".agents/", ".opencodereview/",
)
RULE_MARKER = "ROBOTICS_EVIDENCE_BOUNDARY"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)


def preview_coverage(
    preview: object, changed: dict[str, str]
) -> tuple[list[str], list[dict[str, str]]]:
    """Reconcile OCR's selected files with Git, including omitted or excluded paths."""
    if not isinstance(preview, dict) or not isinstance(preview.get("files"), list):
        return ["OCR preview lacks a files list"], []
    entries = {
        item.get("path"): item for item in preview["files"]
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    errors: list[str] = []
    excluded: list[dict[str, str]] = []
    for path, status in sorted(changed.items()):
        item = entries.get(path)
        if item is None:
            errors.append(f"changed file omitted from OCR preview: {path}")
        elif not item.get("will_review"):
            reason = str(item.get("exclude_reason", "unexplained"))
            excluded.append({"path": path, "status": status, "reason": reason})
            if status != "D" and path.startswith(CRITICAL_PREFIXES):
                errors.append(f"critical file excluded from OCR review: {path} ({reason})")
    return errors, excluded


def _changed(base: str, head: str) -> dict[str, str]:
    output = _run("git", "diff", "--name-status", base, head).stdout
    changed: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split("\t")
        changed[parts[-1]] = parts[0][0]
    return changed


def _resolved_commit(ref: str) -> str:
    return _run("git", "rev-parse", "--verify", f"{ref}^{{commit}}").stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base")
    parser.add_argument("head")
    parser.add_argument("--rule", type=Path, help="human-reviewed rule file outside this repo")
    parser.add_argument("--run", action="store_true", help="run the model after coverage preview")
    args = parser.parse_args()
    if shutil.which("ocr") is None:
        print("BLOCKED: OCR CLI is not installed")
        return 2
    version_output = _run("ocr", "version").stdout
    match = re.search(r"\bv?(\d+)\.(\d+)\.(\d+)\b", version_output)
    if not match or tuple(map(int, match.groups())) < (1, 11, 1):
        print("BLOCKED: OCR 1.11.1 or newer is required")
        return 2
    if _run("git", "status", "--porcelain").stdout.strip():
        print("BLOCKED: review requires a clean committed snapshot")
        return 2
    base, head = _resolved_commit(args.base), _resolved_commit(args.head)
    if head != _resolved_commit("HEAD"):
        print("BLOCKED: checked-out HEAD differs from requested review target")
        return 2
    rule = (args.rule or ROOT / ".opencodereview/rule.json").resolve()
    if not rule.is_file() or (args.run and rule.is_relative_to(ROOT)):
        print("BLOCKED: model review requires an external human-reviewed rule file")
        return 2
    rule_digest = hashlib.sha256(rule.read_bytes()).hexdigest()
    directory = ROOT / "artifacts" / f"ocr-{head[:12]}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "ocr-version.txt").write_text(version_output, encoding="utf-8")
    changed = _changed(base, head)
    (directory / "git-changed-files.json").write_text(json.dumps(changed, indent=2) + "\n")
    rules_log = directory / "rules-check.txt"
    with rules_log.open("w", encoding="utf-8") as log:
        for path in (
            "src/robotics_sim/launch/sim.launch.py",
            "src/robotics_sim/test/test_sim_graph.py",
            "contracts/design-package.schema.json",
            ".github/workflows/ci.yml",
        ):
            output = _run("ocr", "rules", "check", "--rule", str(rule), path).stdout
            log.write(f"{path}\n{output}\n")
            if RULE_MARKER not in output or "System-Specific Rules" not in output:
                print(f"BLOCKED: project or language rule did not resolve for {path}")
                return 2
    common = [
        "ocr", "review", "--from", base, "--to", head, "--rule", str(rule),
        "--format", "json", "--audience", "agent",
    ]
    preview_file = directory / "preview.json"
    _run(*common, "--preview", "--output", str(preview_file))
    preview: Any = json.loads(preview_file.read_text(encoding="utf-8"))
    errors, excluded = preview_coverage(preview, changed)
    coverage = {
        "base_sha": base, "head_sha": head, "ocr_version": version_output.strip(),
        "rule_sha256": rule_digest, "changed_files": changed, "excluded": excluded,
        "coverage_errors": errors, "model_review_run": False,
    }
    if not changed:
        errors.append("review target has no changed files")
    (directory / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    if errors:
        for error in errors:
            print(error)
        return 1
    if args.run:
        review_file = directory / "review.json"
        _run(*common, "--output", str(review_file))
        result = json.loads(review_file.read_text(encoding="utf-8"))
        if not isinstance(result, dict) or result.get("status") == "skipped":
            print("BLOCKED: OCR did not produce a completed review")
            return 2
        coverage["model_review_run"] = True
        (directory / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    if _run("git", "status", "--porcelain").stdout.strip():
        print("BLOCKED: review changed the repository worktree")
        return 2
    print(f"read-only OCR output: {directory.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
