"""Execution evidence must distinguish a passing linked case from a skipped one."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import evidence


class EvidenceTests(unittest.TestCase):
    def test_selected_project_evidence_is_not_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "examples/project-b/design-package.json"
            selected.parent.mkdir(parents=True)
            selected.write_text(
                json.dumps(
                    {
                        "verification_plan": {
                            "checks": [
                                {
                                    "id": "T-PROJECT-B",
                                    "requirement_ids": ["REQ-PROJECT-B"],
                                    "status": "implemented",
                                    "test_node": (
                                        "tests/unit/test_project_b.py::ProjectBTests::test_behavior"
                                    ),
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            default = root / evidence.DESIGN
            default.parent.mkdir(parents=True)
            default.write_text(json.dumps({"verification_plan": {"checks": []}}), encoding="utf-8")
            result = root / evidence.UNIT_RESULTS
            result.parent.mkdir(parents=True)
            result.write_text(
                json.dumps(
                    {
                        "schema_version": "v1",
                        "runner": "unittest",
                        "cases": 1,
                        "tests": [
                            {
                                "node": (
                                    "tests/unit/test_project_b.py::ProjectBTests::test_behavior"
                                ),
                                "status": "pass",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "load_catalog", return_value=({}, {})),
            ):
                self.assertEqual(
                    evidence._selected_design(
                        {"design_package_ref": "examples/project-b/design-package.json"}
                    ),
                    Path("examples/project-b/design-package.json"),
                )
                trace = evidence._offline_trace_results(
                    Path("examples/project-b/design-package.json")
                )
                self.assertEqual(trace[0]["test_id"], "T-PROJECT-B")
                self.assertEqual(trace[0]["status"], "pass")
                self.assertEqual(evidence._offline_trace_results(evidence.DESIGN), [])

    def test_baseline_and_change_purpose_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            design = root / evidence.DESIGN
            design.parent.mkdir(parents=True)
            design.write_text("{}", encoding="utf-8")
            catalog = root / evidence.CATALOG
            catalog.parent.mkdir(parents=True)
            catalog.write_text("{}", encoding="utf-8")
            clean = {"digest": "b" * 64, "dirty": False, "index_worktree_diverged": False}
            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "snapshot", return_value=clean),
                patch.object(evidence, "_git", return_value=("c" * 40).encode()),
                patch.object(
                    evidence, "current_change_contract", side_effect=ValueError("missing")
                ),
                patch.object(evidence, "_commands", return_value=[]),
                patch.object(evidence, "validate_manifest", return_value=[]),
            ):
                with patch.dict(os.environ, {"EVIDENCE_RUN_ID": "baseline"}):
                    self.assertEqual(evidence.run_suite("offline", purpose="baseline"), 0)
                with patch.dict(os.environ, {"EVIDENCE_RUN_ID": "change"}):
                    self.assertEqual(evidence.run_suite("offline", purpose="change"), 1)
            baseline = json.loads((root / "artifacts/baseline/manifest.json").read_text())
            change = json.loads((root / "artifacts/change/manifest.json").read_text())
            self.assertEqual(baseline["purpose"], "baseline")
            self.assertIsNone(baseline["change_contract_path"])
            self.assertEqual(change["purpose"], "change")
            self.assertIn("preflight failed", change["blocker"])

    def test_failed_post_run_validation_is_not_a_passing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (evidence.DESIGN, evidence.CATALOG):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
            clean = {"digest": "b" * 64, "dirty": False, "index_worktree_diverged": False}
            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "snapshot", return_value=clean),
                patch.object(evidence, "_git", return_value=("c" * 40).encode()),
                patch.object(evidence, "_commands", return_value=[]),
                patch.object(
                    evidence, "validate_manifest", return_value=["required unit node missing"]
                ),
                patch.dict(os.environ, {"EVIDENCE_RUN_ID": "validation-failed"}),
            ):
                self.assertEqual(evidence.run_suite("offline", purpose="baseline"), 1)
            manifest = json.loads((root / "artifacts/validation-failed/manifest.json").read_text())
            self.assertEqual(manifest["status"], "fail")
            self.assertEqual(manifest["validation_errors"], ["required unit node missing"])

    def test_mandatory_unit_outcomes_are_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            design = root / evidence.DESIGN
            design.parent.mkdir(parents=True)
            node = "tests/unit/test_case.py::Case::test_one"
            design.write_text(
                json.dumps(
                    {
                        "verification_plan": {
                            "checks": [
                                {
                                    "id": "T-REQUIRED",
                                    "status": "implemented",
                                    "requirement_ids": ["REQ-REQUIRED"],
                                    "test_node": node,
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            contract = root / "changes/task/change.json"
            contract.parent.mkdir(parents=True)
            contract.write_text(
                json.dumps(
                    {
                        "design_package_ref": evidence.DESIGN.as_posix(),
                        "required_test_ids": ["T-REQUIRED"],
                    }
                ),
                encoding="utf-8",
            )
            catalog = root / evidence.CATALOG
            catalog.parent.mkdir(parents=True)
            catalog.write_text("{}", encoding="utf-8")
            report = root / evidence.UNIT_RESULTS
            report.parent.mkdir(parents=True)
            log = root / "artifacts/check/01-unit.log"
            log.parent.mkdir(parents=True)
            log.write_text("real runner log", encoding="utf-8")
            clean = {"digest": "d" * 64, "dirty": False, "index_worktree_diverged": False}
            command = ["python3", "tools/run_unit_tests.py"]
            manifest = {
                "status": "pass",
                "purpose": "change",
                "suite": "offline",
                "tested_sha": "c" * 40,
                "snapshot": clean,
                "change_contract_path": "changes/task/change.json",
                "change_contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
                "design_package_ref": evidence.DESIGN.as_posix(),
                "design_package_sha256": hashlib.sha256(design.read_bytes()).hexdigest(),
                "workflow_catalog_sha256": hashlib.sha256(catalog.read_bytes()).hexdigest(),
                "ros_regression_design_ref": evidence.DESIGN.as_posix(),
                "offline_trace_results": [],
                "checks": [
                    {
                        "id": "unit",
                        "command": command,
                        "exit_code": 0,
                        "log": "artifacts/check/01-unit.log",
                        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                    }
                ],
            }
            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "snapshot", return_value=clean),
                patch.object(evidence, "_git", return_value=("c" * 40).encode()),
                patch.object(evidence, "current_change_contract", return_value=contract),
                patch.object(evidence, "_commands", return_value=[("unit", command)]),
                patch.object(evidence, "load_catalog", return_value=({}, {})),
            ):
                for status in ("skipped", "failure", "error", "expected_failure", "pass"):
                    with self.subTest(status=status):
                        report.write_text(
                            json.dumps(
                                {
                                    "schema_version": "v1",
                                    "runner": "unittest",
                                    "cases": 1,
                                    "tests": [
                                        {
                                            "node": node,
                                            "status": status,
                                        }
                                    ],
                                }
                            ),
                            encoding="utf-8",
                        )
                        manifest["unit_results"] = evidence._unit_summary()
                        manifest["offline_trace_results"] = evidence._offline_trace_results(
                            evidence.DESIGN
                        )
                        (log.parent / "manifest.json").write_text(json.dumps(manifest))
                        errors = evidence.validate_manifest(log.parent)
                        self.assertEqual(not errors, status == "pass", errors)
                report.write_text(
                    json.dumps(
                        {
                            "schema_version": "v1",
                            "runner": "unittest",
                            "cases": 1,
                            "tests": [
                                {
                                    "node": "tests/unit/test_other.py::Case::test_other",
                                    "status": "pass",
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                manifest["unit_results"] = evidence._unit_summary()
                manifest["offline_trace_results"] = evidence._offline_trace_results(evidence.DESIGN)
                (log.parent / "manifest.json").write_text(json.dumps(manifest))
                self.assertTrue(
                    any(
                        "missing or not passing" in error
                        for error in evidence.validate_manifest(log.parent)
                    )
                )
                report.unlink()
                self.assertIn(
                    "unittest result evidence missing or modified",
                    evidence.validate_manifest(log.parent),
                )

    def test_runner_blocks_divergent_index_before_any_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "changes/task/change.json"
            contract.parent.mkdir(parents=True)
            contract.write_text(
                json.dumps(
                    {
                        "base_revision": "a" * 40,
                        "design_package_ref": evidence.DESIGN.as_posix(),
                    }
                )
            )
            design = root / evidence.DESIGN
            design.parent.mkdir(parents=True)
            design.write_text("{}")
            catalog = root / evidence.CATALOG
            catalog.parent.mkdir(parents=True)
            catalog.write_text("{}")
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
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "verification_plan": {
                            "checks": [
                                {
                                    "id": "T-SIM-STOP",
                                    "status": "implemented",
                                    "requirement_ids": ["REQ-SIM-STOP"],
                                    "test_node": (
                                        "src/robotics_sim/test/test_gate.py::GateTest::test_stop"
                                    ),
                                }
                            ]
                        },
                    }
                )
            )
            report = root / "pytest.xml"
            with (
                patch.object(evidence, "ROOT", root),
                patch.object(evidence, "DESIGN", Path("package.json")),
                patch.object(evidence, "JUNIT", Path("pytest.xml")),
            ):
                self.assertEqual(
                    evidence._trace_results(Path("package.json"))[0]["status"], "missing"
                )
                report.write_text(
                    '<testsuite><testcase classname="test.test_gate.GateTest" '
                    'name="test_stop"><skipped/></testcase></testsuite>'
                )
                self.assertEqual(
                    evidence._trace_results(Path("package.json"))[0]["status"], "skipped"
                )
                report.write_text(
                    '<testsuite><testcase classname="test.test_gate.GateTest" '
                    'name="test_stop"/></testsuite>'
                )
                self.assertEqual(evidence._trace_results(Path("package.json"))[0]["status"], "pass")
                collision = json.loads((root / "package.json").read_text())
                collision["verification_plan"]["checks"][0]["test_node"] = (
                    "other_project/test/test_gate.py::GateTest::test_stop"
                )
                (root / "package.json").write_text(json.dumps(collision))
                self.assertEqual(
                    evidence._trace_results(Path("package.json"))[0]["status"], "missing"
                )


if __name__ == "__main__":
    unittest.main()
