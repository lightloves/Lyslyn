"""Zero-dependency Single-File Bundler for Lyslyn.

Inlines all local file imports and dependencies into a single,
self-contained .lys distribution file for easy server deployment.
"""
import os
import re
from typing import Set, List, Dict, Tuple
from .lexer import Lexer
from .parser import Parser
from .ast_nodes import FunctionStmt, SetStmt


class Bundler:
    """Recursively resolves and inlines local Lyslyn modules into a single bundle."""
    def __init__(self, entry_file: str):
        self.entry_file = os.path.abspath(entry_file)
        self.base_dir = os.path.dirname(self.entry_file)
        self.visited_files: Set[str] = set()
        self.module_order: List[str] = []
        self.aliases: Dict[str, Set[str]] = {}

    def _extract_local_imports(self, filepath: str) -> List[Tuple[str, str, List[str]]]:
        """Find local file imports in a .lys file."""
        local_imports: List[Tuple[str, str, List[str]]] = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return []

        pattern = re.compile(
            r'^\s*(?:Import\s+["\']([^"\']+)["\'](?:\s+as\s+(\w+))?|From\s+["\']([^"\']+)["\']\s+import\s+([^\n]+))',
            re.MULTILINE
        )
        for m in pattern.finditer(content):
            if m.group(1):
                mod_path = m.group(1)
                default_name = os.path.basename(mod_path).replace(".lys", "")
                alias = m.group(2) or default_name
                local_imports.append((mod_path, alias, []))
            elif m.group(3):
                mod_path = m.group(3)
                default_name = os.path.basename(mod_path).replace(".lys", "")
                names = [n.strip() for n in m.group(4).split(",") if n.strip()]
                local_imports.append((mod_path, default_name, names))

        return local_imports

    def _resolve_path(self, current_dir: str, rel_path: str) -> str:
        candidates = [
            os.path.normpath(os.path.join(current_dir, rel_path)),
            os.path.normpath(os.path.join(current_dir, f"{rel_path}.lys")),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return candidates[0]

    def _build_dependency_graph(self, filepath: str) -> None:
        norm_path = os.path.normpath(filepath)
        if norm_path in self.visited_files:
            return
        self.visited_files.add(norm_path)

        current_dir = os.path.dirname(norm_path)
        for rel_mod, alias, _ in self._extract_local_imports(norm_path):
            target = self._resolve_path(current_dir, rel_mod)
            if os.path.isfile(target):
                norm_target = os.path.normpath(target)
                if norm_target not in self.aliases:
                    self.aliases[norm_target] = set()
                self.aliases[norm_target].add(alias)
                self._build_dependency_graph(norm_target)

        self.module_order.append(norm_path)

    def _extract_module_exports(self, filepath: str) -> List[str]:
        """Parse module AST to discover all top-level declared names."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                src = f.read()
            tokens = Lexer(src, filename=filepath).tokenize()
            program = Parser(tokens, filename=filepath, source=src).parse()
            names = []
            for stmt in program.statements:
                if isinstance(stmt, FunctionStmt):
                    names.append(stmt.name)
                elif isinstance(stmt, SetStmt) and hasattr(stmt.target, "name"):
                    names.append(stmt.target.name)
            return names
        except Exception:
            return []

    def bundle(self) -> str:
        """Generate bundled source string."""
        self._build_dependency_graph(self.entry_file)

        bundle_lines = [
            "# ===========================================================================",
            "# Lyslyn Self-Contained Application Bundle",
            f"# Entry: {os.path.basename(self.entry_file)}",
            "# Generated automatically by `lys bundle`",
            "# ===========================================================================\n",
        ]

        seen_stdlib_imports: Set[str] = set()

        for mod_path in self.module_order:
            with open(mod_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("Import ") and not ('"' in stripped or "'" in stripped):
                        seen_stdlib_imports.add(stripped)

        if seen_stdlib_imports:
            bundle_lines.append("# --- Standard Library Imports ---")
            for imp in sorted(seen_stdlib_imports):
                bundle_lines.append(imp)
            bundle_lines.append("")

        entry_norm = os.path.normpath(self.entry_file)
        for mod_path in self.module_order:
            is_entry = (mod_path == entry_norm)
            mod_name = os.path.basename(mod_path).replace(".lys", "")

            bundle_lines.append(f"# --- Begin Module: {mod_name} ({os.path.basename(mod_path)}) ---")

            with open(mod_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if (stripped.startswith("Import ") or stripped.startswith("From ")) and ('"' in stripped or "'" in stripped):
                        continue
                    if stripped.startswith("Import ") and not ('"' in stripped or "'" in stripped):
                        continue
                    bundle_lines.append(line.rstrip())

            if not is_entry:
                exports = self._extract_module_exports(mod_path)
                aliases = self.aliases.get(mod_path, {mod_name})
                if exports:
                    obj_entries = ", ".join(f'"{name}": {name}' for name in exports)
                    for alias in aliases:
                        bundle_lines.append(f'\nSet {alias} to {{{obj_entries}}}')

            bundle_lines.append(f"# --- End Module: {mod_name} ---\n")

        return "\n".join(bundle_lines)


def bundle_project(entry_file: str, output_file: Optional[str] = None) -> str:
    bundler = Bundler(entry_file)
    content = bundler.bundle()
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\033[92m✓\033[0m Bundled '\033[1m{entry_file}\033[0m' into '\033[96m{output_file}\033[0m' ({len(content)} bytes).")
    return content
