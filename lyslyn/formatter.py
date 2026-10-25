"""Source code formatter for the Lyslyn programming language."""
import re
from typing import List, Dict


TITLE_KEYWORDS = {
    "set", "let", "constant", "define", "create", "called", "change",
    "increase", "decrease", "function", "method", "with", "return",
    "if", "otherwise", "else", "while", "for", "each", "in", "repeat", "times",
    "break", "continue", "try", "catch", "finally", "raise", "throw",
    "import", "from", "send", "request", "save", "response", "print", "ask", "async", "wait"
}


def format_source(source: str) -> str:
    """Format Lyslyn source code with consistent indentation, spacing, and styling."""
    lines = source.splitlines()
    formatted_lines: List[str] = []
    current_indent = 0
    blank_line_count = 0

    for raw_line in lines:
        line = raw_line.strip()

        # Handle empty lines
        if not line:
            blank_line_count += 1
            if blank_line_count <= 2 and formatted_lines:
                formatted_lines.append("")
            continue

        blank_line_count = 0

        # Preserve comments
        if line.startswith("#") or line.startswith("//"):
            indent_prefix = "    " * current_indent
            formatted_lines.append(f"{indent_prefix}{line}")
            continue

        # Adjust indentation if line starts with dedenting keywords:
        lower_line = line.lower()
        is_dedent = (
            lower_line.startswith("otherwise") or
            lower_line.startswith("else") or
            lower_line.startswith("catch") or
            lower_line.startswith("finally")
        )

        effective_indent = max(0, current_indent - 1) if is_dedent else current_indent

        # Protect string literals from regex manipulation
        strings_map: Dict[str, str] = {}
        str_idx = [0]

        def replace_str(match: re.Match) -> str:
            placeholder = f"__LYS_STR_{str_idx[0]}__"
            str_idx[0] += 1
            strings_map[placeholder] = match.group(0)
            return placeholder

        # Extract double and single quoted strings
        masked_line = re.sub(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', replace_str, line)

        # Normalize casing of leading keywords
        tokens = masked_line.split()
        normalized_tokens = []
        for word in tokens:
            w_clean = word.rstrip(":")
            has_colon = word.endswith(":")
            if w_clean.lower() in TITLE_KEYWORDS:
                w_norm = w_clean.capitalize()
                if has_colon:
                    w_norm += ":"
                normalized_tokens.append(w_norm)
            else:
                normalized_tokens.append(word)

        norm_line = " ".join(normalized_tokens)

        # Ensure clean spaces around operators
        norm_line = re.sub(r"\s*([+\-*/%])\s*", r" \1 ", norm_line)
        norm_line = re.sub(r"\s*(==|!=|<=|>=|<|>|=)\s*", r" \1 ", norm_line)
        norm_line = re.sub(r" +", " ", norm_line)
        norm_line = re.sub(r"\s*:\s*$", ":", norm_line)
        norm_line = re.sub(r"\s*,\s*", ", ", norm_line)

        # Restore string literals
        for placeholder, original_str in strings_map.items():
            norm_line = norm_line.replace(placeholder, original_str)

        indent_prefix = "    " * effective_indent
        formatted_lines.append(f"{indent_prefix}{norm_line}")

        # Check if line opens a new block
        if norm_line.endswith(":"):
            current_indent = effective_indent + 1

    return "\n".join(formatted_lines) + "\n"
