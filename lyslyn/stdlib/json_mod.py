"""JSON standard library module for Lyslyn."""
import json
from typing import Any, Dict
from ..values import LyslynBuiltin


def parse(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception as e:
        raise ValueError(f"JSON parse error: {e}")


def stringify(value: Any, indent: Any = None) -> str:
    try:
        if indent is not None and isinstance(indent, (int, float)):
            indent = int(indent)
        else:
            indent = None
        return json.dumps(value, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise ValueError(f"JSON stringify error: {e}")


def export_module() -> Dict[str, Any]:
    return {
        "parse": LyslynBuiltin("parse", parse, arity=1),
        "stringify": LyslynBuiltin("stringify", stringify),
    }
