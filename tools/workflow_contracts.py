"""Validate the repository's small, non-robot workflow requirement catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .design_contracts import ID_PATTERN, _symbol_exists, _test_node_exists
except ImportError:
    from design_contracts import ID_PATTERN, _symbol_exists, _test_node_exists

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("contracts/workflow-requirements.json")
UNIT_RESULTS = "build/unit/test-results.json"


def load_catalog(root: Path = ROOT) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return checked requirement/test maps; fail closed on broken reverse links."""
    data = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "requirements", "tests"}:
        raise ValueError("workflow catalog must have schema_version, requirements, and tests")
    if (
        data["schema_version"] != "v1"
        or not isinstance(data["requirements"], list)
        or not isinstance(data["tests"], list)
    ):
        raise ValueError("invalid workflow catalog version or collections")
    requirements: dict[str, dict[str, Any]] = {}
    checks: dict[str, dict[str, Any]] = {}
    for item in data["requirements"]:
        if not isinstance(item, dict) or set(item) != {
            "id",
            "statement",
            "acceptance",
            "implementation",
            "test_ids",
        }:
            raise ValueError("invalid workflow requirement fields")
        identifier = item["id"]
        if (
            not isinstance(identifier, str)
            or not ID_PATTERN.fullmatch(identifier)
            or identifier in requirements
        ):
            raise ValueError("duplicate or invalid workflow requirement ID")
        if any(
            not isinstance(item[field], str) or not item[field].strip()
            for field in ("statement", "acceptance")
        ):
            raise ValueError(f"workflow requirement {identifier} needs text")
        if not isinstance(item["implementation"], list) or not item["implementation"]:
            raise ValueError(f"workflow requirement {identifier} needs implementation")
        for ref in item["implementation"]:
            if not isinstance(ref, dict) or set(ref) != {"file", "symbol"}:
                raise ValueError(f"workflow requirement {identifier} has an invalid implementation")
            source = (root / str(ref["file"])).resolve()
            if (
                not source.is_relative_to(root.resolve())
                or not source.is_file()
                or not _symbol_exists(source, str(ref["symbol"]))
            ):
                raise ValueError(f"workflow requirement {identifier} implementation does not exist")
        if not isinstance(item["test_ids"], list) or not item["test_ids"]:
            raise ValueError(f"workflow requirement {identifier} needs tests")
        requirements[identifier] = item
    for item in data["tests"]:
        if not isinstance(item, dict) or set(item) != {
            "id",
            "requirement_ids",
            "test_node",
            "evidence_artifact",
        }:
            raise ValueError("invalid workflow test fields")
        identifier = item["id"]
        if (
            not isinstance(identifier, str)
            or not ID_PATTERN.fullmatch(identifier)
            or identifier in checks
        ):
            raise ValueError("duplicate or invalid workflow test ID")
        node = item["test_node"]
        if (
            not isinstance(node, str)
            or not node.startswith("tests/unit/")
            or not _test_node_exists(node, root)
            or item["evidence_artifact"] != UNIT_RESULTS
        ):
            raise ValueError(
                f"workflow test {identifier} needs a discovered unit node and artifact"
            )
        ids = item["requirement_ids"]
        if not isinstance(ids, list) or not ids or any(req not in requirements for req in ids):
            raise ValueError(f"workflow test {identifier} has unknown requirements")
        checks[identifier] = item
    for req_id, item in requirements.items():
        ids = item["test_ids"]
        if (
            len(ids) != len(set(ids))
            or any(test_id not in checks for test_id in ids)
            or set(ids)
            != {test_id for test_id, check in checks.items() if req_id in check["requirement_ids"]}
        ):
            raise ValueError(f"workflow requirement {req_id} has incomplete test links")
    return requirements, checks
