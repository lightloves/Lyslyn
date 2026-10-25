"""Lexer for Lyslyn programming language."""
from typing import List, Optional
from .tokens import Token, TokenType, KEYWORDS
from .diagnostics import LexerError


class Lexer:
    def __init__(self, source: str, filename: str = "<input>"):
        self.source = source
        self.filename = filename
        self.length = len(source)
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.token_start_column = 1

        self.indent_stack: List[int] = [0]
        self.bracket_depth = 0
        self.at_line_start = True
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        self.tokens = []
        self.indent_stack = [0]
        self.bracket_depth = 0
        self.at_line_start = True
        self.line = 1
        self.column = 1
        self.current = 0

        while not self.is_at_end():
            if self.at_line_start:
                self.handle_line_start()
                if self.is_at_end():
                    break

            self.start = self.current
            self.token_start_column = self.column
            self.scan_token()

        # Emit newline at EOF if previous token wasn't NEWLINE or DEDENT or empty
        if self.tokens and self.tokens[-1].type not in (TokenType.NEWLINE, TokenType.DEDENT):
            self.tokens.append(Token(TokenType.NEWLINE, "\n", None, self.line, self.column, 1))

        # Close all open indentation blocks at EOF
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", None, self.line, self.column, 0))

        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column, 0))
        return self.tokens

    def handle_line_start(self) -> None:
        """Process leading whitespace and emit INDENT/DEDENT tokens."""
        indent_spaces = 0
        char_idx = self.current

        # Look ahead to count indent
        while char_idx < self.length:
            ch = self.source[char_idx]
            if ch == ' ':
                indent_spaces += 1
                char_idx += 1
            elif ch == '\t':
                indent_spaces += 4  # standard 4-space tab expansion
                char_idx += 1
            else:
                break

        # Check if line is empty or comment-only
        is_empty_or_comment = False
        if char_idx >= self.length or self.source[char_idx] in ('\r', '\n'):
            is_empty_or_comment = True
        elif self.source[char_idx] == '#':
            is_empty_or_comment = True
        elif char_idx + 1 < self.length and self.source[char_idx:char_idx + 2] == '//':
            is_empty_or_comment = True

        if is_empty_or_comment:
            # Advance through whitespace to the newline
            while self.current < char_idx:
                self.advance()
            self.at_line_start = False
            return

        # Advance past the indentation whitespace
        while self.current < char_idx:
            self.advance()

        self.at_line_start = False

        # Only emit INDENT/DEDENT if outside brackets/parens/braces
        if self.bracket_depth == 0:
            current_indent = self.indent_stack[-1]
            if indent_spaces > current_indent:
                self.indent_stack.append(indent_spaces)
                self.tokens.append(
                    Token(TokenType.INDENT, "", indent_spaces, self.line, self.column, indent_spaces - current_indent)
                )
            elif indent_spaces < current_indent:
                while len(self.indent_stack) > 1 and indent_spaces < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    self.tokens.append(
                        Token(TokenType.DEDENT, "", indent_spaces, self.line, self.column, 0)
                    )
                if self.indent_stack[-1] != indent_spaces:
                    raise LexerError(
                        f"Unindent does not match any outer indentation level (expected {self.indent_stack[-1]}, found {indent_spaces})",
                        line=self.line,
                        column=self.column,
                        length=1,
                        filename=self.filename,
                        source=self.source,
                        suggestion="Check indentation spacing (use consistent 4 spaces)"
                    )

    def scan_token(self) -> None:
        c = self.advance()

        # Whitespace within line
        if c in (' ', '\t', '\r'):
            return

        # Newline
        if c == '\n':
            if self.bracket_depth == 0:
                # Avoid duplicate newlines
                if not self.tokens or self.tokens[-1].type != TokenType.NEWLINE:
                    self.add_token(TokenType.NEWLINE)
            self.at_line_start = True
            return

        # Comments
        if c == '#':
            while self.peek() != '\n' and not self.is_at_end():
                self.advance()
            return

        if c == '/' and self.peek() == '/':
            while self.peek() != '\n' and not self.is_at_end():
                self.advance()
            return

        if c == '/' and self.peek() == '*':
            self.advance()  # consume '*'
            self.scan_multiline_comment()
            return

        # Operators & delimiters
        if c == '(':
            self.bracket_depth += 1
            self.add_token(TokenType.LPAREN)
        elif c == ')':
            if self.bracket_depth > 0:
                self.bracket_depth -= 1
            self.add_token(TokenType.RPAREN)
        elif c == '[':
            self.bracket_depth += 1
            self.add_token(TokenType.LBRACKET)
        elif c == ']':
            if self.bracket_depth > 0:
                self.bracket_depth -= 1
            self.add_token(TokenType.RBRACKET)
        elif c == '{':
            self.bracket_depth += 1
            self.add_token(TokenType.LBRACE)
        elif c == '}':
            if self.bracket_depth > 0:
                self.bracket_depth -= 1
            self.add_token(TokenType.RBRACE)
        elif c == ':':
            self.add_token(TokenType.COLON)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == '.':
            self.add_token(TokenType.DOT)
        elif c == '+':
            self.add_token(TokenType.PLUS)
        elif c == '-':
            self.add_token(TokenType.MINUS)
        elif c == '*':
            self.add_token(TokenType.STAR)
        elif c == '/':
            self.add_token(TokenType.SLASH)
        elif c == '%':
            self.add_token(TokenType.PERCENT)
        elif c == '=':
            if self.match('='):
                self.add_token(TokenType.EQUAL_EQUAL)
            else:
                self.add_token(TokenType.EQUAL_SIGN)
        elif c == '!':
            if self.match('='):
                self.add_token(TokenType.BANG_EQUAL)
            else:
                self.add_token(TokenType.NOT)
        elif c == '<':
            if self.match('='):
                self.add_token(TokenType.LESS_EQUAL)
            else:
                self.add_token(TokenType.LESS_THAN)
        elif c == '>':
            if self.match('='):
                self.add_token(TokenType.GREATER_EQUAL)
            else:
                self.add_token(TokenType.GREATER_THAN)

        # Strings
        elif c in ('"', "'"):
            self.scan_string(c)

        # Numbers
        elif c.isdigit():
            self.scan_number()

        # Identifiers & Keywords
        elif c.isalpha() or c == '_':
            self.scan_identifier()

        else:
            raise LexerError(
                f"Unexpected character '{c}'",
                line=self.line,
                column=self.token_start_column,
                length=1,
                filename=self.filename,
                source=self.source
            )

    def scan_multiline_comment(self) -> None:
        start_line = self.line
        start_col = self.token_start_column
        while not self.is_at_end():
            if self.peek() == '*' and self.peek_next() == '/':
                self.advance()  # '*'
                self.advance()  # '/'
                return
            if self.peek() == '\n':
                self.line += 1
                self.column = 0
            self.advance()
        raise LexerError(
            "Unterminated multi-line comment",
            line=start_line,
            column=start_col,
            length=2,
            filename=self.filename,
            source=self.source
        )

    def scan_string(self, quote_char: str) -> None:
        start_line = self.line
        start_col = self.token_start_column

        # Check for triple-quote
        is_triple = False
        if self.peek() == quote_char and self.peek_next() == quote_char:
            self.advance()
            self.advance()
            is_triple = True

        value_chars: List[str] = []

        while not self.is_at_end():
            if is_triple:
                if (self.peek() == quote_char and
                    self.peek_next() == quote_char and
                    self.current + 2 < self.length and
                    self.source[self.current + 2] == quote_char):
                    self.advance()
                    self.advance()
                    self.advance()
                    literal = "".join(value_chars)
                    self.add_token(TokenType.STRING, literal)
                    return
            else:
                if self.peek() == quote_char:
                    self.advance()
                    literal = "".join(value_chars)
                    self.add_token(TokenType.STRING, literal)
                    return

            c = self.advance()
            if c == '\n':
                if not is_triple:
                    raise LexerError(
                        "Unterminated string literal (newline in single-line string)",
                        line=start_line,
                        column=start_col,
                        length=self.current - self.start,
                        filename=self.filename,
                        source=self.source,
                        suggestion="Use triple quotes \"\"\" for multi-line strings"
                    )
                value_chars.append('\n')
            elif c == '\\':
                if self.is_at_end():
                    break
                escape = self.advance()
                if escape == 'n':
                    value_chars.append('\n')
                elif escape == 't':
                    value_chars.append('\t')
                elif escape == 'r':
                    value_chars.append('\r')
                elif escape == '\\':
                    value_chars.append('\\')
                elif escape == '"':
                    value_chars.append('"')
                elif escape == "'":
                    value_chars.append("'")
                else:
                    value_chars.append('\\')
                    value_chars.append(escape)
            else:
                value_chars.append(c)

        raise LexerError(
            "Unterminated string literal",
            line=start_line,
            column=start_col,
            length=self.current - self.start,
            filename=self.filename,
            source=self.source
        )

    def scan_number(self) -> None:
        while self.peek().isdigit() or self.peek() == '_':
            self.advance()

        is_float = False
        if self.peek() == '.' and self.peek_next().isdigit():
            is_float = True
            self.advance()  # consume '.'
            while self.peek().isdigit() or self.peek() == '_':
                self.advance()

        # Scientific notation: e.g. 1e5, 2.5e-3
        if self.peek() in ('e', 'E'):
            is_float = True
            self.advance()
            if self.peek() in ('+', '-'):
                self.advance()
            while self.peek().isdigit():
                self.advance()

        raw_text = self.source[self.start:self.current].replace('_', '')
        if is_float:
            self.add_token(TokenType.FLOAT, float(raw_text))
        else:
            self.add_token(TokenType.INT, int(raw_text))

    def scan_identifier(self) -> None:
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()

        text = self.source[self.start:self.current]
        lower_text = text.lower()

        # Check keyword
        token_type = KEYWORDS.get(lower_text, TokenType.IDENTIFIER)
        literal = None
        if token_type == TokenType.TRUE:
            literal = True
        elif token_type == TokenType.FALSE:
            literal = False
        elif token_type == TokenType.NIL:
            literal = None

        self.add_token(token_type, literal)

    def is_at_end(self) -> bool:
        return self.current >= self.length

    def advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        if c == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return c

    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.advance()
        return True

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= self.length:
            return '\0'
        return self.source[self.current + 1]

    def add_token(self, token_type: TokenType, literal: Optional[object] = None) -> None:
        lexeme = self.source[self.start:self.current]
        length = len(lexeme)
        self.tokens.append(
            Token(token_type, lexeme, literal, self.line, self.token_start_column, length)
        )
