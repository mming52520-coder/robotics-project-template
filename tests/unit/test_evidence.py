"""Execution evidence must distinguish a passing linked case from a skipped one."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import evidence


class EvidenceTests(unittest.TestCase):
    def test_runner_blocks_divergent_index_before_any_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "changes/task/change.json"
            contract.parent.mkdir(parents=True)
            contract.write_text(json.dumps({"base_revision": "a" * 40}))
            design = root / evidence.DESIGN
            design.parent.mkdir(parents=True)
            design.write_text("{}")
            divergent = {"digest": "b" * 64, "index_worktree_diverged": True}
            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "snapshot", return_value=divergent),
                patch.object(evidence, "_git", return_value=("c" * 40).encode()),
                patch.object(evidence, "current_change_contract", return_value=contract),
                patch.object(evidence, "_commands", side_effect=AssertionError("ran checks")),
                patch.dict(os.environ, {"EVIDENCE_RUN_ID": "blocked-index"}),
            ):
                self.assertEqual(evidence.run_suite("offline"), 2)
            manifest = json.loads((root / "artifacts/blocked-index/manifest.json").read_text())
            self.assertEqual(manifest["status"], "blocked")
            self.assertEqual(manifest["checks"], [])

    def test_snapshot_binds_index_and_blocks_divergent_staged_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tracked.py").write_text("tested worktree\n")
            staged_diff = b"staged change"

            def git(*args: str) -> bytes:
                if args[:2] == ("ls-files", "--cached"):
                    return b"tracked.py\0"
                if args[:2] == ("ls-files", "--others"):
                    return b""
                if args[0] == "status":
                    return b"M  tracked.py"
                raise AssertionError(args)

            def git_raw(*args: str) -> bytes:
                if args[:2] == ("diff", "--cached"):
                    return staged_diff
                if args[:2] == ("diff", "HEAD"):
                    return b""
                raise AssertionError(args)

            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "_git", git),
                patch.object(evidence, "_git_raw", git_raw),
                patch.object(evidence, "_staged_worktree_diverged", return_value=True),
            ):
                first = evidence.snapshot()
                self.assertTrue(first["index_worktree_diverged"])
                staged_diff = b"different staged change"
                self.assertNotEqual(first["digest"], evidence.snapshot()["digest"])

    def test_staged_deletion_with_remaining_worktree_file_is_divergent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "removed.py"
            path.write_text("still tested, but absent from index\n")

            def git_raw(*args: str) -> bytes:
                if args[:2] == ("diff", "--cached"):
                    return b"removed.py\0"
                if args[:2] == ("ls-files", "--stage"):
                    return b""
                raise AssertionError(args)

            with patch.object(evidence, "ROOT", root), patch.object(evidence, "_git_raw", git_raw):
                self.assertTrue(evidence._staged_worktree_diverged())
                path.unlink()
                self.assertFalse(evidence._staged_worktree_diverged())

    def test_staged_blob_must_match_tested_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "changed.py"
            path.write_bytes(b"old worktree")

            def git_raw(*args: str) -> bytes:
                if args[:2] == ("diff", "--cached"):
                    return b"changed.py\0"
                if args[:2] == ("ls-files", "--stage"):
                    return b"100644 abcdef 0\tchanged.py\0"
                if args[0] == "show":
                    return b"staged content"
                raise AssertionError(args)

            with patch.object(evidence, "ROOT", root), patch.object(evidence, "_git_raw", git_raw):
                self.assertTrue(evidence._staged_worktree_diverged())
                path.write_bytes(b"staged content")
                self.assertFalse(evidence._staged_worktree_diverged())

    def test_trace_results_use_actual_junit_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({
                "verification_plan": {"checks": [{
                    "id": "T-SIM-STOP", "status": "implemented",
                    "requirement_ids": ["REQ-SIM-STOP"],
                    "test_node": "tests/test_gate.py::GateTest::test_stop",
                }]},
            }))
            report = root / "pytest.xml"
            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "DESIGN", Path("package.json")),
                patch.object(evidence, "JUNIT", Path("pytest.xml")),
            ):
                self.assertEqual(evidence._trace_results()[0]["status"], "missing")
                report.write_text(
                    '<testsuite><testcase classname="test_gate.GateTest" '
                    'name="test_stop"><skipped/></testcase></testsuite>'
                )
                self.assertEqual(evidence._trace_results()[0]["status"], "skipped")
                report.write_text(
                    '<testsuite><testcase classname="test_gate.GateTest" '
                    'name="test_stop"/></testsuite>'
                )
                self.assertEqual(evidence._trace_results()[0]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
