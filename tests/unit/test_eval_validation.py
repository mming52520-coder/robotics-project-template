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

    def test_workflow_fixture_cannot_claim_agent_success(self) -> None:
        import json
        from shutil import copytree
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            root = Path(directory) / "evals"
            copytree(ROOT / "evals", root)
            case = root / "workflow-cases" / "01-fake-approval.json"
            document = json.loads(case.read_text())
            document["agent_run_status"] = "passed"
            case.write_text(json.dumps(document))
            errors = validate_eval_suite(root, ROOT)
            self.assertTrue(any("cannot claim an Agent run result" in error for error in errors))

    def test_positive_workflow_requires_code_and_review_artifacts(self) -> None:
        import json
        from shutil import copytree
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            root = Path(directory) / "evals"
            copytree(ROOT / "evals", root)
            case = root / "workflow-cases" / "04-implement-and-review.json"
            document = json.loads(case.read_text())
            document["expected_artifacts"].remove("changed_source")
            case.write_text(json.dumps(document))
            errors = validate_eval_suite(root, ROOT)
            self.assertTrue(any("needs code, tests, evidence, and review" in error
                                for error in errors))


if __name__ == "__main__":
    unittest.main()
