"""Safety checks for public Skills and published repository content."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.public_content import is_ignored_private_file, scan_public_content
from tools.validate_skills import validate_skill_tree
from tools.validate_template import private_configuration_errors

ROOT = Path(__file__).resolve().parents[2]


class SkillAndContentValidationTests(unittest.TestCase):
    def test_robot_design_skills_are_complete(self) -> None:
        self.assertEqual(validate_skill_tree(ROOT / ".agents" / "skills"), [])

    def test_skill_without_safety_boundary_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory) / "skills"
            skill_path = skill_root / "unsafe-skill"
            skill_path.mkdir(parents=True)
            (skill_path / "SKILL.md").write_text(
                "---\nname: unsafe-skill\ndescription: Test unsafe skill.\n---\n# Unsafe\n",
                encoding="utf-8",
            )

            errors = validate_skill_tree(skill_root)

        self.assertIn("unsafe-skill: missing Safety and public boundary section", errors)

    def test_missing_required_skill_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_skill_tree(Path(directory) / "skills")

        self.assertIn("missing required skill: mobile-robot-system-design", errors)
        self.assertIn("missing required skill: open-source-architecture-research", errors)

    def test_content_scanner_rejects_sensitive_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.py"
            candidate.write_text('api' + '_key = "abcdefgh"\n', encoding="utf-8")

            findings = scan_public_content(Path(directory))

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "assigned-secret")

    def test_content_scanner_rejects_hardware_model_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.json"
            candidate.write_text('{"' + 'model' + '": "example-model"}\n', encoding="utf-8")

            findings = scan_public_content(Path(directory))

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "hardware-identifying-field")

    def test_private_selection_is_scanned_if_force_tracked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".gitignore").write_text("config/private/*\n", encoding="utf-8")
            private = root / "config" / "private" / "selection.json"
            private.parent.mkdir(parents=True)
            private.write_text('{"' + 'model' + '": "candidate"}\n', encoding="utf-8")
            self.assertTrue(is_ignored_private_file(root, private))
            self.assertEqual(scan_public_content(root), [])
            self.assertEqual(private_configuration_errors(root), [])

            subprocess.run(
                ["git", "-C", str(root), "add", "-f", "--", "config/private/selection.json"],
                check=True,
            )
            self.assertFalse(is_ignored_private_file(root, private))
            findings = scan_public_content(root)
            self.assertTrue(any(item.kind == "hardware-identifying-field" for item in findings))
            self.assertEqual(
                private_configuration_errors(root),
                ["private configuration tracked or not ignored: config/private/selection.json"],
            )


if __name__ == "__main__":
    unittest.main()
