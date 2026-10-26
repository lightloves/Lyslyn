"""Production-grade Code Beautifier and Formatter for Lyslyn."""
import difflib
import re
from typing import Dict, List, Optional, Tuple


STATEMENT_KEYWORDS = {
    "set": "Set",
    "let": "Let",
    "constant": "Constant",
    "define": "Define",
    "create": "Create",
    "function": "Function",
    "method": "Method",
    "return": "Return",
    "if": "If",
    "otherwise": "Otherwise",
    "else": "Else",
    "while": "While",
    "for": "For",
    "each": "each",
    "repeat": "Repeat",
    "times": "times",
    "break": "Break",
    "continue": "Continue",
    "try": "Try",
    "catch": "Catch",
    "finally": "Finally",
    "raise": "Raise",
    "throw": "Throw",
    "import": "Import",
    "from": "From",
    "send": "Send",
    "request": "request",
    "save": "save",
    "response": "response",
    "serve": "Serve",
    "route": "Route",
    "use": "Use",
    "respond": "Respond",
    "validate": "Validate",
    "print": "Print",
    "display": "Display",
    "show": "Show",
    "add": "Add",
    "append": "Append",
    "call": "Call",
    "run": "Run",
    "execute": "Execute",
    "stop": "Stop",
    "skip": "Skip",
    "give": "Give",
    "do": "Do",
    "assert": "Assert",
    "ask": "Ask",
    "async": "Async",
    "wait": "Wait",
}

CONNECTOR_KEYWORDS = {
    "to": "to",
    "with": "with",
    "by": "by",
    "is": "is",
    "as": "as",
    "and": "and",
    "or": "or",
    "not": "not",
    "in": "in",
    "on": "on",
    "every": "every",
    "each": "each",
    "back": "back",
    "list": "list",
    "object": "object",
    "containing": "containing",
    "empty": "empty",
    "positive": "positive",
    "negative": "negative",
    "even": "even",
    "odd": "odd",
    "zero": "zero",
    "something": "something",
    "nothing": "nothing",
    "port": "port",
    "host": "host",
    "middleware": "middleware",
    "status": "status",
    "body": "body",
    "query": "query",
    "params": "params",
    "headers": "headers",
    "data": "data",
    "timeout": "timeout",
    "json": "json",
    "text": "text",
    "redirect": "redirect",
    "true": "true",
    "false": "false",
    "nil": "nil",
    "null": "nil",
}

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


def format_source(source: str) -> str:
    """Beautify Lyslyn source code with clean indentation, consistent spacing, and standard keyword casing."""
    lines = source.splitlines()
    formatted_lines: List[str] = []
    consecutive_empty = 0
    prev_opened_block = False
    prev_indent_level = 0

    for raw_line in lines:
        stripped = raw_line.strip()

        if not stripped:
            consecutive_empty += 1
            if consecutive_empty <= 2 and formatted_lines:
                formatted_lines.append("")
            continue

        consecutive_empty = 0

        tab_expanded = raw_line.replace("\t", "    ")
        leading_spaces = len(tab_expanded) - len(tab_expanded.lstrip(" "))
        indent_level = round(leading_spaces / 4.0)

        is_dedent_keyword = any(
            stripped.lower().startswith(kw) for kw in ("otherwise", "else", "catch", "finally")
        )

        if prev_opened_block and indent_level <= prev_indent_level and not is_dedent_keyword:
            indent_level = prev_indent_level + 1

        indent_prefix = "    " * indent_level

        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
            formatted_lines.append(f"{indent_prefix}{stripped}")
            continue

        strings_map: Dict[str, str] = {}
        str_idx = [0]

        def mask_string(match: re.Match) -> str:
            placeholder = f"__LYSLYN_STR_{str_idx[0]}__"
            str_idx[0] += 1
            strings_map[placeholder] = match.group(0)
            return placeholder

        line_content = re.sub(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', mask_string, stripped)

        inline_comment = ""
        if " #" in line_content:
            parts = line_content.split(" #", 1)
            line_content = parts[0]
            inline_comment = " #" + parts[1]
        elif " //" in line_content:
            parts = line_content.split(" //", 1)
            line_content = parts[0]
            inline_comment = " //" + parts[1]

        words = line_content.split()
        normalized_words = []
        is_first_word = True

        for i, word in enumerate(words):
            clean_word = word.rstrip(":")
            has_colon = word.endswith(":")
            lower_word = clean_word.lower()

            if is_first_word and lower_word in STATEMENT_KEYWORDS:
                w_out = STATEMENT_KEYWORDS[lower_word]
                is_first_word = False
            elif lower_word in HTTP_METHODS and i > 0 and words[i - 1].lower() in ("route", "send"):
                w_out = lower_word.upper()
            elif lower_word in CONNECTOR_KEYWORDS:
                w_out = CONNECTOR_KEYWORDS[lower_word]
            elif lower_word in STATEMENT_KEYWORDS and lower_word in ("otherwise", "else", "catch", "finally", "return"):
                w_out = STATEMENT_KEYWORDS[lower_word]
            else:
                w_out = clean_word
                is_first_word = False

            if has_colon:
                w_out += ":"
            normalized_words.append(w_out)

        line_norm = " ".join(normalized_words)

        line_norm = re.sub(r"\s*([+\-*/%])\s*", r" \1 ", line_norm)
        line_norm = re.sub(r"\s*(==|!=|<=|>=|<|>|=)\s*", r" \1 ", line_norm)
        line_norm = re.sub(r"\s*,\s*", ", ", line_norm)
        line_norm = re.sub(r"\s*:\s*$", ":", line_norm)

        line_norm = re.sub(r" +", " ", line_norm)

        line_norm = re.sub(r"([a-zA-Z0-9_\)\]\>\"\'])\s*:\s+", r"\1: ", line_norm)

        for placeholder, original_str in strings_map.items():
            line_norm = line_norm.replace(placeholder, original_str)

        if inline_comment:
            line_norm += inline_comment

        prev_opened_block = stripped.endswith(":") and not stripped.startswith(("#", "//", "/*"))
        prev_indent_level = indent_level

        formatted_lines.append(f"{indent_prefix}{line_norm.rstrip()}")

    result = "\n".join(formatted_lines).rstrip() + "\n"
    return result


def generate_diff(original: str, formatted: str, filename: str = "<source>") -> str:
    """Generate colorized unified diff between original and beautified code."""
    orig_lines = original.splitlines(keepends=True)
    fmt_lines = formatted.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        orig_lines,
        fmt_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}"
    ))

    if not diff:
        return ""

    c_green = "\033[92m"
    c_red = "\033[91m"
    c_cyan = "\033[96m"
    c_reset = "\033[0m"

    out = []
    for line in diff:
        if line.startswith("+++") or line.startswith("---"):
            out.append(f"\033[1m{line}\033[0m")
        elif line.startswith("@@"):
            out.append(f"{c_cyan}{line.rstrip()}{c_reset}\n")
        elif line.startswith("+"):
            out.append(f"{c_green}{line.rstrip()}{c_reset}\n")
        elif line.startswith("-"):
            out.append(f"{c_red}{line.rstrip()}{c_reset}\n")
        else:
            out.append(line)

    return "".join(out)
