#!/usr/bin/env python3
"""Run repository unittest discovery and retain machine-readable case outcomes."""

from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _node(test: unittest.case.TestCase) -> str:
    module = sys.modules.get(test.__class__.__module__)
    source = getattr(module, "__file__", None)
    if source is None:
        return test.id()
    try:
        path = Path(source).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return test.id()
    return f"{path}::{test.__class__.__name__}::{test._testMethodName}"


class RecordedResult(unittest.TextTestResult):
    """Use unittest's own outcome callbacks rather than parsing display text."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.outcomes: dict[str, str] = {}

    def startTest(self, test: unittest.case.TestCase) -> None:
        self.outcomes[_node(test)] = "running"
        super().startTest(test)

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        self.outcomes[_node(test)] = "pass"
        super().addSuccess(test)

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:
        self.outcomes[_node(test)] = "skipped"
        super().addSkip(test, reason)

    def addFailure(self, test: unittest.case.TestCase, err: object) -> None:
        self.outcomes[_node(test)] = "failure"
        super().addFailure(test, err)

    def addError(self, test: unittest.case.TestCase, err: object) -> None:
        self.outcomes[_node(test)] = "error"
        super().addError(test, err)

    def addExpectedFailure(self, test: unittest.case.TestCase, err: object) -> None:
        self.outcomes[_node(test)] = "expected_failure"
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:
        self.outcomes[_node(test)] = "unexpected_success"
        super().addUnexpectedSuccess(test)

    def addSubTest(
        self,
        test: unittest.case.TestCase,
        subtest: unittest.case.TestCase,
        err: object | None,
    ) -> None:
        if err is not None:
            self.outcomes[_node(test)] = "failure"
        super().addSubTest(test, subtest, err)


def run(results: Path, start: str = "tests/unit") -> int:
    suite = unittest.TestLoader().discover(start_dir=start, pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    assert isinstance(result, RecordedResult)
    rows = [{"node": node, "status": status} for node, status in sorted(result.outcomes.items())]
    report = {"schema_version": "v1", "runner": "unittest", "cases": result.testsRun, "tests": rows}
    results.parent.mkdir(parents=True, exist_ok=True)
    results.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return (
        0
        if result.testsRun > 0
        and len(rows) == result.testsRun
        and all(row["status"] == "pass" for row in rows)
        and result.wasSuccessful()
        else 1
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--start", default="tests/unit")
    args = parser.parse_args()
    return run(args.results, args.start)


if __name__ == "__main__":
    raise SystemExit(main())
