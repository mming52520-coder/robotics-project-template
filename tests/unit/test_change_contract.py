"""ChangeContract scope and trust-boundary regressions."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.change_contracts import changed_paths, validate_change_contract

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "changes/ai-delivery-chain/change.json"


class ChangeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_current_scope_matches_candidate(self) -> None:
        self.assertEqual(validate_change_contract(self.document, ROOT), [])

    def test_digest_and_scope_changes_fail(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["design_package_sha256"] = "0" * 64
        self.assertIn(
            "design_package_sha256 does not match the referenced file",
            validate_change_contract(changed, ROOT),
        )
        with patch(
            "tools.change_contracts.changed_paths", return_value={"src/robotics_sim/core.py"}
        ):
            self.assertIn(
                "changed path outside allowed_paths: src/robotics_sim/core.py",
                validate_change_contract(self.document, ROOT),
            )

    def test_missing_test_or_fake_approval_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["required_test_ids"] = ["T-SIM-START"]
        errors = validate_change_contract(changed, ROOT)
        self.assertTrue(any("needs a required executable test" in error for error in errors))
        changed = copy.deepcopy(self.document)
        changed["approved"] = True
        self.assertTrue(validate_change_contract(changed, ROOT))

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


if __name__ == "__main__":
    unittest.main()
