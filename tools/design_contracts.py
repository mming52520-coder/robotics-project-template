"""Validation for public, model-free indoor mobile-robot design contracts."""

from __future__ import annotations

import ast
import json
import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

BRIEF_REQUIRED = (
    "schema_version", "brief_id", "mission", "operating_environment",
    "vehicle_constraints", "required_capabilities", "safety_context", "blockers",
)
PACKAGE_REQUIRED = (
    "schema_version", "brief_id", "assumptions", "requirements", "system_architecture",
    "interfaces", "algorithm_plan", "hardware_functional_plan", "safety_plan",
    "verification_plan", "traceability", "open_decisions",
)
MODEL_FREE_FIELDS = {"model", "vendor", "manufacturer", "part_number", "serial_number"}
ROOT = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")


def _schema_errors(document: object, name: str) -> list[str]:
    schema = json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    violations = Draft202012Validator(schema).iter_errors(document)
    return sorted(
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in violations
    )


def _mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _list(value: Any) -> bool:
    return isinstance(value, list)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and (
        math.isfinite(value) and value > 0
    )


def _required_errors(
    document: Mapping[str, Any], fields: tuple[str, ...], path: str = ""
) -> list[str]:
    return [
        f"missing required field: {path}{field}" for field in fields if field not in document
    ]


def _blocker_covers(blockers: list[Any], field_name: str) -> bool:
    return any(_nonempty_text(item) and field_name in item for item in blockers)


def validate_design_brief(brief: object) -> list[str]:
    """Return deterministic contract violations for a DesignBrief document."""
    if not _mapping(brief):
        return ["design brief must be an object"]
    errors = _required_errors(brief, BRIEF_REQUIRED)
    if errors:
        return errors
    if brief["schema_version"] != "v1":
        errors.append("schema_version must be v1")
    if not _nonempty_text(brief["brief_id"]):
        errors.append("brief_id must be non-empty")
    for name in ("mission", "operating_environment", "vehicle_constraints"):
        if not _mapping(brief[name]):
            errors.append(f"{name} must be an object")
    if not _list(brief["required_capabilities"]) or not brief["required_capabilities"]:
        errors.append("required_capabilities must be a non-empty list")
    if not _list(brief["blockers"]):
        errors.append("blockers must be a list")
        blockers: list[Any] = []
    else:
        blockers = brief["blockers"]

    safety_context = brief["safety_context"]
    if not _mapping(safety_context):
        return errors + ["safety_context must be an object"]
    for field_name in ("emergency_stop", "speed_limit", "physical_output"):
        if field_name not in safety_context:
            errors.append(f"missing required field: safety_context.{field_name}")
            continue
        if safety_context[field_name] == "unknown" and not _blocker_covers(blockers, field_name):
            errors.append(f"safety_context.{field_name} is unknown without a blocker")
    for field_name in ("emergency_stop", "speed_limit"):
        if safety_context.get(field_name) not in ("defined", "unknown"):
            errors.append(f"safety_context.{field_name} must be defined or unknown")
    if safety_context.get("physical_output") not in ("disabled", "unknown"):
        errors.append("safety_context.physical_output must be disabled or unknown")
    return errors


def _model_free_errors(value: object, path: str = "") -> list[str]:
    if _mapping(value):
        errors: list[str] = []
        for key, nested_value in value.items():
            key_text = str(key).lower()
            nested_path = f"{path}.{key}" if path else str(key)
            if key_text in MODEL_FREE_FIELDS:
                parent_path = nested_path.rsplit(".", 1)[0] if "." in nested_path else path
                errors.append(f"{parent_path} must not contain {key}")
            errors.extend(_model_free_errors(nested_value, nested_path))
        return errors
    if _list(value):
        return [
            error for index, nested in enumerate(value)
            for error in _model_free_errors(nested, f"{path}[{index}]")
        ]
    return []


def _text_fields(item: Mapping[str, Any], fields: tuple[str, ...], path: str) -> list[str]:
    return [
        f"{path}.{field} must be non-empty"
        for field in fields if not _nonempty_text(item.get(field))
    ]


def _text_list(value: object, path: str) -> list[str]:
    if not _list(value) or not value or any(not _nonempty_text(item) for item in value):
        return [f"{path} must be a non-empty list of non-empty strings"]
    if len(value) != len(set(value)):
        return [f"{path} must not contain duplicates"]
    return []


