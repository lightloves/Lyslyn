"""Math module for Lyslyn."""
import math
from typing import Any, Dict
from ..values import LyslynBuiltin


def export_module() -> Dict[str, Any]:
    return {
        "pi": math.pi,
        "e": math.e,
        "round": LyslynBuiltin("round", lambda x, n=0: round(x, n)),
        "floor": LyslynBuiltin("floor", lambda x: math.floor(x), arity=1),
        "ceil": LyslynBuiltin("ceil", lambda x: math.ceil(x), arity=1),
        "abs": LyslynBuiltin("abs", lambda x: abs(x), arity=1),
        "sqrt": LyslynBuiltin("sqrt", lambda x: math.sqrt(x), arity=1),
        "min": LyslynBuiltin("min", lambda *args: min(*args) if len(args) > 1 else min(args[0])),
        "max": LyslynBuiltin("max", lambda *args: max(*args) if len(args) > 1 else max(args[0])),
        "pow": LyslynBuiltin("pow", lambda x, y: math.pow(x, y), arity=2),
        "sin": LyslynBuiltin("sin", lambda x: math.sin(x), arity=1),
        "cos": LyslynBuiltin("cos", lambda x: math.cos(x), arity=1),
        "tan": LyslynBuiltin("tan", lambda x: math.tan(x), arity=1),
    }
