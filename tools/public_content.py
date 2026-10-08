"""Detect sensitive or identifying content that must not enter a public template."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".ruff_cache", ".pytest_cache"}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12"}
PATTERNS = (
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "assigned-secret",
        re.compile(
            r'''(?i)\b(?:password|secret|api[_-]?key|token)\b\s*[:=]\s*["'][^"'${}<\s][^"']{7,}["']'''
        ),
    ),
    (
        "hardware-identifying-field",
        re.compile(
            r'''(?i)["'](?:model|vendor|manufacturer|part[_-]?number|serial[_-]?number)["']\s*:'''
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    line: int


def is_ignored_private_file(root: Path, path: Path) -> bool:
    """Exclude local private data only while Git actually ignores it."""
    relative = path.relative_to(root)
    if relative.parts[:2] != ("config", "private"):
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--quiet", "--", relative.as_posix()],
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def scan_public_content(root: Path) -> list[Finding]:
    """Scan UTF-8 text files without following ignored development artifacts."""
    findings: list[Finding] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if (
            any(part in EXCLUDED_PARTS for part in relative.parts)
            or is_ignored_private_file(root, path)
        ):
            continue
        if path.name == ".env" or path.suffix.lower() in SENSITIVE_SUFFIXES:
            findings.append(Finding("sensitive-filename", relative.as_posix(), 0))
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for kind, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(kind, relative.as_posix(), line_number))
    return findings
