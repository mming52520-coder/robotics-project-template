"""Execution evidence must distinguish a passing linked case from a skipped one."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import evidence


class EvidenceTests(unittest.TestCase):
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
