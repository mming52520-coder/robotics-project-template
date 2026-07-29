"""Contract tests for the public, model-free robot design package."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.design_contracts import validate_design_brief, validate_design_package


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "examples" / "warehouse-tote"


def load_example(name: str) -> dict[str, object]:
    return json.loads((EXAMPLE_DIR / name).read_text(encoding="utf-8"))


class DesignContractTests(unittest.TestCase):
    def test_example_brief_is_valid(self) -> None:
        self.assertEqual(validate_design_brief(load_example("design-brief.json")), [])

    def test_example_package_is_valid(self) -> None:
        brief = load_example("design-brief.json")
        package = load_example("design-package.json")
        self.assertEqual(validate_design_package(package, brief), [])

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
