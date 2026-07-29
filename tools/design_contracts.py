"""Validation for public, model-free indoor mobile-robot design contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


BRIEF_REQUIRED = (
    "schema_version",
    "brief_id",
    "mission",
    "operating_environment",
    "vehicle_constraints",
    "required_capabilities",
    "safety_context",
    "blockers",
)
PACKAGE_REQUIRED = (
    "schema_version",
    "brief_id",
    "assumptions",
    "system_architecture",
    "interfaces",
    "algorithm_plan",
    "hardware_functional_plan",
    "safety_plan",
    "verification_plan",
    "open_decisions",
)
MODEL_FREE_FIELDS = {"model", "vendor", "manufacturer", "part_number", "serial_number"}


def _mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _list(value: Any) -> bool:
    return isinstance(value, list)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _required_errors(document: Mapping[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [f"missing required field: {field}" for field in fields if field not in document]


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
    if not _mapping(brief["mission"]):
        errors.append("mission must be an object")
    if not _mapping(brief["operating_environment"]):
        errors.append("operating_environment must be an object")
    if not _mapping(brief["vehicle_constraints"]):
        errors.append("vehicle_constraints must be an object")
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
    if safety_context.get("physical_output") not in {"disabled", "unknown"}:
        errors.append("safety_context.physical_output must be disabled or unknown")
    return errors


def _model_free_errors(value: object, path: str = "") -> list[str]:
    if _mapping(value):
        errors: list[str] = []
        for key, nested_value in value.items():
            key_text = str(key).lower()
            nested_path = f"{path}.{key}" if path else str(key)
            if key_text in MODEL_FREE_FIELDS:
                errors.append(f"{nested_path.rsplit('.', 1)[0] if '.' in nested_path else path} must not contain {key}")
            errors.extend(_model_free_errors(nested_value, nested_path))
        return errors
    if _list(value):
        errors = []
        for index, nested_value in enumerate(value):
            errors.extend(_model_free_errors(nested_value, f"{path}[{index}]"))
        return errors
    return []


def _section_errors(section: object, name: str) -> list[str]:
    if not _list(section) or not section:
        return [f"{name} must be a non-empty list"]
    return []


def validate_design_package(package: object, brief: object) -> list[str]:
    """Return deterministic contract violations for a DesignPackage document."""
    brief_errors = validate_design_brief(brief)
    if brief_errors:
        return [f"invalid design brief: {error}" for error in brief_errors]
    if not _mapping(package):
        return ["design package must be an object"]

    errors = _required_errors(package, PACKAGE_REQUIRED)
    if errors:
        return errors
    if package["schema_version"] != "v1":
        errors.append("schema_version must be v1")
    if package["brief_id"] != brief["brief_id"]:
        errors.append("brief_id must match the design brief")

    assumptions = package["assumptions"]
    if not _list(assumptions):
        errors.append("assumptions must be a list")
    else:
        for index, assumption in enumerate(assumptions):
            if not _mapping(assumption):
                errors.append(f"assumptions[{index}] must be an object")
                continue
            status = assumption.get("status")
            if status not in {"confirmed", "inferred", "open"}:
                errors.append(f"assumptions[{index}].status must be confirmed, inferred, or open")
            if not _nonempty_text(assumption.get("statement")):
                errors.append(f"assumptions[{index}].statement must be non-empty")
            if status == "confirmed" and not _nonempty_text(assumption.get("evidence")):
                errors.append(f"assumptions[{index}] confirmed claim requires evidence")

    architecture = package["system_architecture"]
    if not _mapping(architecture):
        errors.append("system_architecture must be an object")
    elif architecture.get("reference") != "ros2":
        errors.append("system_architecture.reference must be ros2")

    for section in ("interfaces", "algorithm_plan", "hardware_functional_plan"):
        errors.extend(_section_errors(package[section], section))
    for section in ("safety_plan", "verification_plan"):
        if not _mapping(package[section]):
            errors.append(f"{section} must be an object")
    if not _list(package["open_decisions"]):
        errors.append("open_decisions must be a list")

    errors.extend(_model_free_errors(package["hardware_functional_plan"], "hardware_functional_plan"))
    safety_plan = package["safety_plan"]
    if _mapping(safety_plan):
        if safety_plan.get("physical_output") != "disabled_by_default":
            errors.append("safety_plan.physical_output must be disabled_by_default")
        for field_name in ("control_authority", "stop_behavior", "watchdog", "fault_recovery"):
            if not _nonempty_text(safety_plan.get(field_name)):
                errors.append(f"safety_plan.{field_name} must be non-empty")
    return errors
