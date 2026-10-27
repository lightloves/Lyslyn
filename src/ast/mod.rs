use crate::errors::Span;

#[derive(Debug, Clone, PartialEq)]
pub enum LiteralValue {
    Int(i64),
    Float(f64),
    String(String),
    Bool(bool),
    Nil,
}

#[derive(Debug, Clone, PartialEq)]
pub enum BinaryOp {
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Equal,
    NotEqual,
    Greater,
    GreaterEqual,
    Less,
    LessEqual,
    And,
    Or,
    In,
    NotIn,
}

#[derive(Debug, Clone, PartialEq)]
pub enum UnaryOp {
    Neg,
    Not,
    IsPositive,
    IsNegative,
    IsZero,
    IsEven,
    IsOdd,
    IsEmpty,
    IsSomething,
    IsNotPositive,
    IsNotNegative,
    IsNotZero,
    IsNotEven,
    IsNotOdd,
    IsNotEmpty,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Expr {
    Literal(LiteralValue, Span),
    Variable(String, Span),
    Binary(Box<Expr>, BinaryOp, Box<Expr>, Span),
    Unary(UnaryOp, Box<Expr>, Span),
    List(Vec<Expr>, Span),
    Map(Vec<(Expr, Expr)>, Span),
    MemberAccess(Box<Expr>, String, Span),
    IndexAccess(Box<Expr>, Box<Expr>, Span),
    Call(Box<Expr>, Vec<Expr>, Span),
    Ask(Option<Box<Expr>>, Span),
    If(Box<Expr>, Box<Expr>, Box<Expr>, Span),
}

impl Expr {
    pub fn span(&self) -> Span {
        match self {
            Expr::Literal(_, span)
            | Expr::Variable(_, span)
            | Expr::Binary(_, _, _, span)
            | Expr::Unary(_, _, span)
            | Expr::List(_, span)
            | Expr::Map(_, span)
            | Expr::MemberAccess(_, _, span)
            | Expr::IndexAccess(_, _, span)
            | Expr::Call(_, _, span)
            | Expr::Ask(_, span)
            | Expr::If(_, _, _, span) => span.clone(),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum Stmt {
    Block(Vec<Stmt>, Span),
    Set {
        target: Expr,
        value: Expr,
        is_constant: bool,
        span: Span,
    },
    Change {
        target: Expr,
        operation: String,
        value: Expr,
        span: Span,
    },
    If {
        branches: Vec<(Expr, Vec<Stmt>)>,
        otherwise_branch: Option<Vec<Stmt>>,
        span: Span,
    },
    While {
        condition: Expr,
        body: Vec<Stmt>,
        span: Span,
    },
    For {
        variable: String,
        iterable: Expr,
        body: Vec<Stmt>,
        span: Span,
    },
    Repeat {
        count: Expr,
        body: Vec<Stmt>,
        span: Span,
    },
    Function {
        name: String,
        params: Vec<String>,
        body: Vec<Stmt>,
        is_async: bool,
        span: Span,
    },
    Return {
        value: Option<Expr>,
        span: Span,
    },
    Break(Span),
    Continue(Span),
    Say {
        expressions: Vec<Expr>,
        span: Span,
    },
    Assert {
        condition: Expr,
        message: Option<Expr>,
        span: Span,
    },
    Get {
        module_name: String,
        alias: Option<String>,
        span: Span,
    },
    Import {
        module_name: String,
        alias: Option<String>,
        names: Option<Vec<String>>,
        span: Span,
    },
    Try {
        try_block: Vec<Stmt>,
        catch_var: Option<String>,
        catch_block: Option<Vec<Stmt>>,
        finally_block: Option<Vec<Stmt>>,
        span: Span,
    },
    Raise {
        expression: Expr,
        span: Span,
    },
    AddToList {
        item: Expr,
        list: Expr,
        span: Span,
    },
    Serve {
        port: Expr,
        host: Option<Expr>,
        middlewares: Vec<Expr>,
        routes: Vec<RouteStmt>,
        span: Span,
    },
    Respond {
        status: Expr,
        content_type: String,
        payload: Expr,
        headers: Option<Expr>,
        span: Span,
    },
    Validate {
        target: String,
        schema: Expr,
        span: Span,
    },
    HttpRequest {
        method: String,
        url: Expr,
        headers: Option<Expr>,
        data: Option<Expr>,
        params: Option<Expr>,
        timeout: Option<Expr>,
        response_var: String,
        span: Span,
    },
    Expr(Expr),
}

#[derive(Debug, Clone, PartialEq)]
pub struct RouteStmt {
    pub method: String,
    pub path: String,
    pub body: Vec<Stmt>,
    pub span: Span,
}

impl Stmt {
    pub fn span(&self) -> Span {
        match self {
            Stmt::Block(_, span)
            | Stmt::Set { span, .. }
            | Stmt::Change { span, .. }
            | Stmt::If { span, .. }
            | Stmt::While { span, .. }
            | Stmt::For { span, .. }
            | Stmt::Repeat { span, .. }
            | Stmt::Function { span, .. }
            | Stmt::Return { span, .. }
            | Stmt::Break(span)
            | Stmt::Continue(span)
            | Stmt::Say { span, .. }
            | Stmt::Assert { span, .. }
            | Stmt::Get { span, .. }
            | Stmt::Import { span, .. }
            | Stmt::Try { span, .. }
            | Stmt::Raise { span, .. }
            | Stmt::AddToList { span, .. }
            | Stmt::Serve { span, .. }
            | Stmt::Respond { span, .. }
            | Stmt::Validate { span, .. }
            | Stmt::HttpRequest { span, .. } => span.clone(),
            Stmt::Expr(expr) => expr.span(),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct Program {
    pub statements: Vec<Stmt>,
}
