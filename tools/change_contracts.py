"""Check a bounded change declaration against the design and actual Git diff."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from .design_contracts import validate_design_package
except ImportError:
    from design_contracts import validate_design_package

ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str, root: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _inside(root: Path, name: str) -> Path | None:
    if not name or Path(name).is_absolute():
        return None
    path = (root / name).resolve()
    return path if path.is_relative_to(root.resolve()) else None


def changed_paths(base: str, root: Path = ROOT) -> set[str]:
    """Include committed, staged, unstaged, and untracked candidate inputs."""
    head = os.environ.get("PR_HEAD_SHA") or "HEAD"
    tracked = _git("diff", "--name-only", base, head, "--", root=root).splitlines()
    dirty_tracked = _git("diff", "--name-only", "HEAD", "--", root=root).splitlines()
    untracked = _git("ls-files", "--others", "--exclude-standard", root=root).splitlines()
    return set(tracked + dirty_tracked + untracked)


def trusted_candidate_base(root: Path = ROOT) -> str:
    """Use the event base or tracked main, never a base chosen by the contract."""
    base_ref = os.environ.get("BASE_SHA") or "origin/main"
    head_ref = os.environ.get("PR_HEAD_SHA") or "HEAD"
    return _git("merge-base", head_ref, base_ref, root=root)


def current_change_contract(root: Path = ROOT) -> Path:
    """Find the one contract changed by this candidate, not a prior merged contract."""
    base = trusted_candidate_base(root)
    paths = changed_paths(base, root)
    candidates = sorted(
        path for path in paths if re.fullmatch(r"changes/[^/]+/change\.json", path)
    )
    if len(candidates) != 1:
        raise ValueError(f"expected one changed ChangeContract, found {len(candidates)}")
    return root / candidates[0]


def validate_change_contract(
    document: object, root: Path = ROOT, phase: str = "final"
) -> list[str]:
    """Check a proposed or completed change without asserting human approval."""
    if phase not in {"plan", "final"}:
        raise ValueError("phase must be plan or final")
    schema = json.loads((root / "contracts/change-contract.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    violations = list(Draft202012Validator(schema).iter_errors(document))
    if violations:
        return sorted(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: "
            f"{error.message}" for error in violations
        )
    assert isinstance(document, dict)
    errors: list[str] = []
    design_path = _inside(root, document["design_package_ref"])
    if design_path is None or not design_path.is_file():
        return ["design_package_ref must name a repository file"]
    digest = hashlib.sha256(design_path.read_bytes()).hexdigest()
    if digest != document["design_package_sha256"]:
        errors.append("design_package_sha256 does not match the referenced file")
    brief_path = design_path.with_name("design-brief.json")
    if not brief_path.is_file():
        return errors + ["referenced design package needs its sibling DesignBrief"]
    package: Any = json.loads(design_path.read_text(encoding="utf-8"))
    brief: Any = json.loads(brief_path.read_text(encoding="utf-8"))
    errors.extend(validate_design_package(package, brief, root))
    if errors:
        return errors
    requirements = {item["id"]: item for item in package["requirements"]}
    checks = {item["id"]: item for item in package["verification_plan"]["checks"]}
    affected = set(document["affected_requirement_ids"])
    required = set(document["required_test_ids"])
    for req_id in affected - requirements.keys():
        errors.append(f"unknown affected requirement: {req_id}")
    for test_id in required - checks.keys():
        errors.append(f"unknown required test: {test_id}")
    for req_id in affected & requirements.keys():
        linked = {
            test_id for test_id in required & checks.keys()
            if req_id in checks[test_id]["requirement_ids"]
        }
        if not linked:
            errors.append(f"affected requirement {req_id} needs a required test link")
        if phase == "final" and requirements[req_id]["status"] != "implemented":
            errors.append(f"affected requirement {req_id} is not implemented")
        if requirements[req_id]["status"] == "implemented" and not any(
            checks[test_id]["status"] == "implemented" for test_id in linked
        ):
            errors.append(f"implemented requirement {req_id} needs a required executable test")
    for test_id in required & checks.keys():
        if phase == "final" and checks[test_id]["status"] != "implemented":
            errors.append(f"required test {test_id} is only planned")
        if not affected.intersection(checks[test_id]["requirement_ids"]):
            errors.append(f"required test {test_id} does not cover affected requirements")
    patterns = document["allowed_paths"]
    for pattern in patterns:
        if (
            pattern in {"*", "**", "**/*"} or Path(pattern).is_absolute()
            or ".." in Path(pattern).parts
        ):
            errors.append(f"unsafe allowed_paths pattern: {pattern}")
    if errors:
        return errors
    base = trusted_candidate_base(root)
    main_push = (
        os.environ.get("GITHUB_EVENT_NAME") == "push"
        and os.environ.get("GITHUB_REF") == "refs/heads/main"
    )
    if main_push:
        # A PR may have forked before the previous main tip. The scope below
        # still uses the trusted push event base, never the declared base.
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", document["base_revision"], base],
            cwd=root, capture_output=True, check=False,
        ).returncode != 0:
            return ["base_revision must precede the trusted main push base"]
    elif document["base_revision"] != base:
        return ["base_revision must match the trusted candidate merge-base"]
    for path in sorted(changed_paths(base, root)):
        if not any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns):
            errors.append(f"changed path outside allowed_paths: {path}")
    return errors
