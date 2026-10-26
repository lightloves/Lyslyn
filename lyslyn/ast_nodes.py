"""Abstract Syntax Tree node definitions for Lyslyn."""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any, Union


class ASTNode:
    """Base class for all AST nodes."""
    line: int
    column: int


# ============================================================================
# Expressions
# ============================================================================

class Expr(ASTNode):
    pass


@dataclass
class LiteralExpr(Expr):
    value: Any
    line: int
    column: int


@dataclass
class VariableExpr(Expr):
    name: str
    line: int
    column: int


@dataclass
class BinaryExpr(Expr):
    left: Expr
    operator: str  # '+', '-', '*', '/', '%', '==', '!=', '<', '<=', '>', '>=', 'and', 'or', 'in', 'not in'
    right: Expr
    line: int
    column: int


@dataclass
class UnaryExpr(Expr):
    operator: str  # '-', '+', 'not', 'await'
    operand: Expr
    line: int
    column: int


@dataclass
class ListExpr(Expr):
    elements: List[Expr]
    line: int
    column: int


@dataclass
class MapExpr(Expr):
    entries: List[Tuple[Expr, Expr]]  # List of (key, value)
    line: int
    column: int


@dataclass
class MemberAccessExpr(Expr):
    target: Expr
    member: str
    line: int
    column: int


@dataclass
class IndexAccessExpr(Expr):
    target: Expr
    index: Expr
    line: int
    column: int


@dataclass
class CallExpr(Expr):
    callee: Expr
    arguments: List[Expr]
    line: int
    column: int


@dataclass
class StringInterpolationExpr(Expr):
    parts: List[Union[str, Expr]]
    line: int
    column: int


@dataclass
class AskExpr(Expr):
    prompt: Optional[Expr]
    line: int
    column: int


@dataclass
class ConditionalExpr(Expr):
    condition: Expr
    then_expr: Expr
    else_expr: Expr
    line: int
    column: int



# ============================================================================
# Statements
# ============================================================================

class Stmt(ASTNode):
    pass


@dataclass
class BlockStmt(Stmt):
    statements: List[Stmt]
    line: int
    column: int


@dataclass
class SetStmt(Stmt):
    target: Expr  # VariableExpr, MemberAccessExpr, or IndexAccessExpr
    value: Expr
    is_constant: bool
    line: int
    column: int


@dataclass
class ChangeStmt(Stmt):
    target: Expr  # VariableExpr, MemberAccessExpr, or IndexAccessExpr
    operation: str  # 'increase', 'decrease', 'change'
    value: Expr
    line: int
    column: int


@dataclass
class IfStmt(Stmt):
    # List of (condition, body)
    branches: List[Tuple[Expr, BlockStmt]]
    otherwise_branch: Optional[BlockStmt]
    line: int
    column: int


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: BlockStmt
    line: int
    column: int


@dataclass
class ForStmt(Stmt):
    variable: str
    iterable: Expr
    body: BlockStmt
    line: int
    column: int


@dataclass
class RepeatStmt(Stmt):
    count: Expr
    body: BlockStmt
    line: int
    column: int


@dataclass
class FunctionStmt(Stmt):
    name: str
    params: List[str]
    body: BlockStmt
    is_async: bool
    line: int
    column: int


@dataclass
class ReturnStmt(Stmt):
    value: Optional[Expr]
    line: int
    column: int


@dataclass
class AssertStmt(Stmt):
    condition: Expr
    message: Optional[Expr]
    line: int
    column: int


@dataclass
class BreakStmt(Stmt):
    line: int
    column: int


@dataclass
class ContinueStmt(Stmt):
    line: int
    column: int


@dataclass
class TryStmt(Stmt):
    try_block: BlockStmt
    catch_var: Optional[str]
    catch_block: Optional[BlockStmt]
    finally_block: Optional[BlockStmt]
    line: int
    column: int


@dataclass
class RaiseStmt(Stmt):
    expression: Expr
    line: int
    column: int


@dataclass
class ImportStmt(Stmt):
    module_name: str
    alias: Optional[str]
    imported_names: Optional[List[str]]  # For "From module import x, y"
    line: int
    column: int


@dataclass
class HttpStmt(Stmt):
    method: str  # 'GET', 'POST', 'PUT', 'DELETE', etc.
    url: Expr
    headers: Optional[Expr]
    data: Optional[Expr]
    params: Optional[Expr]
    timeout: Optional[Expr]
    response_var: str
    line: int
    column: int


@dataclass
class RouteStmt(Stmt):
    method: str  # 'GET', 'POST', 'PUT', 'DELETE', 'PATCH', '*'
    path: str
    body: BlockStmt
    line: int
    column: int


@dataclass
class UseMiddlewareStmt(Stmt):
    middleware: Expr
    line: int
    column: int


@dataclass
class RespondStmt(Stmt):
    status: Expr
    content_type: str  # 'json', 'text', 'raw'
    payload: Expr
    headers: Optional[Expr]
    line: int
    column: int


@dataclass
class ValidateStmt(Stmt):
    target: str  # 'body', 'query', 'params'
    schema: Expr
    line: int
    column: int


@dataclass
class ServeStmt(Stmt):
    port: Expr
    host: Optional[Expr]
    middlewares: List[Expr]
    routes: List[RouteStmt]
    line: int
    column: int



@dataclass
class PrintStmt(Stmt):
    expressions: List[Expr]
    line: int
    column: int


@dataclass
class ExprStmt(Stmt):
    expression: Expr
    line: int
    column: int


@dataclass
class Program(ASTNode):
    statements: List[Stmt]
    line: int = 1
    column: int = 1
