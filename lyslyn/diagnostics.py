"""Diagnostic and error reporting system for Lyslyn with syntax-highlighted frames."""
import re
import sys
from typing import Optional


HIGHLIGHT_KEYWORDS = {
    "set", "let", "constant", "define", "create", "called", "change",
    "increase", "decrease", "function", "method", "with", "return",
    "if", "otherwise", "else", "while", "for", "each", "in", "repeat", "times",
    "break", "continue", "try", "catch", "finally", "raise", "throw",
    "import", "from", "send", "request", "save", "response", "print", "assert",
    "serve", "route", "use", "respond", "validate", "body", "status", "port",
    "true", "false", "nil", "and", "or", "not", "is", "equals", "at", "least", "most"
}


def highlight_code_line(line: str) -> str:
    """Apply terminal ANSI colors to code snippet line."""
    c_kw = "\033[95;1m"
    c_str = "\033[92m"
    c_num = "\033[96m"
    c_comment = "\033[90m"
    c_reset = "\033[0m"

    if line.strip().startswith("#") or line.strip().startswith("//"):
        return f"{c_comment}{line}{c_reset}"

    strings = []
    def save_str(m):
        strings.append(m.group(0))
        return f"\001{len(strings)-1}\002"

    temp = re.sub(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', save_str, line)

    temp = re.sub(r'\b\d+(\.\d+)?\b', lambda m: f"{c_num}{m.group(0)}{c_reset}", temp)

    words = re.split(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\b)', temp)
    res = []
    for w in words:
        if w.lower() in HIGHLIGHT_KEYWORDS:
            res.append(f"{c_kw}{w}{c_reset}")
        else:
            res.append(w)
    out = "".join(res)

    for i, s in enumerate(strings):
        out = out.replace(f"\001{i}\002", f"{c_str}{s}{c_reset}")

    return out


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
        """Render a formatted, user-friendly compiler diagnostic with code frame."""
        c_red = "\033[91;1m" if color else ""
        c_cyan = "\033[96m" if color else ""
        c_yellow = "\033[93m" if color else ""
        c_bold = "\033[1m" if color else ""
        c_dim = "\033[90m" if color else ""
        c_reset = "\033[0m" if color else ""

        error_type = self.__class__.__name__.rstrip("_")
        header = f"{c_red}✖ {error_type}{c_reset}: {c_bold}{self.message}{c_reset}"
        location = f"  {c_dim}-->{c_reset} {c_cyan}{self.filename}:{self.line}:{self.column}{c_reset}"

        lines = [header, location]

        if self.source:
            source_lines = self.source.splitlines()
            if 1 <= self.line <= len(source_lines):
                line_str = source_lines[self.line - 1]
                line_num_str = f"{self.line:>4} │ "
                colored_line = highlight_code_line(line_str) if color else line_str
                lines.append(f"{c_dim}{line_num_str}{c_reset}{colored_line}")

                padding = " " * (len(line_num_str) + max(0, self.column - 1))
                pointer = "^" * self.length
                lines.append(f"{padding}{c_red}{pointer}{c_reset}")

        if self.suggestion:
            lines.append(f"  {c_yellow}💡 Suggestion:{c_reset} {self.suggestion}")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format_diagnostic(color=False)


class LexerError(LyslynError):
    pass


class ParseError(LyslynError):
    pass


class SemanticError(LyslynError):
    pass


class RuntimeError_(LyslynError):
    pass
