"""OCR preview must account for the actual Git change set before model review."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.ocr_review import preview_coverage

ROOT = Path(__file__).resolve().parents[2]


class OCRCoverageTests(unittest.TestCase):
    def test_rules_include_language_baseline(self) -> None:
        rules = json.loads((ROOT / ".opencodereview/rule.json").read_text())
        self.assertTrue(rules["rules"][0]["merge_system_rule"])
        self.assertIn("**/*.msg", rules["include"])
        self.assertIn("**/*.srv", rules["include"])
        self.assertIn("**/*.xacro", rules["include"])

    def test_missing_or_excluded_critical_file_blocks_review(self) -> None:
        changed = {
            "src/robotics_sim/test/test_sim_graph.py": "M",
            "contracts/design-package.schema.json": "M",
        }
        preview = {"files": [{
            "path": "src/robotics_sim/test/test_sim_graph.py",
            "will_review": False, "exclude_reason": "default_path",
        }]}
        errors, excluded = preview_coverage(preview, changed)
        self.assertTrue(any("critical file excluded" in error for error in errors))
        self.assertTrue(any("omitted" in error for error in errors))
        self.assertEqual(excluded[0]["reason"], "default_path")

    def test_deleted_file_is_recorded_without_false_review_claim(self) -> None:
        errors, excluded = preview_coverage(
            {"files": [{
                "path": "tools/old.py", "will_review": False,
                "exclude_reason": "deleted",
            }]},
            {"tools/old.py": "D"},
        )
        self.assertEqual(errors, [])
        self.assertEqual(excluded[0]["status"], "D")


if __name__ == "__main__":
    unittest.main()
