"""Contract tests for the public, model-free robot design package."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.design_contracts import (
    validate_design_brief,
    validate_design_package,
    validate_junit_evidence,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "examples" / "warehouse-tote"


def load_example(name: str) -> dict[str, object]:
    return json.loads((EXAMPLE_DIR / name).read_text(encoding="utf-8"))


class DesignContractTests(unittest.TestCase):
    def test_example_brief_is_valid(self) -> None:
        self.assertEqual(validate_design_brief(load_example("design-brief.json")), [])

    def test_example_package_is_valid(self) -> None:
        for example in ("warehouse-tote", "narrow-delivery", "indoor-inspection"):
            with self.subTest(example=example):
                directory = ROOT / "examples" / example
                brief = json.loads((directory / "design-brief.json").read_text())
                package = json.loads((directory / "design-package.json").read_text())
                self.assertEqual(validate_design_package(package, brief), [])

    def test_v1_package_requires_explicit_upgrade(self) -> None:
        brief = load_example("design-brief.json")
        package = load_example("design-package.json")
        package["schema_version"] = "v1"
        self.assertIn("schema_version must be v2", validate_design_package(package, brief))

    def test_core_sections_reject_missing_null_and_wrong_type(self) -> None:
        brief = load_example("design-brief.json")
        original = load_example("design-package.json")
        for field in (
            "interfaces", "algorithm_plan", "hardware_functional_plan",
            "safety_plan", "verification_plan",
        ):
            for replacement in ("missing", None, 42):
                with self.subTest(field=field, replacement=replacement):
                    package = copy.deepcopy(original)
                    if replacement == "missing":
                        package.pop(field)
                    else:
                        package[field] = replacement
                    self.assertTrue(validate_design_package(package, brief))

    def test_nested_contract_fields_reject_missing_null_and_wrong_type(self) -> None:
        brief = load_example("design-brief.json")
        original = load_example("design-package.json")
        paths = (
            ("interfaces", 1, "owner"), ("interfaces", 1, "producer"),
            ("interfaces", 1, "consumer"), ("interfaces", 1, "units"),
            ("interfaces", 1, "frame"), ("interfaces", 1, "freshness"),
            ("interfaces", 1, "failure_behavior"),
            ("algorithm_plan", 0, "choice"),
            ("algorithm_plan", 0, "prerequisites"),
            ("hardware_functional_plan", 0, "performance_requirements"),
            ("hardware_functional_plan", 0, "degradation"),
            ("safety_plan", None, "fault_recovery"),
            ("verification_plan", None, "manual_safety_review"),
        )
        for section, index, field in paths:
            for replacement in ("missing", None, 42):
                with self.subTest(section=section, field=field, replacement=replacement):
                    package = copy.deepcopy(original)
                    item = package[section] if index is None else package[section][index]
                    if replacement == "missing":
                        item.pop(field)
                    else:
                        item[field] = replacement
                    self.assertTrue(validate_design_package(package, brief))

    def test_unknown_or_invalid_safety_bounds_block_package(self) -> None:
        brief = load_example("design-brief.json")
        package = load_example("design-package.json")
        for value in (None, "unknown", 0, -1, float("nan"), 0.7):
            with self.subTest(value=value):
                changed = copy.deepcopy(package)
                changed["safety_plan"]["max_linear_mps"] = value
                self.assertTrue(validate_design_package(changed, brief))
        brief["safety_context"]["speed_limit"] = "unknown"
        brief["blockers"] = ["speed_limit unknown pending review"]
        self.assertIn(
            "cannot finalize package with unknown safety_context.speed_limit",
            validate_design_package(package, brief),
        )
        brief["safety_context"]["speed_limit"] = "defined"
        brief["vehicle_constraints"]["maximum_speed_mps"] = "unknown"
        self.assertIn(
            "design brief maximum_speed_mps must be a known positive number",
            validate_design_package(package, brief),
        )

    def test_verification_and_trace_links_are_bidirectional(self) -> None:
        brief = load_example("design-brief.json")
        original = load_example("design-package.json")
        mutations = (
            lambda p: p["traceability"][0]["design_ids"].pop(),
            lambda p: p["traceability"][0]["test_ids"].pop(),
            lambda p: p["traceability"][0]["ros_interfaces"].pop(),
            lambda p: p["traceability"][0]["implementation"][0].update(symbol="missing"),
            lambda p: p["verification_plan"]["checks"][0].update(test_node="missing"),
            lambda p: p["verification_plan"]["checks"][0].update(acceptance=None),
            lambda p: p["verification_plan"]["checks"][0].update(evidence=None),
            lambda p: p["requirements"][0].update(source="/no/such/field"),
        )
        for mutate in mutations:
            with self.subTest(mutation=str(mutate)):
                package = copy.deepcopy(original)
                mutate(package)
                self.assertTrue(validate_design_package(package, brief))

    def test_junit_evidence_requires_every_passing_case(self) -> None:
        package = load_example("design-package.json")
        checks = [
            check for check in package["verification_plan"]["checks"]
            if check["status"] == "implemented"
        ]
        cases = "".join(
            f'<testcase classname="{Path(check["test_node"].split("::")[0]).stem}.'
            f'{check["test_node"].split("::")[-2]}" '
            f'name="{check["test_node"].split("::")[-1]}"/>'
            for check in checks
        )
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "pytest.xml"
            report.write_text(f"<testsuite>{cases}</testsuite>")
            self.assertEqual(validate_junit_evidence(package, report), [])
            report.write_text(
                '<testsuite><testcase classname="test_sim_graph.SimGraphTest" '
                'name="test_faults_stop_and_require_fresh_motion"/></testsuite>'
            )
            self.assertTrue(validate_junit_evidence(package, report))
            report.write_text(
                '<testsuite><testcase classname="test_sim_graph.SimGraphTest" '
                'name="test_faults_stop_and_require_fresh_motion">'
                '<failure/></testcase></testsuite>'
            )
            self.assertTrue(validate_junit_evidence(package, report))

    def test_unknown_safety_constraint_requires_a_blocker(self) -> None:
        brief = copy.deepcopy(load_example("design-brief.json"))
        brief["safety_context"]["emergency_stop"] = "unknown"

        errors = validate_design_brief(brief)

        self.assertIn("safety_context.emergency_stop is unknown without a blocker", errors)

    def test_package_rejects_hardware_model_fields(self) -> None:
        brief = load_example("design-brief.json")
        package = copy.deepcopy(load_example("design-package.json"))
        package["hardware_functional_plan"][0]["model"] = "example-model"

        errors = validate_design_package(package, brief)

        self.assertIn("hardware_functional_plan[0] must not contain model", errors)

    def test_package_rejects_confirmed_claim_without_evidence(self) -> None:
        brief = load_example("design-brief.json")
        package = copy.deepcopy(load_example("design-package.json"))
        package["assumptions"][0].pop("evidence")

        errors = validate_design_package(package, brief)

        self.assertIn("assumptions[0] confirmed claim requires evidence", errors)


if __name__ == "__main__":
    unittest.main()
