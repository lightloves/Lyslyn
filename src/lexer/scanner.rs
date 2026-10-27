use crate::errors::{ErrorKind, LyslynError, Span};
use crate::lexer::token::{Token, TokenType};

pub struct Scanner {
    source: Vec<char>,
    filename: String,
    start: usize,
    current: usize,
    line: usize,
    column: usize,
    token_start_column: usize,
    indent_stack: Vec<usize>,
    bracket_depth: usize,
    at_line_start: bool,
    tokens: Vec<Token>,
}

impl Scanner {
    pub fn new(source: &str, filename: &str) -> Self {
        Scanner {
            source: source.chars().collect(),
            filename: filename.to_string(),
            start: 0,
            current: 0,
            line: 1,
            column: 1,
            token_start_column: 1,
            indent_stack: vec![0],
            bracket_depth: 0,
            at_line_start: true,
            tokens: Vec::new(),
        }
    }

    pub fn scan_tokens(&mut self) -> Result<Vec<Token>, LyslynError> {
        while !self.is_at_end() {
            if self.at_line_start {
                self.handle_line_start()?;
            }

            if self.is_at_end() {
                break;
            }

            self.start = self.current;
            self.token_start_column = self.column;
            self.scan_token()?;
        }

        if !self.tokens.is_empty() {
            let last_type = &self.tokens.last().unwrap().token_type;
            if *last_type != TokenType::Newline && *last_type != TokenType::Dedent {
                let span = Span::new(self.line, self.column, 1);
                self.tokens.push(Token::new(TokenType::Newline, "\n", span));
            }
        }

        while self.indent_stack.len() > 1 {
            self.indent_stack.pop();
            let span = Span::new(self.line, self.column, 0);
            self.tokens.push(Token::new(TokenType::Dedent, "", span));
        }

        let eof_span = Span::new(self.line, self.column, 0);
        self.tokens.push(Token::new(TokenType::Eof, "", eof_span));

        Ok(std::mem::take(&mut self.tokens))
    }

    fn handle_line_start(&mut self) -> Result<(), LyslynError> {
        let mut indent_spaces = 0;
        let mut idx = self.current;

        while idx < self.source.len() {
            let ch = self.source[idx];
            if ch == ' ' {
                indent_spaces += 1;
                idx += 1;
            } else if ch == '\t' {
                indent_spaces += 4;
                idx += 1;
            } else {
                break;
            }
        }

        let is_empty_or_comment = if idx >= self.source.len() || self.source[idx] == '\n' || self.source[idx] == '\r' {
            true
        } else if self.source[idx] == '#' {
            true
        } else if idx + 1 < self.source.len() && self.source[idx] == '/' && self.source[idx + 1] == '/' {
            true
        } else {
            false
        };

        if is_empty_or_comment {
            while self.current < idx {
                self.advance();
            }
            self.at_line_start = false;
            return Ok(());
        }

        while self.current < idx {
            self.advance();
        }

        self.at_line_start = false;

        if self.bracket_depth == 0 {
            let current_indent = *self.indent_stack.last().unwrap();
            if indent_spaces > current_indent {
                self.indent_stack.push(indent_spaces);
                let span = Span::new(self.line, 1, indent_spaces - current_indent);
                self.tokens.push(Token::new(TokenType::Indent, "", span));
            } else if indent_spaces < current_indent {
                while self.indent_stack.len() > 1 && indent_spaces < *self.indent_stack.last().unwrap() {
                    self.indent_stack.pop();
                    let span = Span::new(self.line, 1, 0);
                    self.tokens.push(Token::new(TokenType::Dedent, "", span));
                }

                if *self.indent_stack.last().unwrap() != indent_spaces {
                    return Err(LyslynError::new(
                        ErrorKind::Lexer,
                        format!(
                            "Unindent does not match any outer indentation level (expected {}, found {})",
                            self.indent_stack.last().unwrap(),
                            indent_spaces
                        ),
                        Span::new(self.line, 1, 1),
                        &self.filename,
                    )
                    .with_suggestion("Ensure indentation is consistent (4 spaces per level)"));
                }
            }
        }

        Ok(())
    }

