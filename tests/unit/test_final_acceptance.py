"""Final delivery checks candidate identity, review, and executed test evidence."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import final_acceptance


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


class FinalAcceptanceTests(unittest.TestCase):
    def test_pr_merge_relation_uses_both_parents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            git(root, "init", "-b", "main")
            git(root, "config", "user.name", "Fixture")
            git(root, "config", "user.email", "fixture@example.invalid")
            (root / "file.txt").write_text("base\n")
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            target = git(root, "rev-parse", "HEAD")
            git(root, "checkout", "-b", "candidate")
            (root / "candidate.txt").write_text("change\n")
            git(root, "add", ".")
            git(root, "commit", "-m", "candidate")
            candidate = git(root, "rev-parse", "HEAD")
            git(root, "checkout", "main")
            git(root, "merge", "--no-ff", "candidate", "-m", "synthetic merge")
            tested = git(root, "rev-parse", "HEAD")
            event = {"pull_request": {"base": {"sha": target}, "head": {"sha": candidate}}}
            with (
                patch.object(final_acceptance, "ROOT", root),
                patch.dict(
                    os.environ, {"BASE_SHA": target, "PR_HEAD_SHA": candidate, "GITHUB_SHA": tested}
                ),
            ):
                self.assertEqual(final_acceptance._merge_errors(event), [])
                wrong = {"pull_request": {"base": {"sha": target}, "head": {"sha": target}}}
                self.assertTrue(final_acceptance._merge_errors(wrong))

    def test_final_gate_keeps_review_and_required_test_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = root / "changes/task/change.json"
            contract.parent.mkdir(parents=True)
            contract.write_text(json.dumps({"required_test_ids": ["T-WF-REQUIRED"]}))
            for suite in ("offline", "ros"):
                path = root / f"artifacts/{suite}/manifest.json"
                path.parent.mkdir(parents=True)
                path.write_text(
                    json.dumps(
                        {
                            "offline_trace_results": [],
                            "trace_results": [],
                            "selected_ros_trace_results": [],
                        }
                    )
                )
            with (
                patch.object(final_acceptance, "ROOT", root),
                patch.object(final_acceptance, "current_change_contract", return_value=contract),
                patch.object(final_acceptance, "validate_change_contract", return_value=[]),
                patch.object(
                    final_acceptance,
                    "validate_record",
                    return_value=["offline evidence cannot satisfy change acceptance"],
                ),
            ):
                errors = final_acceptance.validate_final(
                    {"schema_version": "v1"},
                    {"offline": "artifacts/offline", "ros": "artifacts/ros"},
                )
            self.assertTrue(any("cannot satisfy change" in error for error in errors))
            self.assertTrue(any("T-WF-REQUIRED" in error for error in errors))

    def test_pr_body_requires_one_v2_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "event.json"
            path.write_text(json.dumps({"pull_request": {"body": "no review"}}))
            with self.assertRaisesRegex(ValueError, "exactly one"):
                final_acceptance._event_review(path)
            path.write_text(
                json.dumps(
                    {
                        "pull_request": {
                            "body": (
                                final_acceptance.REVIEW_BEGIN
                                + '{"schema_version":"v2"}'
                                + final_acceptance.REVIEW_END
                            )
                        }
                    }
                )
            )
            _, record = final_acceptance._event_review(path)
            self.assertEqual(record["schema_version"], "v2")


if __name__ == "__main__":
    unittest.main()
