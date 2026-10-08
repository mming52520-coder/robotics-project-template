#!/usr/bin/env python3
"""Validate a ChangeContract's declared scope against the current candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .change_contracts import current_change_contract, validate_change_contract
except ImportError:
    from change_contracts import current_change_contract, validate_change_contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        contract = args.contract or current_change_contract()
    except ValueError as error:
        print(error)
        return 1
    document = json.loads(contract.read_text(encoding="utf-8"))
    if contract.parent.name != document.get("change_id"):
        print("change_id must match the contract directory")
        return 1
    errors = validate_change_contract(document)
    for error in errors:
        print(error)
    if errors:
        return 1
    print("change scope and design references validated; human approval not asserted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
