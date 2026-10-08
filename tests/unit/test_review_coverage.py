"""A review record cannot silently omit files or claim stale tests as passing."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import review_coverage


class ReviewCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = {
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "snapshot_digest": "c" * 64,
            "change_contract_path": "changes/review/change.json",
            "change_contract_sha256": "d" * 64,
            "changed_paths": ["src/robotics_sim/robotics_sim/core.py", "tests/unit/test_core.py"],
        }
        self.record = {
            "schema_version": "v1", **self.context,
            "reviewer_mode": "self",
            "reviewed_paths": self.context["changed_paths"].copy(),
            "skipped_paths": [],
            "findings": [],
            "evidence_runs": {
                "offline": "artifacts/offline-run", "ros": "artifacts/ros-run",
            },
        }

    def validate(self, record: object) -> list[str]:
        with (
            patch.object(review_coverage, "review_context", return_value=self.context),
            patch.object(review_coverage, "_evidence_errors", return_value=[]),
        ):
            return review_coverage.validate_record(record)

    def test_complete_review_can_be_validated_without_claiming_human_approval(self) -> None:
        self.assertEqual(self.validate(self.record), [])
        changed = copy.deepcopy(self.record)
        changed["approved"] = True
        self.assertIn("review record has missing or unknown fields", self.validate(changed))

    def test_missing_or_duplicate_file_blocks_review(self) -> None:
        for paths in (
            self.context["changed_paths"][:1],
            self.context["changed_paths"] * 2,
            list(reversed(self.context["changed_paths"])),
        ):
            with self.subTest(paths=paths):
                changed = copy.deepcopy(self.record)
                changed["reviewed_paths"] = paths
                self.assertTrue(any("reviewed_paths" in error for error in self.validate(changed)))
        changed["reviewed_paths"] = self.context["changed_paths"].copy()
        changed["skipped_paths"] = [{"path": "tests/unit/test_core.py", "reason": "filtered"}]
        self.assertTrue(any("incomplete" in error for error in self.validate(changed)))

    def test_changed_snapshot_or_contract_blocks_old_review(self) -> None:
        for field in ("base_sha", "head_sha", "snapshot_digest", "change_contract_sha256"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.record)
                changed[field] = "0" * len(changed[field])
                self.assertTrue(any(field in error for error in self.validate(changed)))

    def test_unresolved_or_unverifiable_finding_blocks_review(self) -> None:
        finding = {
            "id": "R-1", "path": "src/robotics_sim/robotics_sim/core.py",
            "line": 5, "contract": "REQ-SIM-STOP", "trigger": "stale request",
            "status": "OPEN",
        }
        changed = copy.deepcopy(self.record)
        changed["findings"] = [finding]
        self.assertTrue(any("remains OPEN" in error for error in self.validate(changed)))
        finding["status"] = "FIXED"
        finding["resolution"] = "discarded stale request"
        self.assertTrue(any("verification" in error for error in self.validate(changed)))
        finding["verification"] = "T-SIM-GRAPH in current ROS manifest"
        self.assertEqual(self.validate(changed), [])
        finding["status"] = []
        self.assertTrue(any("status is invalid" in error for error in self.validate(changed)))

    def test_missing_failed_or_wrong_suite_evidence_blocks_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            (artifacts / "offline-run").mkdir(parents=True)
            (artifacts / "offline-run/manifest.json").write_text(json.dumps({"suite": "ros"}))
            with patch.object(review_coverage, "ROOT", root):
                self.assertTrue(any(
                    "wrong suite" in error for error in
                    review_coverage._evidence_errors(
                        "offline", "artifacts/offline-run", self.context
                    )
                ))
                self.assertTrue(any(
                    "missing or NOT_RUN" in error for error in
                    review_coverage._evidence_errors("ros", None, self.context)
                ))
                (artifacts / "offline-run/manifest.json").write_text(
                    json.dumps({"suite": "offline", "status": "pass"})
                )
                with patch.object(
                    review_coverage, "validate_manifest", return_value=["failed check: unit"]
                ):
                    self.assertIn(
                        "offline evidence: failed check: unit",
                        review_coverage._evidence_errors(
                            "offline", "artifacts/offline-run", self.context
                        ),
                    )

    def test_evidence_must_use_reviewed_base_head_and_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "artifacts/offline-run"
            directory.mkdir(parents=True)
            manifest = {
                "suite": "offline", "base_sha": self.context["base_sha"],
                "pr_head_sha": self.context["head_sha"],
                "change_contract_path": self.context["change_contract_path"],
                "change_contract_sha256": self.context["change_contract_sha256"],
            }
            with (
                patch.object(review_coverage, "ROOT", root),
                patch.object(review_coverage, "validate_manifest", return_value=[]),
            ):
                for field in (
                    "base_sha", "pr_head_sha", "change_contract_path",
                    "change_contract_sha256",
                ):
                    with self.subTest(field=field):
                        changed = {**manifest, field: "forged"}
                        (directory / "manifest.json").write_text(json.dumps(changed))
                        self.assertTrue(any(
                            field in error for error in review_coverage._evidence_errors(
                                "offline", "artifacts/offline-run", self.context
                            )
                        ))


if __name__ == "__main__":
    unittest.main()
