#!/usr/bin/env python3
"""Validate a DesignBrief and versioned DesignPackage with JSON Schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .design_contracts import (
        validate_design_brief,
        validate_design_package,
        validate_junit_evidence,
        validate_legacy_design_package,
    )
except ImportError:  # Direct script execution has no package context.
    from design_contracts import (
        validate_design_brief,
        validate_design_package,
        validate_junit_evidence,
        validate_legacy_design_package,
    )


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("package", nargs="?", type=Path)
    parser.add_argument(
        "--evidence", type=Path, help="verify implemented checks in a JUnit XML file"
    )
    parser.add_argument(
        "--legacy-design-only", action="store_true",
        help="validate a v1 package only as a design artifact, without implementation status",
    )
    args = parser.parse_args()
    if args.legacy_design_only and args.evidence:
        parser.error("--legacy-design-only cannot accept implementation evidence")

    brief = load_json(args.brief)
    brief_errors = validate_design_brief(brief)
    if args.package:
        package = load_json(args.package)
        errors = (
            validate_legacy_design_package(package, brief)
            if args.legacy_design_only else validate_design_package(package, brief)
        )
        if args.evidence:
            plan = package.get("verification_plan") if isinstance(package, dict) else None
            checks = plan.get("checks", []) if isinstance(plan, dict) else []
            expected = {
                check.get("evidence") for check in checks
                if isinstance(check, dict) and check.get("status") == "implemented"
            } if isinstance(checks, list) else set()
            if expected != {str(args.evidence)}:
                errors.append("--evidence must match the implemented checks' evidence artifact")
            elif not errors:
                errors.extend(validate_junit_evidence(package, args.evidence))
    else:
        errors = brief_errors
        if args.evidence:
            errors.append("--evidence requires a DesignPackage")
    if errors:
        for error in errors:
            print(error)
        return 1
    if args.legacy_design_only:
        print("legacy v1 design-only validation passed; implementation is not qualified")
    else:
        print("design contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
