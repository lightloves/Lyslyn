use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Span {
    pub line: usize,
    pub column: usize,
    pub length: usize,
}

impl Span {
    pub fn new(line: usize, column: usize, length: usize) -> Self {
        Span {
            line,
            column,
            length,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ErrorKind {
    Lexer,
    Parser,
    Semantic,
    Compile,
    Runtime,
}

impl fmt::Display for ErrorKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ErrorKind::Lexer => write!(f, "LexerError"),
            ErrorKind::Parser => write!(f, "ParseError"),
            ErrorKind::Semantic => write!(f, "SemanticError"),
            ErrorKind::Compile => write!(f, "CompileError"),
            ErrorKind::Runtime => write!(f, "RuntimeError"),
        }
    }
}

#[derive(Debug, Clone)]
pub struct LyslynError {
    pub kind: ErrorKind,
    pub message: String,
    pub span: Span,
    pub filename: String,
    pub source: Option<String>,
    pub suggestion: Option<String>,
}

impl LyslynError {
    pub fn new(
        kind: ErrorKind,
        message: impl Into<String>,
        span: Span,
        filename: impl Into<String>,
    ) -> Self {
        LyslynError {
            kind,
            message: message.into(),
            span,
            filename: filename.into(),
            source: None,
            suggestion: None,
        }
    }

    pub fn with_source(mut self, source: impl Into<String>) -> Self {
        self.source = Some(source.into());
        self
    }

    pub fn with_suggestion(mut self, suggestion: impl Into<String>) -> Self {
        self.suggestion = Some(suggestion.into());
        self
    }

    pub fn format_diagnostic(&self) -> String {
        let mut out = String::new();
        out.push_str(&format!(
            "{}: {} at {}:{}:{}\n",
            self.kind, self.message, self.filename, self.span.line, self.span.column
        ));

        if let Some(ref source) = self.source {
            let lines: Vec<&str> = source.lines().collect();
            if self.span.line > 0 && self.span.line <= lines.len() {
                let line_str = lines[self.span.line - 1];
                let line_num_str = format!("{:4} | ", self.span.line);
                out.push_str(&line_num_str);
                out.push_str(line_str);
                out.push('\n');

                let indent = " ".repeat(line_num_str.len() + self.span.column.saturating_sub(1));
                let carets = "^".repeat(std::cmp::max(1, self.span.length));
                out.push_str(&format!("{}{}\n", indent, carets));
            }
        }

        if let Some(ref sugg) = self.suggestion {
            out.push_str(&format!("  help: {}\n", sugg));
        }

        out
    }
}

impl fmt::Display for LyslynError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.format_diagnostic())
    }
}

impl std::error::Error for LyslynError {}
