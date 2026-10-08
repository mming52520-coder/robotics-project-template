"""ChangeContract scope and trust-boundary regressions."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.change_contracts import (
    changed_paths,
    trusted_candidate_base,
    validate_change_contract,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "changes/ai-delivery-chain/change.json"


class ChangeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(CONTRACT.read_text(encoding="utf-8"))
        design = ROOT / self.document["design_package_ref"]
        self.document["design_package_sha256"] = hashlib.sha256(design.read_bytes()).hexdigest()
        self.document["base_revision"] = trusted_candidate_base(ROOT)

    def validate_fixture(
        self, document: dict[str, object], phase: str = "final",
        paths: set[str] | None = None,
    ) -> list[str]:
        with patch("tools.change_contracts.changed_paths", return_value=paths or set()):
            return validate_change_contract(document, ROOT, phase=phase)

    def test_valid_fixture(self) -> None:
        self.assertEqual(self.validate_fixture(self.document), [])

    def test_digest_and_scope_changes_fail(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["design_package_sha256"] = "0" * 64
        self.assertIn(
            "design_package_sha256 does not match the referenced file",
            self.validate_fixture(changed),
        )
        self.assertIn(
            "changed path outside allowed_paths: unrelated.py",
            self.validate_fixture(self.document, paths={"unrelated.py"}),
        )

    def test_contract_cannot_choose_a_shorter_base(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["base_revision"] = "0" * 40
        changed["allowed_paths"] = ["nothing/*"]
        self.assertIn(
            "base_revision must match the trusted candidate merge-base",
            self.validate_fixture(changed),
        )

    def test_missing_test_or_fake_approval_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["required_test_ids"] = ["T-SIM-START"]
        errors = self.validate_fixture(changed)
        self.assertTrue(any("needs a required executable test" in error for error in errors))
        changed = copy.deepcopy(self.document)
        changed["approved"] = True
        self.assertTrue(self.validate_fixture(changed))

    def test_scope_includes_dirty_tracked_files(self) -> None:
        with patch("tools.change_contracts._git", side_effect=[
            "contracts/change-contract.schema.json",
            "src/robotics_sim/core.py",
            "scratch/extra.py",
        ]):
            self.assertEqual(changed_paths("a" * 40, ROOT), {
                "contracts/change-contract.schema.json",
                "src/robotics_sim/core.py",
                "scratch/extra.py",
            })

    def test_planned_feature_can_start_but_cannot_pass_final_gate(self) -> None:
        contract = copy.deepcopy(self.document)
        contract["affected_requirement_ids"] = ["REQ-PLAN-LOCALIZE"]
        contract["required_test_ids"] = ["T-PLAN-LOCALIZE"]
        self.assertEqual(self.validate_fixture(contract, phase="plan"), [])
        errors = self.validate_fixture(contract, phase="final")
        self.assertIn("affected requirement REQ-PLAN-LOCALIZE is not implemented", errors)
        self.assertIn("required test T-PLAN-LOCALIZE is only planned", errors)
        contract["required_test_ids"] = ["T-PLAN-NAV"]
        self.assertTrue(any(
            "needs a required test link" in error
            for error in self.validate_fixture(contract, phase="plan")
        ))


if __name__ == "__main__":
    unittest.main()
