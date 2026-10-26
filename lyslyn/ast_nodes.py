"""Abstract Syntax Tree node definitions for Lyslyn."""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any, Union


class ASTNode:
    """Base class for all AST nodes."""
    line: int
    column: int


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
    operator: str
    right: Expr
    line: int
    column: int


@dataclass
class UnaryExpr(Expr):
    operator: str
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
    entries: List[Tuple[Expr, Expr]]
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


class Stmt(ASTNode):
    pass


@dataclass
class BlockStmt(Stmt):
    statements: List[Stmt]
    line: int
    column: int


@dataclass
class SetStmt(Stmt):
    target: Expr
    value: Expr
    is_constant: bool
    line: int
    column: int


@dataclass
class ChangeStmt(Stmt):
    target: Expr
    operation: str
    value: Expr
    line: int
    column: int


@dataclass
class IfStmt(Stmt):
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
    imported_names: Optional[List[str]]
    line: int
    column: int


@dataclass
class HttpStmt(Stmt):
    method: str
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
    method: str
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
    content_type: str
    payload: Expr
    headers: Optional[Expr]
    line: int
    column: int


@dataclass
class ValidateStmt(Stmt):
    target: str
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
