#!/usr/bin/env python3
"""Validate the deterministic fixtures used to evaluate public robot-design Skills."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

try:
    from .design_contracts import validate_design_package
except ImportError:  # Direct script execution has no package context.
    from design_contracts import validate_design_package


REQUIRED_PACKAGE_SECTIONS = {
    "system_architecture",
    "algorithm_plan",
    "hardware_functional_plan",
    "safety_plan",
    "verification_plan",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_eval_document(document: object, repo_root: Path) -> list[str]:
    """Validate a single evaluation manifest against committed fixture files."""
    if not isinstance(document, Mapping):
        return ["evaluation must be an object"]
    errors: list[str] = []
    for field in ("id", "kind", "skill_sequence", "expected_outcome"):
        if field not in document:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors
    if document["kind"] not in {"positive", "negative"}:
        return ["kind must be positive or negative"]
    if not isinstance(document["skill_sequence"], list) or not document["skill_sequence"]:
        errors.append("skill_sequence must be a non-empty list")
    expected = document["expected_outcome"]
    if not isinstance(expected, Mapping):
        return errors + ["expected_outcome must be an object"]

    if document["kind"] == "negative":
        if expected.get("must_block") is not True:
            errors.append("negative evaluation must require a blocker")
        minimum_blockers = expected.get("minimum_blockers")
        if not isinstance(minimum_blockers, list) or not minimum_blockers:
            errors.append("negative evaluation must name minimum blockers")
        return errors

    fixtures = document.get("fixtures")
    if not isinstance(fixtures, Mapping):
        return errors + ["positive evaluation must define fixtures"]
    for field in ("brief", "package"):
        if not isinstance(fixtures.get(field), str):
            errors.append(f"positive evaluation missing fixtures.{field}")
    if errors:
        return errors
    brief_path = repo_root / fixtures["brief"]
    package_path = repo_root / fixtures["package"]
    if not brief_path.is_file() or not package_path.is_file():
        return ["positive evaluation fixture path does not exist"]
    errors.extend(validate_design_package(_load_json(package_path), _load_json(brief_path)))
    required_sections = expected.get("required_sections")
    if (
        not isinstance(required_sections, list)
        or set(required_sections) != REQUIRED_PACKAGE_SECTIONS
    ):
        errors.append("positive evaluation must require every core DesignPackage section")
    if expected.get("model_free") is not True:
        errors.append("positive evaluation must require model_free output")
    return errors


def validate_eval_suite(evals_root: Path, repo_root: Path) -> list[str]:
    """Validate the three positive and three negative public evaluation cases."""
    cases = sorted((evals_root / "cases").glob("*.json"))
    if len(cases) != 6:
        return ["evaluation suite must contain exactly six cases"]
    errors: list[str] = []
    kinds: list[str] = []
    identifiers: set[str] = set()
    for path in cases:
        document = _load_json(path)
        if isinstance(document, Mapping):
            kinds.append(str(document.get("kind")))
            identifier = document.get("id")
            if identifier in identifiers:
                errors.append(f"duplicate evaluation id: {identifier}")
            identifiers.add(str(identifier))
        document_errors = validate_eval_document(document, repo_root)
        errors.extend(f"{path.name}: {error}" for error in document_errors)
    if kinds.count("positive") != 3 or kinds.count("negative") != 3:
        errors.append("evaluation suite must contain three positive and three negative cases")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evals", nargs="?", type=Path, default=Path("evals"))
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    errors = validate_eval_suite(args.evals, repo_root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("evaluation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
