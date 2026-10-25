"""Text and string manipulation module for Lyslyn."""
from typing import Any, Dict, List
from ..values import LyslynBuiltin


def trim(s: str) -> str:
    return str(s).strip()


def uppercase(s: str) -> str:
    return str(s).upper()


def lowercase(s: str) -> str:
    return str(s).lower()


def split(s: str, sep: str = " ") -> List[str]:
    if sep == "":
        return list(str(s))
    return str(s).split(sep)


def join(items: List[Any], sep: str = "") -> str:
    return str(sep).join(str(x) for x in items)


def replace(s: str, old: str, new: str) -> str:
    return str(s).replace(str(old), str(new))


def starts_with(s: str, prefix: str) -> bool:
    return str(s).startswith(str(prefix))


def ends_with(s: str, suffix: str) -> bool:
    return str(s).endswith(str(suffix))


def contains(s: str, sub: str) -> bool:
    return str(sub) in str(s)


def length(s: Any) -> int:
    return len(s)


def export_module() -> Dict[str, Any]:
    return {
        "trim": LyslynBuiltin("trim", trim, arity=1),
        "uppercase": LyslynBuiltin("uppercase", uppercase, arity=1),
        "lowercase": LyslynBuiltin("lowercase", lowercase, arity=1),
        "split": LyslynBuiltin("split", split),
        "join": LyslynBuiltin("join", join),
        "replace": LyslynBuiltin("replace", replace, arity=3),
        "starts_with": LyslynBuiltin("starts_with", starts_with, arity=2),
        "ends_with": LyslynBuiltin("ends_with", ends_with, arity=2),
        "contains": LyslynBuiltin("contains", contains, arity=2),
        "length": LyslynBuiltin("length", length, arity=1),
    }