def _pointer(document: object, pointer: str) -> object | None:
    if not pointer.startswith("/"):
        return None
    current = document
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if _mapping(current) and token in current:
            current = current[token]
        elif _list(current) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return None
    return current


def _symbol_exists(path: Path, symbol: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    parts = symbol.split(".")
    nodes: list[ast.AST] = [tree]
    for part in parts:
        nodes = [
            child for node in nodes for child in getattr(node, "body", [])
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == part
        ]
    return bool(nodes)


def _test_node_exists(node_id: str, root: Path) -> bool:
    if not _nonempty_text(node_id):
        return False
    parts = node_id.split("::")
    if len(parts) < 2:
        return False
    path = (root / parts[0]).resolve()
    return path.is_relative_to(root) and path.is_file() and _symbol_exists(
        path, ".".join(parts[1:])
    )


def _trace_errors(
    package: Mapping[str, Any], requirements: dict[str, Mapping[str, Any]],
    design_links: dict[str, set[str]], interface_names: dict[str, str],
    checks: dict[str, Mapping[str, Any]], root: Path,
) -> list[str]:
    trace = package["traceability"]
    if not _list(trace):
        return ["traceability must be a list"]
    errors: list[str] = []
    seen: set[str] = set()
    traced_tests: set[str] = set()
    for index, row in enumerate(trace):
        path = f"traceability[{index}]"
        if not _mapping(row):
            errors.append(f"{path} must be an object")
            continue
        req_id = row.get("requirement_id")
        if not _nonempty_text(req_id) or req_id not in requirements:
            errors.append(f"{path}.requirement_id must name a requirement")
            continue
        if req_id in seen:
            errors.append(f"{path}.requirement_id must be unique")
        seen.add(req_id)
        if requirements[req_id].get("status") != "implemented":
            errors.append(f"{path}.requirement_id must be implemented")
        for field in ("design_ids", "test_ids", "ros_interfaces"):
            errors.extend(_text_list(row.get(field), f"{path}.{field}"))
        design_ids = row.get("design_ids")
        if _list(design_ids) and all(isinstance(item, str) for item in design_ids):
            expected = {key for key, links in design_links.items() if req_id in links}
            if set(design_ids) != expected:
                errors.append(f"{path}.design_ids must match all design links for {req_id}")
            expected_ros = {interface_names[key] for key in expected if key in interface_names}
            ros_interfaces = row.get("ros_interfaces")
            if (
                _list(ros_interfaces)
                and all(isinstance(item, str) for item in ros_interfaces)
                and set(ros_interfaces) != expected_ros
            ):
                errors.append(f"{path}.ros_interfaces must match linked ROS interfaces")
        test_ids = row.get("test_ids")
        if _list(test_ids):
            expected_tests = {
                key for key, item in checks.items()
                if item.get("status") == "implemented"
                and req_id in item.get("requirement_ids", [])
            }
            if all(isinstance(item, str) for item in test_ids) and set(test_ids) != expected_tests:
                errors.append(f"{path}.test_ids must match all implemented checks for {req_id}")
            for test_id in test_ids:
                if not isinstance(test_id, str) or test_id not in checks:
                    errors.append(f"{path}.test_ids contains an unknown check")
                elif req_id not in checks[test_id].get("requirement_ids", []):
                    errors.append(f"{path}.test_ids contains a check without {req_id}")
                else:
                    traced_tests.add(test_id)
        implementations = row.get("implementation")
        if not _list(implementations) or not implementations:
            errors.append(f"{path}.implementation must be a non-empty list")
        else:
            for offset, item in enumerate(implementations):
                item_path = f"{path}.implementation[{offset}]"
                if not _mapping(item):
                    errors.append(f"{item_path} must be an object")
                    continue
                errors.extend(_text_fields(item, ("file", "symbol"), item_path))
                file_name, symbol = item.get("file"), item.get("symbol")
                if _nonempty_text(file_name) and _nonempty_text(symbol):
                    file_path = (root / file_name).resolve()
                    if not file_path.is_relative_to(root) or not file_path.is_file():
                        errors.append(f"{item_path}.file must exist inside the repository")
                    elif not _symbol_exists(file_path, symbol):
                        errors.append(f"{item_path}.symbol must exist in the file")
        artifact = row.get("evidence_artifact")
        if not _nonempty_text(artifact):
            errors.append(f"{path}.evidence_artifact must be non-empty")
        elif _list(test_ids):
            for test_id in test_ids:
                if test_id in checks and checks[test_id].get("evidence") != artifact:
                    errors.append(f"{path}.evidence_artifact must match {test_id}")
    for req_id, item in requirements.items():
        if item.get("status") == "implemented" and req_id not in seen:
            errors.append(f"implemented requirement {req_id} needs traceability")
    for test_id, check in checks.items():
        if check.get("status") == "implemented" and test_id not in traced_tests:
            errors.append(f"implemented check {test_id} needs traceability")
    return errors


def validate_design_package(package: object, brief: object, root: Path = ROOT) -> list[str]:
    """Validate v2 structure, safety bounds, and both sides of implemented trace links."""
    brief_errors = validate_design_brief(brief)
    if brief_errors:
        return [f"invalid design brief: {error}" for error in brief_errors]
    if not _mapping(package):
        return ["design package must be an object"]
    if package.get("schema_version") != "v2":
        return ["schema_version must be v2"]
    schema_errors = _schema_errors(package, "design-package.schema.json")
    if schema_errors:
        return schema_errors
    errors = _required_errors(package, PACKAGE_REQUIRED)
    if errors:
        return errors
    if package["schema_version"] != "v2":
        errors.append("schema_version must be v2")
    if package["brief_id"] != brief["brief_id"]:
        errors.append("brief_id must match the design brief")
    for field in ("emergency_stop", "speed_limit", "physical_output"):
        if brief["safety_context"].get(field) == "unknown":
            errors.append(f"cannot finalize package with unknown safety_context.{field}")

    assumptions = package["assumptions"]
    if not _list(assumptions):
        errors.append("assumptions must be a list")
    else:
        for index, assumption in enumerate(assumptions):
            path = f"assumptions[{index}]"
            if not _mapping(assumption):
                errors.append(f"{path} must be an object")
                continue
            status = assumption.get("status")
            if status not in ("confirmed", "inferred", "open"):
                errors.append(f"{path}.status must be confirmed, inferred, or open")
            errors.extend(_text_fields(assumption, ("statement",), path))
            if status == "confirmed" and not _nonempty_text(assumption.get("evidence")):
                errors.append(f"{path} confirmed claim requires evidence")

    architecture = package["system_architecture"]
    if not _mapping(architecture):
        errors.append("system_architecture must be an object")
    else:
        if architecture.get("reference") != "ros2":
            errors.append("system_architecture.reference must be ros2")
        components = architecture.get("components")
        if not _list(components) or not components:
            errors.append("system_architecture.components must be a non-empty list")
        else:
            for index, item in enumerate(components):
                if not _mapping(item):
                    errors.append(f"system_architecture.components[{index}] must be an object")
                else:
                    errors.extend(_text_fields(
                        item, ("name", "responsibility"), f"system_architecture.components[{index}]"
                    ))

    requirements: dict[str, Mapping[str, Any]] = {}
    items = package["requirements"]
    if not _list(items) or not items:
        errors.append("requirements must be a non-empty list")
    else:
        for index, item in enumerate(items):
            path = f"requirements[{index}]"
            if not _mapping(item):
                errors.append(f"{path} must be an object")
                continue
            errors.extend(_text_fields(
                item, ("id", "source", "statement", "scope", "acceptance"), path
            ))
            req_id = item.get("id")
            if _nonempty_text(req_id):
                if not ID_PATTERN.fullmatch(req_id):
                    errors.append(f"{path}.id has invalid format")
                if req_id in requirements:
                    errors.append(f"{path}.id must be unique")
                requirements[req_id] = item
            if item.get("status") not in ("planned", "implemented"):
                errors.append(f"{path}.status must be planned or implemented")
            source = item.get("source")
            source_value = _pointer(brief, source) if _nonempty_text(source) else None
            if not (_nonempty_text(source_value) or _positive_number(source_value)):
                errors.append(f"{path}.source must point to a populated DesignBrief value")

    design_links: dict[str, set[str]] = {}
    interface_names: dict[str, str] = {}
    section_fields = {
        "interfaces": ("id", "name", "owner", "producer", "consumer", "data", "units",
                       "frame", "freshness", "failure_behavior"),
        "algorithm_plan": ("id", "function", "choice", "rationale", "failure_behavior"),
        "hardware_functional_plan": ("id", "function", "interface", "degradation"),
    }
    for section, fields in section_fields.items():
        entries = package[section]
        if not _list(entries) or not entries:
            errors.append(f"{section} must be a non-empty list")
            continue
        for index, item in enumerate(entries):
            path = f"{section}[{index}]"
            if not _mapping(item):
                errors.append(f"{path} must be an object")
                continue
            errors.extend(_text_fields(item, fields, path))
            if section == "algorithm_plan":
                errors.extend(_text_list(item.get("prerequisites"), f"{path}.prerequisites"))
            if section == "hardware_functional_plan":
                for field in ("performance_requirements", "environmental_requirements"):
                    errors.extend(_text_list(item.get(field), f"{path}.{field}"))
            item_id = item.get("id")
            if _nonempty_text(item_id):
                if not ID_PATTERN.fullmatch(item_id):
                    errors.append(f"{path}.id has invalid format")
                if item_id in design_links:
                    errors.append(f"{path}.id must be unique")
                design_links[item_id] = set()
                if section == "interfaces" and _nonempty_text(item.get("ros_name")):
                    interface_names[item_id] = item["ros_name"]
            errors.extend(_text_list(item.get("requirement_ids"), f"{path}.requirement_ids"))
            if _list(item.get("requirement_ids")):
                for req_id in item["requirement_ids"]:
                    if req_id not in requirements:
                        errors.append(f"{path}.requirement_ids contains an unknown requirement")
                    elif _nonempty_text(item_id):
                        design_links[item_id].add(req_id)

    safety = package["safety_plan"]
    if not _mapping(safety):
        errors.append("safety_plan must be an object")
    else:
        errors.extend(_text_fields(
            safety, ("id", "control_authority", "stop_behavior", "watchdog",
                     "fault_recovery"), "safety_plan"
        ))
        if safety.get("physical_output") != "disabled_by_default":
            errors.append("safety_plan.physical_output must be disabled_by_default")
        for field in ("max_linear_mps", "max_angular_radps", "command_timeout_s",
                      "status_timeout_s"):
            if not _positive_number(safety.get(field)):
                errors.append(f"safety_plan.{field} must be a finite positive number")
        max_brief = brief["vehicle_constraints"].get("maximum_speed_mps") if _mapping(
            brief["vehicle_constraints"]
        ) else None
        if not _positive_number(max_brief):
            errors.append("design brief maximum_speed_mps must be a known positive number")
        elif _positive_number(safety.get("max_linear_mps")) and (
            safety["max_linear_mps"] > max_brief
        ):
            errors.append("safety_plan.max_linear_mps exceeds design brief limit")
        errors.extend(_text_list(safety.get("requirement_ids"), "safety_plan.requirement_ids"))
        safety_id = safety.get("id")
        if _nonempty_text(safety_id):
            if not ID_PATTERN.fullmatch(safety_id):
                errors.append("safety_plan.id has invalid format")
            if safety_id in design_links:
                errors.append("safety_plan.id must be unique")
            design_links[safety_id] = set()
            if _list(safety.get("requirement_ids")):
                for req_id in safety["requirement_ids"]:
                    if req_id not in requirements:
                        errors.append("safety_plan.requirement_ids contains an unknown requirement")
                    else:
                        design_links[safety_id].add(req_id)

    verification = package["verification_plan"]
    checks: dict[str, Mapping[str, Any]] = {}
    if not _mapping(verification):
        errors.append("verification_plan must be an object")
    else:
        errors.extend(_text_fields(
            verification, ("unit", "integration", "simulation", "replay",
                           "manual_safety_review"), "verification_plan"
        ))
        entries = verification.get("checks")
        if not _list(entries) or not entries:
            errors.append("verification_plan.checks must be a non-empty list")
        else:
            for index, item in enumerate(entries):
                path = f"verification_plan.checks[{index}]"
                if not _mapping(item):
                    errors.append(f"{path} must be an object")
                    continue
                errors.extend(_text_fields(
                    item, ("id", "level", "preconditions", "scenario", "acceptance", "evidence"),
                    path,
                ))
                if item.get("status") not in ("planned", "implemented"):
                    errors.append(f"{path}.status must be planned or implemented")
                errors.extend(_text_list(item.get("requirement_ids"), f"{path}.requirement_ids"))
                check_id = item.get("id")
                if _nonempty_text(check_id):
                    if not ID_PATTERN.fullmatch(check_id):
                        errors.append(f"{path}.id has invalid format")
                    if check_id in checks:
                        errors.append(f"{path}.id must be unique")
                    checks[check_id] = item
                if _list(item.get("requirement_ids")):
                    for req_id in item["requirement_ids"]:
                        if req_id not in requirements:
                            errors.append(f"{path}.requirement_ids contains an unknown requirement")
                if item.get("status") == "implemented" and not _test_node_exists(
                    item.get("test_node", ""), root
                ):
                    errors.append(f"{path}.test_node must name an existing test")

    if not _list(package["open_decisions"]):
        errors.append("open_decisions must be a list")
    else:
        decision_ids: set[str] = set()
        for index, item in enumerate(package["open_decisions"]):
            path = f"open_decisions[{index}]"
            if not _mapping(item):
                errors.append(f"{path} must be an object")
                continue
            errors.extend(_text_fields(item, ("id", "statement", "closure_evidence"), path))
            decision_id = item.get("id")
            if _nonempty_text(decision_id):
                if decision_id in decision_ids:
                    errors.append(f"{path}.id must be unique")
                decision_ids.add(decision_id)
            errors.extend(_text_list(item.get("requirement_ids"), f"{path}.requirement_ids"))
            for req_id in item.get("requirement_ids", []):
                if req_id not in requirements:
                    errors.append(f"{path}.requirement_ids contains an unknown requirement")
                elif item.get("blocks_implementation") and (
                    requirements[req_id].get("status") == "implemented"
                ):
                    errors.append(f"{path} blocks implemented requirement {req_id}")
    errors.extend(_model_free_errors(package["hardware_functional_plan"],
                                     "hardware_functional_plan"))
    for req_id in requirements:
        if not any(req_id in links for links in design_links.values()):
            errors.append(f"requirement {req_id} needs a design link")
        if not any(req_id in check.get("requirement_ids", []) for check in checks.values()):
            errors.append(f"requirement {req_id} needs a verification check")
    errors.extend(_trace_errors(package, requirements, design_links, interface_names, checks, root))
    return errors


def validate_legacy_design_package(package: object, brief: object) -> list[str]:
    """Validate v1 only as a design artifact, never as implementation evidence."""
    brief_errors = validate_design_brief(brief)
    if brief_errors:
        return [f"invalid design brief: {error}" for error in brief_errors]
    if not _mapping(package) or package.get("schema_version") != "v1":
        return ["legacy design package must be a v1 object"]
    errors = _schema_errors(package, "design-package.v1.schema.json")
    if package.get("brief_id") != brief["brief_id"]:
        errors.append("brief_id must match the design brief")
    safety = package.get("safety_plan")
    if _mapping(safety):
        if safety.get("physical_output") != "disabled_by_default":
            errors.append("safety_plan.physical_output must be disabled_by_default")
        errors.extend(_text_fields(
            safety, ("control_authority", "stop_behavior", "watchdog", "fault_recovery"),
            "safety_plan",
        ))
    errors.extend(_model_free_errors(package.get("hardware_functional_plan"),
                                     "hardware_functional_plan"))
    return errors


def validate_junit_evidence(package: object, report: Path) -> list[str]:
    """Confirm every implemented check has a passing JUnit case in the named artifact."""
    if not _mapping(package) or not _mapping(package.get("verification_plan")):
        return ["invalid package for JUnit evidence"]
    if not report.is_file():
        return [f"missing JUnit evidence: {report}"]
    try:
        cases = list(ET.parse(report).iter("testcase"))
    except ET.ParseError as error:
        return [f"invalid JUnit evidence: {error}"]
    errors: list[str] = []
    for check in package["verification_plan"].get("checks", []):
        if not _mapping(check) or check.get("status") != "implemented":
            continue
        node = check.get("test_node", "")
        parts = node.split("::")
        if len(parts) < 3:
            errors.append(f"{check.get('id')}: invalid test node")
            continue
        class_name = f"{Path(parts[0]).stem}.{parts[-2]}"
        matches = [
            case for case in cases
            if case.get("classname", "").endswith(class_name)
            and case.get("name") == parts[-1]
        ]
        if len(matches) != 1 or any(
            matches[0].find(tag) is not None for tag in ("failure", "error", "skipped")
        ):
            errors.append(f"{check.get('id')}: no passing JUnit case")
    return errors
