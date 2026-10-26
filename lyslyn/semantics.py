"""Semantic analysis and validation for Lyslyn AST."""
from typing import List, Optional, Set
from .ast_nodes import (
    ASTNode, Program, Stmt, Expr,
    BlockStmt, SetStmt, ChangeStmt, IfStmt, WhileStmt,
    ForStmt, RepeatStmt, FunctionStmt, ReturnStmt, AssertStmt,
    BreakStmt, ContinueStmt, TryStmt, RaiseStmt,
    ImportStmt, HttpStmt, PrintStmt, ExprStmt,
    BinaryExpr, UnaryExpr, VariableExpr, LiteralExpr,
    CallExpr, MemberAccessExpr, IndexAccessExpr,
    ListExpr, MapExpr, StringInterpolationExpr, AskExpr,
    ConditionalExpr,
    ServeStmt, RouteStmt, UseMiddlewareStmt, RespondStmt, ValidateStmt
)
from .diagnostics import SemanticError


class SemanticAnalyzer:
    def __init__(self, filename: str = "<input>", source: str = ""):
        self.filename = filename
        self.source = source
        self.loop_depth = 0
        self.function_depth = 0
        self.constants: Set[str] = set()

    def analyze(self, program: Program) -> None:
        for stmt in program.statements:
            self.visit_stmt(stmt)

    def visit_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, BlockStmt):
            for s in stmt.statements:
                self.visit_stmt(s)

        elif isinstance(stmt, SetStmt):
            if stmt.is_constant and isinstance(stmt.target, VariableExpr):
                if stmt.target.name in self.constants:
                    raise SemanticError(
                        f"Constant '{stmt.target.name}' has already been declared",
                        line=stmt.line,
                        column=stmt.column,
                        filename=self.filename,
                        source=self.source
                    )
                self.constants.add(stmt.target.name)
            elif isinstance(stmt.target, VariableExpr):
                if stmt.target.name in self.constants:
                    raise SemanticError(
                        f"Cannot reassign to constant '{stmt.target.name}'",
                        line=stmt.line,
                        column=stmt.column,
                        filename=self.filename,
                        source=self.source
                    )
            self.visit_expr(stmt.value)

        elif isinstance(stmt, ChangeStmt):
            if isinstance(stmt.target, VariableExpr) and stmt.target.name in self.constants:
                raise SemanticError(
                    f"Cannot modify constant '{stmt.target.name}'",
                    line=stmt.line,
                    column=stmt.column,
                    filename=self.filename,
                    source=self.source
                )
            self.visit_expr(stmt.value)

        elif isinstance(stmt, IfStmt):
            for cond, body in stmt.branches:
                self.visit_expr(cond)
                self.visit_stmt(body)
            if stmt.otherwise_branch:
                self.visit_stmt(stmt.otherwise_branch)

        elif isinstance(stmt, WhileStmt):
            self.visit_expr(stmt.condition)
            self.loop_depth += 1
            try:
                self.visit_stmt(stmt.body)
            finally:
                self.loop_depth -= 1

        elif isinstance(stmt, ForStmt):
            self.visit_expr(stmt.iterable)
            self.loop_depth += 1
            try:
                self.visit_stmt(stmt.body)
            finally:
                self.loop_depth -= 1

        elif isinstance(stmt, RepeatStmt):
            self.visit_expr(stmt.count)
            self.loop_depth += 1
            try:
                self.visit_stmt(stmt.body)
            finally:
                self.loop_depth -= 1

        elif isinstance(stmt, FunctionStmt):
            self.function_depth += 1
            try:
                self.visit_stmt(stmt.body)
            finally:
                self.function_depth -= 1

        elif isinstance(stmt, ReturnStmt):
            if self.function_depth == 0:
                raise SemanticError(
                    "Cannot 'return' outside of a function",
                    line=stmt.line,
                    column=stmt.column,
                    filename=self.filename,
                    source=self.source,
                    suggestion="Move return statement into a function body"
                )
            if stmt.value:
                self.visit_expr(stmt.value)

        elif isinstance(stmt, BreakStmt):
            if self.loop_depth == 0:
                raise SemanticError(
                    "Cannot 'break' outside of a loop",
                    line=stmt.line,
                    column=stmt.column,
                    filename=self.filename,
                    source=self.source
                )

        elif isinstance(stmt, ContinueStmt):
            if self.loop_depth == 0:
                raise SemanticError(
                    "Cannot 'continue' outside of a loop",
                    line=stmt.line,
                    column=stmt.column,
                    filename=self.filename,
                    source=self.source
                )

        elif isinstance(stmt, TryStmt):
            self.visit_stmt(stmt.try_block)
            if stmt.catch_block:
                self.visit_stmt(stmt.catch_block)
            if stmt.finally_block:
                self.visit_stmt(stmt.finally_block)

        elif isinstance(stmt, RaiseStmt):
            self.visit_expr(stmt.expression)

        elif isinstance(stmt, HttpStmt):
            self.visit_expr(stmt.url)
            if stmt.headers:
                self.visit_expr(stmt.headers)
            if stmt.data:
                self.visit_expr(stmt.data)
            if stmt.params:
                self.visit_expr(stmt.params)
            if stmt.timeout:
                self.visit_expr(stmt.timeout)

        elif isinstance(stmt, ServeStmt):
            self.visit_expr(stmt.port)
            if stmt.host:
                self.visit_expr(stmt.host)
            for m in stmt.middlewares:
                self.visit_expr(m)
            for r in stmt.routes:
                self.visit_stmt(r)

        elif isinstance(stmt, RouteStmt):
            self.visit_stmt(stmt.body)

        elif isinstance(stmt, UseMiddlewareStmt):
            self.visit_expr(stmt.middleware)

        elif isinstance(stmt, RespondStmt):
            self.visit_expr(stmt.status)
            self.visit_expr(stmt.payload)
            if stmt.headers:
                self.visit_expr(stmt.headers)

        elif isinstance(stmt, ValidateStmt):
            self.visit_expr(stmt.schema)

        elif isinstance(stmt, PrintStmt):
            for e in stmt.expressions:
                self.visit_expr(e)

        elif isinstance(stmt, AssertStmt):
            self.visit_expr(stmt.condition)
            if stmt.message:
                self.visit_expr(stmt.message)

        elif isinstance(stmt, ExprStmt):
            self.visit_expr(stmt.expression)

    def visit_expr(self, expr: Expr) -> None:
        if isinstance(expr, BinaryExpr):
            self.visit_expr(expr.left)
            self.visit_expr(expr.right)
        elif isinstance(expr, UnaryExpr):
            self.visit_expr(expr.operand)
        elif isinstance(expr, CallExpr):
            self.visit_expr(expr.callee)
            for a in expr.arguments:
                self.visit_expr(a)
        elif isinstance(expr, MemberAccessExpr):
            self.visit_expr(expr.target)
        elif isinstance(expr, IndexAccessExpr):
            self.visit_expr(expr.target)
            self.visit_expr(expr.index)
        elif isinstance(expr, ListExpr):
            for e in expr.elements:
                self.visit_expr(e)
        elif isinstance(expr, MapExpr):
            for k, v in expr.entries:
                self.visit_expr(k)
                self.visit_expr(v)
        elif isinstance(expr, StringInterpolationExpr):
            for p in expr.parts:
                if isinstance(p, Expr):
                    self.visit_expr(p)
        elif isinstance(expr, AskExpr):
            if expr.prompt:
                self.visit_expr(expr.prompt)
        elif isinstance(expr, ConditionalExpr):
            self.visit_expr(expr.condition)
            self.visit_expr(expr.then_expr)
            self.visit_expr(expr.else_expr)
