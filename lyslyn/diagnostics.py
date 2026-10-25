"""Diagnostic and error reporting system for Lyslyn."""
import sys
from typing import Optional


class LyslynError(Exception):
    """Base class for all Lyslyn errors."""
    def __init__(
        self,
        message: str,
        line: int = 1,
        column: int = 1,
        length: int = 1,
        filename: str = "<input>",
        source: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.length = max(1, length)
        self.filename = filename
        self.source = source
        self.suggestion = suggestion

    def format_diagnostic(self, color: bool = True) -> str:
        """Render a formatted, user-friendly compiler diagnostic."""
        c_red = "\033[91;1m" if color else ""
        c_cyan = "\033[96m" if color else ""
        c_yellow = "\033[93m" if color else ""
        c_bold = "\033[1m" if color else ""
        c_reset = "\033[0m" if color else ""

        error_type = self.__class__.__name__
        header = f"{c_red}{error_type}{c_reset}: {c_bold}{self.message}{c_reset}"
        location = f"  --> {c_cyan}{self.filename}:{self.line}:{self.column}{c_reset}"

        lines = [header, location]

        if self.source:
            source_lines = self.source.splitlines()
            if 1 <= self.line <= len(source_lines):
                line_str = source_lines[self.line - 1]
                line_num_str = f"{self.line:>4} | "
                lines.append(f"{c_cyan}{line_num_str}{c_reset}{line_str}")

                # Pointer row
                padding = " " * (len(line_num_str) + max(0, self.column - 1))
                pointer = "^" * self.length
                lines.append(f"{padding}{c_red}{pointer}{c_reset}")

        if self.suggestion:
            lines.append(f"  {c_yellow}Note:{c_reset} {self.suggestion}")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format_diagnostic(color=False)


class LexerError(LyslynError):
    """Raised during lexical scanning."""
    pass


class ParseError(LyslynError):
    """Raised during syntactic parsing."""
    pass


class SemanticError(LyslynError):
    """Raised during semantic analysis."""
    pass


class RuntimeError_(LyslynError):
    """Raised during program execution."""
    pass
