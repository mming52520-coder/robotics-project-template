"""The offline runner must report actual unittest outcomes, including no tests."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import run_unit_tests


class UnitRunnerTests(unittest.TestCase):
    def fixture(self, source: str | None) -> tuple[int, dict[str, object]]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests = root / "tests/unit"
            tests.mkdir(parents=True)
            if source is not None:
                (tests / "test_case.py").write_text(source, encoding="utf-8")
            output = root / "build/unit/test-results.json"
            sys.modules.pop("test_case", None)
            with (
                patch.object(run_unit_tests, "ROOT", root),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                status = run_unit_tests.run(output, str(tests))
            sys.modules.pop("test_case", None)
            return status, json.loads(output.read_text(encoding="utf-8"))

    def test_zero_tests_is_failure(self) -> None:
        status, result = self.fixture(None)
        self.assertEqual(status, 1)
        self.assertEqual(result["cases"], 0)

    def test_all_skipped_is_failure(self) -> None:
        status, result = self.fixture(
            "import unittest\nclass Case(unittest.TestCase):\n"
            '    @unittest.skip("not run")\n    def test_required(self):\n        pass\n'
        )
        self.assertEqual(status, 1)
        self.assertEqual(result["tests"][0]["status"], "skipped")

    def test_failure_error_and_expected_failure_are_not_pass(self) -> None:
        examples = (
            ("self.fail()", "failure"),
            ("raise RuntimeError('broken')", "error"),
            (
                "@unittest.expectedFailure\n    def test_required(self):\n        self.fail()",
                "expected_failure",
            ),
        )
        for body, expected in examples:
            with self.subTest(expected=expected):
                if expected == "expected_failure":
                    method = body
                else:
                    method = f"def test_required(self):\n        {body}"
                status, result = self.fixture(
                    f"import unittest\nclass Case(unittest.TestCase):\n    {method}\n"
                )
                self.assertEqual(status, 1)
                self.assertEqual(result["tests"][0]["status"], expected)

    def test_success_records_exact_node(self) -> None:
        status, result = self.fixture(
            "import unittest\nclass Case(unittest.TestCase):\n"
            "    def test_required(self):\n        self.assertTrue(True)\n"
        )
        self.assertEqual(status, 0)
        self.assertEqual(
            result["tests"],
            [
                {
                    "node": "tests/unit/test_case.py::Case::test_required",
                    "status": "pass",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
