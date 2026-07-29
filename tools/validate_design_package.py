#!/usr/bin/env python3
"""Validate a DesignBrief and DesignPackage pair without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from design_contracts import validate_design_brief, validate_design_package


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("package", nargs="?", type=Path)
    args = parser.parse_args()

    brief_errors = validate_design_brief(load_json(args.brief))
    if args.package:
        errors = validate_design_package(load_json(args.package), load_json(args.brief))
    else:
        errors = brief_errors
    if errors:
        for error in errors:
            print(error)
        return 1
    print("design contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
