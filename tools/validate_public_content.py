#!/usr/bin/env python3
"""Fail when a public repository candidate contains sensitive identifying content."""

from __future__ import annotations

import argparse
from pathlib import Path

from public_content import scan_public_content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    findings = scan_public_content(args.path.resolve())
    if findings:
        for finding in findings:
            print(f"{finding.kind}: {finding.path}:{finding.line}")
        return 1
    print("public content scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