    fn scan_token(&mut self) -> Result<(), LyslynError> {
        let c = self.advance();

        match c {
            ' ' | '\t' | '\r' => {}
            '\n' => {
                if self.bracket_depth == 0 {
                    if let Some(last) = self.tokens.last() {
                        if last.token_type != TokenType::Newline && last.token_type != TokenType::Indent {
                            let span = Span::new(self.line - 1, self.column, 1);
                            self.tokens.push(Token::new(TokenType::Newline, "\n", span));
                        }
                    }
                }
                self.at_line_start = true;
            }
            '#' => {
                while self.peek() != '\n' && !self.is_at_end() {
                    self.advance();
                }
            }
            '/' if self.peek() == '/' => {
                while self.peek() != '\n' && !self.is_at_end() {
                    self.advance();
                }
            }
            '/' if self.peek() == '*' => {
                self.advance();
                self.scan_multiline_comment()?;
            }
            '(' => {
                self.bracket_depth += 1;
                self.add_token(TokenType::LParen);
            }
            ')' => {
                if self.bracket_depth > 0 {
                    self.bracket_depth -= 1;
                }
                self.add_token(TokenType::RParen);
            }
            '[' => {
                self.bracket_depth += 1;
                self.add_token(TokenType::LBracket);
            }
            ']' => {
                if self.bracket_depth > 0 {
                    self.bracket_depth -= 1;
                }
                self.add_token(TokenType::RBracket);
            }
            '{' => {
                self.bracket_depth += 1;
                self.add_token(TokenType::LBrace);
            }
            '}' => {
                if self.bracket_depth > 0 {
                    self.bracket_depth -= 1;
                }
                self.add_token(TokenType::RBrace);
            }
            ':' => self.add_token(TokenType::Colon),
            ',' => self.add_token(TokenType::Comma),
            '.' => self.add_token(TokenType::Dot),
            '+' => self.add_token(TokenType::Plus),
            '-' => self.add_token(TokenType::Minus),
            '*' => self.add_token(TokenType::Star),
            '/' => self.add_token(TokenType::Slash),
            '%' => self.add_token(TokenType::Percent),
            '=' => {
                if self.match_char('=') {
                    self.add_token(TokenType::EqualEqual);
                } else {
                    self.add_token(TokenType::EqualSign);
                }
            }
            '!' => {
                if self.match_char('=') {
                    self.add_token(TokenType::BangEqual);
                } else {
                    return Err(self.error(format!("Unexpected character '{}', expected '!='", c)));
                }
            }
            '>' => {
                if self.match_char('=') {
                    self.add_token(TokenType::GreaterEqual);
                } else {
                    self.add_token(TokenType::GreaterThan);
                }
            }
            '<' => {
                if self.match_char('=') {
                    self.add_token(TokenType::LessEqual);
                } else {
                    self.add_token(TokenType::LessThan);
                }
            }
            '"' | '\'' => self.scan_string(c)?,
            _ if c.is_ascii_digit() => self.scan_number()?,
            _ if c.is_alphabetic() || c == '_' => self.scan_identifier()?,
            _ => {
                return Err(self.error(format!("Unexpected character '{}'", c)));
            }
        }

        Ok(())
    }

    fn scan_multiline_comment(&mut self) -> Result<(), LyslynError> {
        while !self.is_at_end() {
            if self.peek() == '*' && self.peek_next() == '/' {
                self.advance();
                self.advance();
                return Ok(());
            }
            self.advance();
        }
        Err(self.error("Unterminated multi-line comment"))
    }

    fn scan_string(&mut self, quote: char) -> Result<(), LyslynError> {
        let is_triple = self.peek() == quote && self.peek_next() == quote;
        if is_triple {
            self.advance();
            self.advance();
        }

        let mut val = String::new();

        while !self.is_at_end() {
            if is_triple {
                if self.peek() == quote && self.peek_next() == quote {
                    if self.current + 2 < self.source.len() && self.source[self.current + 2] == quote {
                        self.advance();
                        self.advance();
                        self.advance();
                        self.add_token(TokenType::String(val));
                        return Ok(());
                    }
                }
            } else if self.peek() == quote {
                self.advance();
                self.add_token(TokenType::String(val));
                return Ok(());
            }

            let ch = self.advance();
            if ch == '\\' && !self.is_at_end() {
                let esc = self.advance();
                match esc {
                    'n' => val.push('\n'),
                    't' => val.push('\t'),
                    'r' => val.push('\r'),
                    '\\' => val.push('\\'),
                    '\'' => val.push('\''),
                    '"' => val.push('"'),
                    _ => {
                        val.push('\\');
                        val.push(esc);
                    }
                }
            } else {
                val.push(ch);
            }
        }

        Err(self.error("Unterminated string literal"))
    }

    fn scan_number(&mut self) -> Result<(), LyslynError> {
        while self.peek().is_ascii_digit() {
            self.advance();
        }

        if self.peek() == '.' && self.peek_next().is_ascii_digit() {
            self.advance();
            while self.peek().is_ascii_digit() {
                self.advance();
            }
            let lexeme: String = self.source[self.start..self.current].iter().collect();
            let val: f64 = lexeme.parse().map_err(|_| self.error("Invalid float literal"))?;
            self.add_token(TokenType::Float(val));
        } else {
            let lexeme: String = self.source[self.start..self.current].iter().collect();
            let val: i64 = lexeme.parse().map_err(|_| self.error("Invalid integer literal"))?;
            self.add_token(TokenType::Int(val));
        }

        Ok(())
    }

