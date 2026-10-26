"""Static Analysis & Industrial Linter for Lyslyn."""
import os
from typing import List, Dict, Set, Optional, Tuple
from .ast_nodes import (
    Program, Stmt, Expr,
    BlockStmt, SetStmt, ChangeStmt, IfStmt, WhileStmt,
    ForStmt, RepeatStmt, FunctionStmt, ReturnStmt,
    BreakStmt, ContinueStmt, TryStmt, RaiseStmt,
    HttpStmt, ServeStmt, RouteStmt,
    VariableExpr, LiteralExpr, BinaryExpr, CallExpr
)
from .diagnostics import highlight_code_line


class LintWarning:
    def __init__(self, rule: str, message: str, line: int, column: int, suggestion: Optional[str] = None):
        self.rule = rule
        self.message = message
        self.line = line
        self.column = column
        self.suggestion = suggestion


class Linter:
    def __init__(self, filename: str = "<input>", source: str = ""):
        self.filename = filename
        self.source = source
        self.warnings: List[LintWarning] = []
        self.defined_variables: Set[str] = set()
        self.used_variables: Set[str] = set()

    def lint(self, program: Program) -> List[LintWarning]:
        self.warnings = []
        self.defined_variables = set()
        self.used_variables = set()

        for stmt in program.statements:
            self.visit_stmt(stmt)

        return self.warnings

    def visit_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, BlockStmt):
            self.check_unreachable_code(stmt.statements)
            for s in stmt.statements:
                self.visit_stmt(s)

        elif isinstance(stmt, SetStmt):
            if isinstance(stmt.target, VariableExpr):
                self.defined_variables.add(stmt.target.name)
            self.visit_expr(stmt.value)

        elif isinstance(stmt, IfStmt):
            for cond, body in stmt.branches:
                if isinstance(cond, LiteralExpr) and cond.value is False:
                    self.warnings.append(LintWarning(
                        rule="dead-branch",
                        message="Condition is constant 'false'; this block will never execute",
                        line=cond.line,
                        column=cond.column,
                        suggestion="Remove dead branch or correct condition"
                    ))
                self.visit_expr(cond)
                self.visit_stmt(body)
            if stmt.otherwise_branch:
                self.visit_stmt(stmt.otherwise_branch)

        elif isinstance(stmt, WhileStmt):
            if isinstance(stmt.condition, LiteralExpr) and stmt.condition.value is False:
                self.warnings.append(LintWarning(
                    rule="dead-loop",
                    message="While condition is constant 'false'; loop body is unreachable",
                    line=stmt.condition.line,
                    column=stmt.condition.column
                ))
            self.visit_expr(stmt.condition)
            self.visit_stmt(stmt.body)

        elif isinstance(stmt, FunctionStmt):
            if not stmt.body.statements:
                self.warnings.append(LintWarning(
                    rule="empty-function",
                    message=f"Function '{stmt.name}' has an empty body",
                    line=stmt.line,
                    column=stmt.column,
                    suggestion="Add implementation or return statement"
                ))
            self.visit_stmt(stmt.body)

        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                self.visit_expr(stmt.value)

        elif isinstance(stmt, RaiseStmt):
            self.visit_expr(stmt.expression)

        elif isinstance(stmt, ServeStmt):
            self.visit_expr(stmt.port)
            for r in stmt.routes:
                self.visit_stmt(r)

        elif isinstance(stmt, RouteStmt):
            self.visit_stmt(stmt.body)

    def visit_expr(self, expr: Expr) -> None:
        if isinstance(expr, VariableExpr):
            self.used_variables.add(expr.name)
        elif isinstance(expr, BinaryExpr):
            self.visit_expr(expr.left)
            self.visit_expr(expr.right)
        elif isinstance(expr, CallExpr):
            self.visit_expr(expr.callee)
            for a in expr.arguments:
                self.visit_expr(a)

    def check_unreachable_code(self, statements: List[Stmt]) -> None:
        for i, s in enumerate(statements):
            if isinstance(s, (ReturnStmt, RaiseStmt, BreakStmt, ContinueStmt)):
                if i + 1 < len(statements):
                    next_stmt = statements[i + 1]
                    self.warnings.append(LintWarning(
                        rule="unreachable-code",
                        message=f"Unreachable statement after '{type(s).__name__.replace('Stmt', '').lower()}'",
                        line=next_stmt.line,
                        column=next_stmt.column,
                        suggestion="Remove unreachable code"
                    ))
                break

    def format_warnings(self) -> str:
        if not self.warnings:
            return f"\033[92m✓\033[0m No lint issues detected in \033[1m{self.filename}\033[0m."

        lines = [f"\033[1mFound {len(self.warnings)} warning(s) in {self.filename}:\033[0m\n"]
        for w in self.warnings:
            header = f"  \033[93m⚠ [{w.rule}]\033[0m {w.message} at line {w.line}, column {w.column}"
            lines.append(header)
            if self.source:
                src_lines = self.source.splitlines()
                if 1 <= w.line <= len(src_lines):
                    line_str = src_lines[w.line - 1]
                    lines.append(f"     {w.line:>4} │ {highlight_code_line(line_str)}")
                    lines.append(f"          │ {' ' * max(0, w.column - 1)}\033[93m^\033[0m")
            if w.suggestion:
                lines.append(f"     \033[96m💡 {w.suggestion}\033[0m")
            lines.append("")
        return "\n".join(lines)
