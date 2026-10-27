use crate::errors::Span;
use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum TokenType {
    Int(i64),
    Float(f64),
    String(String),
    Identifier(String),

    True,
    False,
    Nil,

    Set,
    Let,
    To,
    Constant,
    Define,
    Create,
    Called,
    Change,
    Increase,
    Decrease,
    By,

    Function,
    Method,
    Class,
    Inheriting,
    Initialize,
    New,
    This,
    Parent,
    Instance,
    Type,
    StringKeyword,
    NumberKeyword,
    IntegerKeyword,
    FloatKeyword,
    BooleanKeyword,
    MapKeyword,
    With,
    Return,
    Give,
    Back,
    Async,
    Wait,
    Call,

    If,
    Otherwise,
    Else,
    While,
    For,
    Every,
    Each,
    In,
    Repeat,
    Do,
    Times,
    Break,
    Continue,
    Stop,
    Skip,

    Try,
    Catch,
    Error,
    As,
    Finally,
    Raise,
    Throw,

    Get,
    Import,
    From,

    Say,
    Display,
    Print,
    Ask,
    Assert,

    And,
    Or,
    Not,
    Is,
    Equal,
    Equals,
    Does,
    Greater,
    Less,
    Than,
    At,
    Least,
    Most,
    Positive,
    Negative,
    Zero,
    Even,
    Odd,
    Empty,
    Something,

    A,
    An,
    List,
    Object,
    Add,
    Of,
    The,
    Loop,
    Next,

    Serve,
    Port,
    Route,
    Use,
    Middleware,
    Respond,
    Status,
    Validate,
    Body,
    Send,
    Request,
    Save,
    Response,
    Headers,
    Data,
    Params,
    Timeout,

    Plus,
    Minus,
    Star,
    Slash,
    Percent,

    EqualSign,
    EqualEqual,
    BangEqual,
    GreaterThan,
    GreaterEqual,
    LessThan,
    LessEqual,

    Colon,
    Comma,
    Dot,
    LParen,
    RParen,
    LBracket,
    RBracket,
    LBrace,
    RBrace,

    Newline,
    Indent,
    Dedent,
    Eof,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Token {
    pub token_type: TokenType,
    pub lexeme: String,
    pub span: Span,
}

impl Token {
    pub fn new(token_type: TokenType, lexeme: impl Into<String>, span: Span) -> Self {
        Token {
            token_type,
            lexeme: lexeme.into(),
            span,
        }
    }
}

impl fmt::Display for TokenType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}
