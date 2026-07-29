"""Validation tests for the public Skill evaluation manifest."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.validate_evals import validate_eval_document, validate_eval_suite


ROOT = Path(__file__).resolve().parents[2]


class EvalValidationTests(unittest.TestCase):
    def test_committed_eval_suite_is_complete(self) -> None:
        self.assertEqual(validate_eval_suite(ROOT / "evals", ROOT), [])

    def test_negative_case_requires_a_blocking_outcome(self) -> None:
        document = {
            "id": "missing-stop",
            "kind": "negative",
            "skill_sequence": ["mobile-robot-control-safety"],
            "expected_outcome": {"must_block": False, "minimum_blockers": []},
        }

        errors = validate_eval_document(document, ROOT)

        self.assertIn("negative evaluation must require a blocker", errors)


if __name__ == "__main__":
    unittest.main()
