#!/usr/bin/env python3
"""Validate the public robotics project template and its safety defaults."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    ".agents/skills/README.md",
    "AGENTS.md",
    "LICENSE",
    "contracts/design-brief.schema.json",
    "contracts/design-package.schema.json",
    "contracts/README.md",
    "config/example/system.yaml",
    "config/private/README.md",
    "docs/architecture/system-context.md",
    "docs/decisions/0000-template.md",
    "docs/decisions/0001-model-free-design-package.md",
    "docs/reference/indoor-wheeled-robot.md",
    "docs/work-memory/current.md",
    "experiments/experiment-template.md",
    "scripts/run-checks.sh",
    "src/README.md",
    "tests/unit/README.md",
    "tests/integration/README.md",
    "tests/replay/README.md",
    "evals/cases/01-warehouse-tote.json",
)
EXCLUDED_PARTS = {".git", ".venv", "__pycache__"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def scan_public_files() -> list[str]:
    findings: list[str] = []
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.name == ".env" or path.suffix.lower() in {".key", ".p12", ".pem"}:
            findings.append(f"sensitive filename: {relative.as_posix()}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in SECRET_PATTERNS):
                findings.append(f"secret-like content: {relative.as_posix()}:{line_number}")
    return findings


def validate() -> list[str]:
    errors = [
        f"missing required path: {path}"
        for path in REQUIRED_PATHS
        if not (ROOT / path).is_file()
    ]

    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if "config/private/*" not in ignore_text:
        errors.append(".gitignore must exclude config/private/*")

    system_config = (ROOT / "config/example/system.yaml").read_text(encoding="utf-8")
    if "hardware_output_enabled: false" not in system_config:
        errors.append("example configuration must disable hardware output")

    private_files = [
        path
        for path in (ROOT / "config/private").rglob("*")
        if path.is_file() and path.name != "README.md"
    ]
    errors.extend(
        f"private configuration present: {path.relative_to(ROOT)}" for path in private_files
    )
    errors.extend(scan_public_files())
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {len(REQUIRED_PATHS)} required paths and public-release safety defaults")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
