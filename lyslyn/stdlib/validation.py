"""Request data validation module for Lyslyn."""
import re
from typing import Any, Dict, List, Tuple
from ..values import LyslynBuiltin

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_data(data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": [{"field": "_root", "issue": "Expected object/dictionary for validation"}]
        }

    errors: List[Dict[str, str]] = []

    for field, rule_spec in schema.items():
        rules = [r.strip().lower() for r in str(rule_spec).split("|")] if isinstance(rule_spec, str) else []
        if isinstance(rule_spec, str) and " " in rule_spec and "|" not in rule_spec:
            rules = [r.strip().lower() for r in rule_spec.split()]

        val = data.get(field, None)
        is_required = "required" in rules

        if val is None:
            if is_required:
                errors.append({"field": field, "issue": f"Field '{field}' is required"})
            continue

        if "string" in rules and not isinstance(val, str):
            errors.append({"field": field, "issue": f"Field '{field}' must be a string"})
            continue

        if "number" in rules and not isinstance(val, (int, float)):
            errors.append({"field": field, "issue": f"Field '{field}' must be a number"})
            continue

        if "boolean" in rules and not isinstance(val, bool):
            errors.append({"field": field, "issue": f"Field '{field}' must be a boolean"})
            continue

        if "list" in rules and not isinstance(val, list):
            errors.append({"field": field, "issue": f"Field '{field}' must be a list"})
            continue

        if "email" in rules:
            if not isinstance(val, str) or not EMAIL_REGEX.match(val):
                errors.append({"field": field, "issue": f"Field '{field}' must be a valid email address"})
                continue

        for r in rules:
            if r.startswith("min:"):
                try:
                    min_val = float(r.split(":", 1)[1])
                    if isinstance(val, (int, float)) and val < min_val:
                        errors.append({"field": field, "issue": f"Field '{field}' must be at least {min_val}"})
                    elif isinstance(val, (str, list)) and len(val) < min_val:
                        errors.append({"field": field, "issue": f"Field '{field}' length must be at least {int(min_val)}"})
                except ValueError:
                    pass
            elif r.startswith("max:"):
                try:
                    max_val = float(r.split(":", 1)[1])
                    if isinstance(val, (int, float)) and val > max_val:
                        errors.append({"field": field, "issue": f"Field '{field}' must be at most {max_val}"})
                    elif isinstance(val, (str, list)) and len(val) > max_val:
                        errors.append({"field": field, "issue": f"Field '{field}' length must be at most {int(max_val)}"})
                except ValueError:
                    pass

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def export_module() -> Dict[str, Any]:
    return {
        "validate": LyslynBuiltin("validate", validate_data, arity=2),
    }
