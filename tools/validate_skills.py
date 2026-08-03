#!/usr/bin/env python3
"""Validate public project Skills with UTF-8 handling on every platform."""

from __future__ import annotations

import re
from pathlib import Path

REQUIRED_UI_KEYS = ("display_name", "short_description", "default_prompt")
REQUIRED_SKILLS = {
    "mobile-robot-system-design",
    "mobile-robot-navigation-planning",
    "mobile-robot-hardware-planning",
    "mobile-robot-control-safety",
    "mobile-robot-verification-plan",
    "open-source-architecture-research",
}


def _frontmatter(content: str) -> tuple[dict[str, str], str] | None:
    if not content.startswith("---\n"):
        return None
    closing = content.find("\n---\n", 4)
    if closing < 0:
        return None
    metadata: dict[str, str] = {}
    for line in content[4:closing].splitlines():
        match = re.fullmatch(r"([a-z_]+):\s*(.+)", line)
        if not match:
            return None
        metadata[match.group(1)] = match.group(2)
    return metadata, content[closing + 5 :]


def validate_skill_tree(root: Path) -> list[str]:
    """Return deterministic validation errors for every skill directory below root."""
    errors: list[str] = []
    skill_files = sorted(root.glob("*/SKILL.md"))
    found_skills = {skill_file.parent.name for skill_file in skill_files}
    for required_skill in sorted(REQUIRED_SKILLS - found_skills):
        errors.append(f"missing required skill: {required_skill}")
    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        parsed = _frontmatter(skill_file.read_text(encoding="utf-8"))
        if not parsed:
            errors.append(f"{skill_name}: invalid YAML frontmatter")
            continue
        metadata, body = parsed
        if set(metadata) != {"name", "description"}:
            errors.append(f"{skill_name}: frontmatter must contain only name and description")
        if metadata.get("name") != skill_name:
            errors.append(f"{skill_name}: frontmatter name must match directory")
        if not metadata.get("description", "").strip():
            errors.append(f"{skill_name}: description must be non-empty")
        if "## Safety and public boundary" not in body:
            errors.append(f"{skill_name}: missing Safety and public boundary section")
        for directory in ("references", "assets"):
            resource_dir = skill_file.parent / directory
            if not resource_dir.is_dir() or not any(resource_dir.iterdir()):
                errors.append(f"{skill_name}: missing {directory} resource")
        ui_file = skill_file.parent / "agents" / "openai.yaml"
        if not ui_file.is_file():
            errors.append(f"{skill_name}: missing agents/openai.yaml")
            continue
        ui_text = ui_file.read_text(encoding="utf-8")
        for key in REQUIRED_UI_KEYS:
            if not re.search(rf"^\s+{key}:\s+\".+\"$", ui_text, flags=re.MULTILINE):
                errors.append(f"{skill_name}: missing UI key {key}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1] / ".agents" / "skills"
    errors = validate_skill_tree(root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