    fn scan_identifier(&mut self) -> Result<(), LyslynError> {
        while self.peek().is_alphanumeric() || self.peek() == '_' {
            self.advance();
        }

        let lexeme: String = self.source[self.start..self.current].iter().collect();
        let lower = lexeme.to_lowercase();

        let token_type = match lower.as_str() {
            "set" => TokenType::Set,
            "let" => TokenType::Let,
            "to" => TokenType::To,
            "constant" => TokenType::Constant,
            "define" => TokenType::Define,
            "create" => TokenType::Create,
            "called" => TokenType::Called,
            "change" => TokenType::Change,
            "increase" => TokenType::Increase,
            "decrease" => TokenType::Decrease,
            "by" => TokenType::By,

            "function" => TokenType::Function,
            "method" => TokenType::Method,
            "with" => TokenType::With,
            "return" => TokenType::Return,
            "give" => TokenType::Give,
            "back" => TokenType::Back,
            "async" => TokenType::Async,
            "wait" => TokenType::Wait,
            "call" => TokenType::Call,

            "if" => TokenType::If,
            "otherwise" => TokenType::Otherwise,
            "else" => TokenType::Else,
            "while" => TokenType::While,
            "for" => TokenType::For,
            "every" => TokenType::Every,
            "each" => TokenType::Each,
            "in" => TokenType::In,
            "repeat" => TokenType::Repeat,
            "do" => TokenType::Do,
            "times" => TokenType::Times,
            "break" => TokenType::Break,
            "continue" => TokenType::Continue,
            "stop" => TokenType::Stop,
            "skip" => TokenType::Skip,

            "try" => TokenType::Try,
            "catch" => TokenType::Catch,
            "error" => TokenType::Error,
            "as" => TokenType::As,
            "finally" => TokenType::Finally,
            "raise" => TokenType::Raise,
            "throw" => TokenType::Throw,

            "get" => TokenType::Get,
            "import" => TokenType::Import,
            "from" => TokenType::From,

            "say" => TokenType::Say,
            "display" => TokenType::Display,
            "print" => TokenType::Print,
            "ask" => TokenType::Ask,
            "assert" => TokenType::Assert,

            "and" => TokenType::And,
            "or" => TokenType::Or,
            "not" => TokenType::Not,
            "is" => TokenType::Is,
            "equal" => TokenType::Equal,
            "equals" => TokenType::Equals,
            "does" => TokenType::Does,
            "greater" => TokenType::Greater,
            "less" => TokenType::Less,
            "than" => TokenType::Than,
            "at" => TokenType::At,
            "least" => TokenType::Least,
            "most" => TokenType::Most,
            "positive" => TokenType::Positive,
            "negative" => TokenType::Negative,
            "zero" => TokenType::Zero,
            "even" => TokenType::Even,
            "odd" => TokenType::Odd,
            "empty" => TokenType::Empty,
            "something" => TokenType::Something,

            "a" => TokenType::A,
            "an" => TokenType::An,
            "list" => TokenType::List,
            "object" => TokenType::Object,
            "add" => TokenType::Add,
            "of" => TokenType::Of,
            "the" => TokenType::The,
            "loop" => TokenType::Loop,
            "next" => TokenType::Next,

            "serve" => TokenType::Serve,
            "port" => TokenType::Port,
            "route" => TokenType::Route,
            "use" => TokenType::Use,
            "middleware" => TokenType::Middleware,
            "respond" => TokenType::Respond,
            "status" => TokenType::Status,
            "validate" => TokenType::Validate,
            "body" => TokenType::Body,
            "send" => TokenType::Send,
            "request" => TokenType::Request,
            "save" => TokenType::Save,
            "response" => TokenType::Response,
            "headers" => TokenType::Headers,
            "data" => TokenType::Data,
            "params" => TokenType::Params,
            "timeout" => TokenType::Timeout,

            "true" | "yes" => TokenType::True,
            "false" | "no" => TokenType::False,
            "nil" | "null" | "nothing" => TokenType::Nil,

            _ => TokenType::Identifier(lexeme.clone()),
        };

        self.add_token(token_type);
        Ok(())
    }

    fn add_token(&mut self, token_type: TokenType) {
        let lexeme: String = self.source[self.start..self.current].iter().collect();
        let span = Span::new(
            self.line,
            self.token_start_column,
            self.current.saturating_sub(self.start),
        );
        self.tokens.push(Token::new(token_type, lexeme, span));
    }

    fn advance(&mut self) -> char {
        let ch = self.source[self.current];
        self.current += 1;
        if ch == '\n' {
            self.line += 1;
            self.column = 1;
        } else {
            self.column += 1;
        }
        ch
    }

    fn match_char(&mut self, expected: char) -> bool {
        if self.is_at_end() || self.source[self.current] != expected {
            false
        } else {
            self.current += 1;
            self.column += 1;
            true
        }
    }

    fn peek(&self) -> char {
        if self.is_at_end() {
            '\0'
        } else {
            self.source[self.current]
        }
    }

    fn peek_next(&self) -> char {
        if self.current + 1 >= self.source.len() {
            '\0'
        } else {
            self.source[self.current + 1]
        }
    }

    fn is_at_end(&self) -> bool {
        self.current >= self.source.len()
    }

    fn error(&self, message: impl Into<String>) -> LyslynError {
        LyslynError::new(
            ErrorKind::Lexer,
            message,
            Span::new(self.line, self.token_start_column, 1),
            &self.filename,
        )
    }
}
