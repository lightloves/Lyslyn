"""Environment and scoping for Lyslyn runtime."""
from typing import Dict, Any, Optional, Set


class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: Dict[str, Any] = {}
        self.constants: Set[str] = set()

    def define(self, name: str, value: Any, is_constant: bool = False) -> None:
        """Define a new variable or constant in current scope."""
        if name in self.constants:
            raise RuntimeError(f"Cannot redefine constant '{name}'")
        self.values[name] = value
        if is_constant:
            self.constants.add(name)

    def assign(self, name: str, value: Any) -> None:
        """Assign to an existing variable in this or an enclosing scope."""
        if name in self.values:
            if name in self.constants:
                raise RuntimeError(f"Cannot reassign constant '{name}'")
            self.values[name] = value
            return

        if self.parent is not None:
            self.parent.assign(name, value)
            return

        # If not found in any scope, define in current scope
        self.values[name] = value

    def get(self, name: str) -> Any:
        """Look up variable in this or enclosing scope."""
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(name)

        raise NameError(f"Undefined variable '{name}'")

    def contains(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False
