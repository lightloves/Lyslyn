"""AST to Bytecode Compiler for the Lyslyn language."""
from typing import Any, Dict, List, Optional, Tuple
from .ast_nodes import (
    Program, Stmt, Expr,
    BlockStmt, SetStmt, ChangeStmt, IfStmt, WhileStmt,
    ForStmt, RepeatStmt, FunctionStmt, ReturnStmt,
    BreakStmt, ContinueStmt, PrintStmt, ExprStmt,
    BinaryExpr, UnaryExpr, VariableExpr, LiteralExpr,
    CallExpr, MemberAccessExpr, IndexAccessExpr,
    ListExpr, MapExpr, StringInterpolationExpr, ConditionalExpr
)
from .opcodes import OpCode
from .chunk import Chunk
from .diagnostics import SemanticError


class Local:
    def __init__(self, name: str, depth: int):
        self.name = name
        self.depth = depth


class Compiler:
    def __init__(self, filename: str = "<input>", source: str = ""):
        self.filename = filename
        self.source = source
        self.chunk: Chunk = Chunk("<main>")
        self.locals: List[Local] = []
        self.scope_depth: int = 0
        self.loop_stack: List[Tuple[int, List[int]]] = []  # (loop_start, break_jump_offsets)

    def compile(self, program: Program) -> Chunk:
        self.chunk = Chunk("<main>")
        self.locals = []
        self.scope_depth = 0
        self.loop_stack = []

        for stmt in program.statements:
            self.compile_stmt(stmt)

        self.emit_byte(OpCode.OP_HALT, program.line)
        return self.chunk

    # ========================================================================
    # Statements
    # ========================================================================

    def compile_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, BlockStmt):
            self.begin_scope()
            for s in stmt.statements:
                self.compile_stmt(s)
            self.end_scope(stmt.line)

        elif isinstance(stmt, SetStmt):
            self.compile_set(stmt)

        elif isinstance(stmt, ChangeStmt):
            self.compile_change(stmt)

        elif isinstance(stmt, IfStmt):
            self.compile_if(stmt)

        elif isinstance(stmt, WhileStmt):
            self.compile_while(stmt)

        elif isinstance(stmt, ForStmt):
            self.compile_for(stmt)

        elif isinstance(stmt, RepeatStmt):
            self.compile_repeat(stmt)

        elif isinstance(stmt, FunctionStmt):
            self.compile_function(stmt)

        elif isinstance(stmt, ReturnStmt):
            self.compile_return(stmt)

        elif isinstance(stmt, BreakStmt):
            if not self.loop_stack:
                raise SemanticError("Cannot break outside loop", line=stmt.line, column=stmt.column)
            jump_offset = self.emit_jump(OpCode.OP_JUMP, stmt.line)
            self.loop_stack[-1][1].append(jump_offset)

        elif isinstance(stmt, ContinueStmt):
            if not self.loop_stack:
                raise SemanticError("Cannot continue outside loop", line=stmt.line, column=stmt.column)
            loop_start = self.loop_stack[-1][0]
            self.emit_loop(loop_start, stmt.line)

        elif isinstance(stmt, PrintStmt):
            for expr in stmt.expressions:
                self.compile_expr(expr)
            self.emit_bytes(OpCode.OP_PRINT, len(stmt.expressions), stmt.line)

        elif isinstance(stmt, ExprStmt):
            self.compile_expr(stmt.expression)
            self.emit_byte(OpCode.OP_POP, stmt.line)

    def compile_set(self, stmt: SetStmt) -> None:
        self.compile_expr(stmt.value)
        target = stmt.target

        if isinstance(target, VariableExpr):
            if self.scope_depth > 0:
                # Local variable
                local_idx = self.resolve_local(target.name)
                if local_idx is not None:
                    self.emit_bytes(OpCode.OP_SET_LOCAL, local_idx, stmt.line)
                else:
                    self.add_local(target.name)
            else:
                # Global variable
                const_idx = self.chunk.add_constant(target.name)
                self.emit_bytes(OpCode.OP_DEF_GLOBAL, const_idx, stmt.line)

        elif isinstance(target, IndexAccessExpr):
            self.compile_expr(target.target)
            self.compile_expr(target.index)
            self.emit_byte(OpCode.OP_INDEX_SET, stmt.line)

        elif isinstance(target, MemberAccessExpr):
            self.compile_expr(target.target)
            const_prop = self.chunk.add_constant(target.member)
            self.emit_bytes(OpCode.OP_CONSTANT, const_prop, stmt.line)
            self.emit_byte(OpCode.OP_INDEX_SET, stmt.line)

    def compile_change(self, stmt: ChangeStmt) -> None:
        target = stmt.target
        # Push current target value
        if isinstance(target, VariableExpr):
            local_idx = self.resolve_local(target.name) if self.scope_depth > 0 else None
            if local_idx is not None:
                self.emit_bytes(OpCode.OP_GET_LOCAL, local_idx, stmt.line)
            else:
                const_name = self.chunk.add_constant(target.name)
                self.emit_bytes(OpCode.OP_GET_GLOBAL, const_name, stmt.line)
        else:
            self.compile_expr(target)

        # Push delta and apply operation
        self.compile_expr(stmt.value)
        if stmt.operation == "increase":
            self.emit_byte(OpCode.OP_ADD, stmt.line)
        elif stmt.operation == "decrease":
            self.emit_byte(OpCode.OP_SUB, stmt.line)

        # Write back to target
        if isinstance(target, VariableExpr):
            if local_idx is not None:
                self.emit_bytes(OpCode.OP_SET_LOCAL, local_idx, stmt.line)
            else:
                const_name = self.chunk.add_constant(target.name)
                self.emit_bytes(OpCode.OP_SET_GLOBAL, const_name, stmt.line)

    def compile_if(self, stmt: IfStmt) -> None:
        else_jumps: List[int] = []

        for cond_expr, body in stmt.branches:
            self.compile_expr(cond_expr)
            jump_false = self.emit_jump(OpCode.OP_JUMP_IF_FALSE, stmt.line)
            self.emit_byte(OpCode.OP_POP, stmt.line)  # Pop condition if truthy

            self.compile_stmt(body)

            jump_end = self.emit_jump(OpCode.OP_JUMP, stmt.line)
            else_jumps.append(jump_end)

            self.patch_jump(jump_false)
            self.emit_byte(OpCode.OP_POP, stmt.line)  # Pop condition if falsy

        if stmt.otherwise_branch:
            self.compile_stmt(stmt.otherwise_branch)

        for j in else_jumps:
            self.patch_jump(j)

    def compile_while(self, stmt: WhileStmt) -> None:
        loop_start = len(self.chunk.code)
        self.loop_stack.append((loop_start, []))

        self.compile_expr(stmt.condition)
        exit_jump = self.emit_jump(OpCode.OP_JUMP_IF_FALSE, stmt.line)
        self.emit_byte(OpCode.OP_POP, stmt.line)

        self.compile_stmt(stmt.body)

        self.emit_loop(loop_start, stmt.line)
        self.patch_jump(exit_jump)
        self.emit_byte(OpCode.OP_POP, stmt.line)

        _, break_jumps = self.loop_stack.pop()
        for bj in break_jumps:
            self.patch_jump(bj)

    def compile_repeat(self, stmt: RepeatStmt) -> None:
        # Desugar repeat N times into while loop with internal counter
        self.begin_scope()
        self.compile_expr(stmt.count)
        count_slot = self.add_local("__count")

        self.emit_byte(OpCode.OP_CONSTANT, stmt.line)
        self.chunk.code.append(self.chunk.add_constant(0))
        self.chunk.lines.append(stmt.line)
        iter_slot = self.add_local("__i")

        loop_start = len(self.chunk.code)
        self.loop_stack.append((loop_start, []))

        self.emit_bytes(OpCode.OP_GET_LOCAL, iter_slot, stmt.line)
        self.emit_bytes(OpCode.OP_GET_LOCAL, count_slot, stmt.line)
        self.emit_byte(OpCode.OP_LESS, stmt.line)

        exit_jump = self.emit_jump(OpCode.OP_JUMP_IF_FALSE, stmt.line)
        self.emit_byte(OpCode.OP_POP, stmt.line)

        self.compile_stmt(stmt.body)

        # Increment __i
        self.emit_bytes(OpCode.OP_GET_LOCAL, iter_slot, stmt.line)
        self.emit_bytes(OpCode.OP_CONSTANT, self.chunk.add_constant(1), stmt.line)
        self.emit_byte(OpCode.OP_ADD, stmt.line)
        self.emit_bytes(OpCode.OP_SET_LOCAL, iter_slot, stmt.line)

        self.emit_loop(loop_start, stmt.line)
        self.patch_jump(exit_jump)
        self.emit_byte(OpCode.OP_POP, stmt.line)

        _, break_jumps = self.loop_stack.pop()
        for bj in break_jumps:
            self.patch_jump(bj)

        self.end_scope(stmt.line)

    def compile_for(self, stmt: ForStmt) -> None:
        # Desugar for-in: evaluates iterable, indexes from 0 to len
        self.begin_scope()
        self.compile_expr(stmt.iterable)
        list_slot = self.add_local("__list")

        self.emit_bytes(OpCode.OP_CONSTANT, self.chunk.add_constant(0), stmt.line)
        idx_slot = self.add_local("__idx")

        # Local variable for current item
        self.emit_byte(OpCode.OP_NIL, stmt.line)
        item_slot = self.add_local(stmt.variable)

        loop_start = len(self.chunk.code)
        self.loop_stack.append((loop_start, []))

        # Check: idx < list.length
        self.emit_bytes(OpCode.OP_GET_LOCAL, idx_slot, stmt.line)
        self.emit_bytes(OpCode.OP_GET_LOCAL, list_slot, stmt.line)
        const_len = self.chunk.add_constant("length")
        self.emit_bytes(OpCode.OP_CONSTANT, const_len, stmt.line)
        self.emit_byte(OpCode.OP_INDEX_GET, stmt.line)
        self.emit_byte(OpCode.OP_LESS, stmt.line)

        exit_jump = self.emit_jump(OpCode.OP_JUMP_IF_FALSE, stmt.line)
        self.emit_byte(OpCode.OP_POP, stmt.line)

        # Set item = list[idx]
        self.emit_bytes(OpCode.OP_GET_LOCAL, list_slot, stmt.line)
        self.emit_bytes(OpCode.OP_GET_LOCAL, idx_slot, stmt.line)
        self.emit_byte(OpCode.OP_INDEX_GET, stmt.line)
        self.emit_bytes(OpCode.OP_SET_LOCAL, item_slot, stmt.line)

        self.compile_stmt(stmt.body)

        # Increment idx
        self.emit_bytes(OpCode.OP_GET_LOCAL, idx_slot, stmt.line)
        self.emit_bytes(OpCode.OP_CONSTANT, self.chunk.add_constant(1), stmt.line)
        self.emit_byte(OpCode.OP_ADD, stmt.line)
        self.emit_bytes(OpCode.OP_SET_LOCAL, idx_slot, stmt.line)

        self.emit_loop(loop_start, stmt.line)
        self.patch_jump(exit_jump)
        self.emit_byte(OpCode.OP_POP, stmt.line)

        _, break_jumps = self.loop_stack.pop()
        for bj in break_jumps:
            self.patch_jump(bj)

        self.end_scope(stmt.line)

    def compile_function(self, stmt: FunctionStmt) -> None:
        sub_compiler = Compiler(filename=self.filename, source=self.source)
        sub_compiler.chunk.name = stmt.name
        sub_compiler.scope_depth = 1

        # Parameters are the first local variables
        for param in stmt.params:
            sub_compiler.add_local(param)

        for s in stmt.body.statements:
            sub_compiler.compile_stmt(s)

        # Implicit return nil
        sub_compiler.emit_byte(OpCode.OP_NIL, stmt.line)
        sub_compiler.emit_byte(OpCode.OP_RETURN, stmt.line)

        sub_chunk = sub_compiler.chunk
        const_fn = self.chunk.add_constant({
            "type": "function",
            "name": stmt.name,
            "params": stmt.params,
            "chunk": sub_chunk.serialize().hex()
        })
        self.emit_bytes(OpCode.OP_CONSTANT, const_fn, stmt.line)

        const_name = self.chunk.add_constant(stmt.name)
        self.emit_bytes(OpCode.OP_DEF_GLOBAL, const_name, stmt.line)

    def compile_return(self, stmt: ReturnStmt) -> None:
        if stmt.value:
            self.compile_expr(stmt.value)
        else:
            self.emit_byte(OpCode.OP_NIL, stmt.line)
        self.emit_byte(OpCode.OP_RETURN, stmt.line)

    # ========================================================================
    # Expressions
    # ========================================================================

    def compile_expr(self, expr: Expr) -> None:
        if isinstance(expr, LiteralExpr):
            if expr.value is None:
                self.emit_byte(OpCode.OP_NIL, expr.line)
            elif expr.value is True:
                self.emit_byte(OpCode.OP_TRUE, expr.line)
            elif expr.value is False:
                self.emit_byte(OpCode.OP_FALSE, expr.line)
            else:
                const_idx = self.chunk.add_constant(expr.value)
                self.emit_bytes(OpCode.OP_CONSTANT, const_idx, expr.line)

        elif isinstance(expr, VariableExpr):
            local_idx = self.resolve_local(expr.name) if self.scope_depth > 0 else None
            if local_idx is not None:
                self.emit_bytes(OpCode.OP_GET_LOCAL, local_idx, expr.line)
            else:
                const_name = self.chunk.add_constant(expr.name)
                self.emit_bytes(OpCode.OP_GET_GLOBAL, const_name, expr.line)

        elif isinstance(expr, BinaryExpr):
            self.compile_binary(expr)

        elif isinstance(expr, UnaryExpr):
            self.compile_expr(expr.operand)
            if expr.operator == "-":
                self.emit_byte(OpCode.OP_NEG, expr.line)
            elif expr.operator in ("not", "!"):
                self.emit_byte(OpCode.OP_NOT, expr.line)

        elif isinstance(expr, CallExpr):
            self.compile_expr(expr.callee)
            for arg in expr.arguments:
                self.compile_expr(arg)
            self.emit_bytes(OpCode.OP_CALL, len(expr.arguments), expr.line)

        elif isinstance(expr, MemberAccessExpr):
            self.compile_expr(expr.target)
            const_prop = self.chunk.add_constant(expr.member)
            self.emit_bytes(OpCode.OP_CONSTANT, const_prop, expr.line)
            self.emit_byte(OpCode.OP_INDEX_GET, expr.line)

        elif isinstance(expr, IndexAccessExpr):
            self.compile_expr(expr.target)
            self.compile_expr(expr.index)
            self.emit_byte(OpCode.OP_INDEX_GET, expr.line)

        elif isinstance(expr, ListExpr):
            for e in expr.elements:
                self.compile_expr(e)
            self.emit_bytes(OpCode.OP_BUILD_LIST, len(expr.elements), expr.line)

        elif isinstance(expr, MapExpr):
            for k_expr, v_expr in expr.entries:
                self.compile_expr(k_expr)
                self.compile_expr(v_expr)
            self.emit_bytes(OpCode.OP_BUILD_MAP, len(expr.entries), expr.line)

        elif isinstance(expr, StringInterpolationExpr):
            # Concatenate all parts with +
            if not expr.parts:
                self.emit_bytes(OpCode.OP_CONSTANT, self.chunk.add_constant(""), expr.line)
                return
            for i, part in enumerate(expr.parts):
                if isinstance(part, str):
                    self.emit_bytes(OpCode.OP_CONSTANT, self.chunk.add_constant(part), expr.line)
                else:
                    self.compile_expr(part)
                if i > 0:
                    self.emit_byte(OpCode.OP_ADD, expr.line)

        elif isinstance(expr, ConditionalExpr):
            self.compile_expr(expr.condition)
            jump_false = self.emit_jump(OpCode.OP_JUMP_IF_FALSE, expr.line)
            self.emit_byte(OpCode.OP_POP, expr.line)
            self.compile_expr(expr.then_expr)
            jump_end = self.emit_jump(OpCode.OP_JUMP, expr.line)
            self.patch_jump(jump_false)
            self.emit_byte(OpCode.OP_POP, expr.line)
            self.compile_expr(expr.else_expr)
            self.patch_jump(jump_end)

    def compile_binary(self, expr: BinaryExpr) -> None:
        op = expr.operator
        if op == "and":
            self.compile_expr(expr.left)
            end_jump = self.emit_jump(OpCode.OP_JUMP_IF_FALSE, expr.line)
            self.emit_byte(OpCode.OP_POP, expr.line)
            self.compile_expr(expr.right)
            self.patch_jump(end_jump)
            return

        if op == "or":
            self.compile_expr(expr.left)
            else_jump = self.emit_jump(OpCode.OP_JUMP_IF_FALSE, expr.line)
            end_jump = self.emit_jump(OpCode.OP_JUMP, expr.line)
            self.patch_jump(else_jump)
            self.emit_byte(OpCode.OP_POP, expr.line)
            self.compile_expr(expr.right)
            self.patch_jump(end_jump)
            return

        self.compile_expr(expr.left)
        self.compile_expr(expr.right)

        if op == "+":
            self.emit_byte(OpCode.OP_ADD, expr.line)
        elif op == "-":
            self.emit_byte(OpCode.OP_SUB, expr.line)
        elif op == "*":
            self.emit_byte(OpCode.OP_MUL, expr.line)
        elif op == "/":
            self.emit_byte(OpCode.OP_DIV, expr.line)
        elif op == "%":
            self.emit_byte(OpCode.OP_MOD, expr.line)
        elif op in ("==", "equals"):
            self.emit_byte(OpCode.OP_EQUAL, expr.line)
        elif op in ("!=", "does not equal"):
            self.emit_byte(OpCode.OP_EQUAL, expr.line)
            self.emit_byte(OpCode.OP_NOT, expr.line)
        elif op == ">":
            self.emit_byte(OpCode.OP_GREATER, expr.line)
        elif op == "<":
            self.emit_byte(OpCode.OP_LESS, expr.line)
        elif op == ">=":
            self.emit_byte(OpCode.OP_LESS, expr.line)
            self.emit_byte(OpCode.OP_NOT, expr.line)
        elif op == "<=":
            self.emit_byte(OpCode.OP_GREATER, expr.line)
            self.emit_byte(OpCode.OP_NOT, expr.line)

    # ========================================================================
    # Helpers
    # ========================================================================

    def emit_byte(self, byte_val: int, line: int) -> int:
        return self.chunk.write(byte_val, line)

    def emit_bytes(self, byte1: int, byte2: int, line: int) -> None:
        self.emit_byte(byte1, line)
        self.emit_byte(byte2, line)

    def emit_jump(self, instruction: int, line: int) -> int:
        self.emit_byte(instruction, line)
        self.emit_byte(0xFF, line)
        self.emit_byte(0xFF, line)
        return len(self.chunk.code) - 2

    def patch_jump(self, offset: int) -> None:
        jump = len(self.chunk.code) - offset - 2
        if jump > 65535:
            raise RuntimeError("Bytecode jump distance exceeds 16-bit offset")
        self.chunk.code[offset] = (jump >> 8) & 0xFF
        self.chunk.code[offset + 1] = jump & 0xFF

    def emit_loop(self, loop_start: int, line: int) -> None:
        self.emit_byte(OpCode.OP_LOOP, line)
        offset = len(self.chunk.code) - loop_start + 2
        if offset > 65535:
            raise RuntimeError("Loop body too large for 16-bit offset")
        self.emit_byte((offset >> 8) & 0xFF, line)
        self.emit_byte(offset & 0xFF, line)

    def begin_scope(self) -> None:
        self.scope_depth += 1

    def end_scope(self, line: int) -> None:
        self.scope_depth -= 1
        while self.locals and self.locals[-1].depth > self.scope_depth:
            self.emit_byte(OpCode.OP_POP, line)
            self.locals.pop()

    def add_local(self, name: str) -> int:
        self.locals.append(Local(name, self.scope_depth))
        return len(self.locals) - 1

    def resolve_local(self, name: str) -> Optional[int]:
        for i in range(len(self.locals) - 1, -1, -1):
            if self.locals[i].name == name:
                return i
        return None
