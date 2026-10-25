"""Runtime values and representations for Lyslyn."""
import json
from typing import Any, List, Dict, Callable, Optional


class LyslynControlFlow(Exception):
    """Base exception for control flow jumps."""
    pass


class ReturnSignal(LyslynControlFlow):
    def __init__(self, value: Any):
        self.value = value


class BreakSignal(LyslynControlFlow):
    pass


class ContinueSignal(LyslynControlFlow):
    pass


class LyslynFunction:
    """Represents a user-defined function with lexical closure."""
    def __init__(self, name: str, params: List[str], body: Any, closure: Any, is_async: bool = False):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure
        self.is_async = is_async

    def __call__(self, *args: Any) -> Any:
        # Will be called through interpreter
        pass

    def __repr__(self) -> str:
        return f"<function {self.name}({', '.join(self.params)})>"


class LyslynBuiltin:
    """Represents a host built-in function."""
    def __init__(self, name: str, func: Callable, arity: Optional[int] = None):
        self.name = name
        self.func = func
        self.arity = arity

    def call(self, args: List[Any], interpreter: Any = None) -> Any:
        if self.arity is not None and len(args) != self.arity:
            raise TypeError(f"Function '{self.name}' expects {self.arity} arguments, but got {len(args)}")
        return self.func(*args)

    def __repr__(self) -> str:
        return f"<built-in function {self.name}>"


class LyslynModule:
    """Represents an imported module namespace."""
    def __init__(self, name: str, exports: Dict[str, Any]):
        self.name = name
        self.exports = exports

    def get(self, name: str) -> Any:
        if name in self.exports:
            return self.exports[name]
        raise AttributeError(f"Module '{self.name}' has no export named '{name}'")

    def __repr__(self) -> str:
        return f"<module '{self.name}'>"


class LyslynHttpResponse:
    """Represents an HTTP response in Lyslyn."""
    def __init__(self, status: int, body: str, headers: Dict[str, str], url: str):
        self.status = status
        self.status_code = status
        self.body = body
        self.headers = headers
        self.url = url
        self.ok = 200 <= status < 400

    def json(self) -> Any:
        try:
            return json.loads(self.body)
        except Exception as e:
            raise ValueError(f"Failed to parse response body as JSON: {e}")

    def text(self) -> str:
        return self.body

    def get_property(self, prop: str) -> Any:
        if prop in ("status", "status_code"):
            return self.status
        if prop in ("body", "text"):
            return self.body
        if prop == "headers":
            return self.headers
        if prop == "url":
            return self.url
        if prop == "ok":
            return self.ok
        if prop == "json":
            return LyslynBuiltin("json", lambda: self.json(), arity=0)
        raise AttributeError(f"HTTP Response has no property '{prop}'")

    def __repr__(self) -> str:
        return f"<HttpResponse status={self.status} ok={self.ok}>"
