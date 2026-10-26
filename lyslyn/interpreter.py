"""Tree-walking AST Interpreter for Lyslyn."""
import os
import sys
from typing import Any, List, Dict, Optional, Union
from .ast_nodes import (
    ASTNode, Program, Stmt, Expr,
    BlockStmt, SetStmt, ChangeStmt, IfStmt, WhileStmt,
    ForStmt, RepeatStmt, FunctionStmt, ReturnStmt,
    BreakStmt, ContinueStmt, TryStmt, RaiseStmt,
    ImportStmt, HttpStmt, PrintStmt, ExprStmt, AssertStmt,
    BinaryExpr, UnaryExpr, VariableExpr, LiteralExpr,
    CallExpr, MemberAccessExpr, IndexAccessExpr,
    ListExpr, MapExpr, StringInterpolationExpr, AskExpr,
    ConditionalExpr,
    ServeStmt, RouteStmt, UseMiddlewareStmt, RespondStmt, ValidateStmt
)
from .tokens import Token
from .environment import Environment
from .values import (
    LyslynFunction, LyslynBuiltin, LyslynModule, LyslynHttpResponse,
    ReturnSignal, BreakSignal, ContinueSignal, RespondSignal
)
from .builtins import get_global_builtins
from .stdlib import get_stdlib_module
from .diagnostics import RuntimeError_


class Interpreter:
    def __init__(self, filename: str = "<input>", source: str = ""):
        self.filename = filename
        self.source = source
        self.globals = Environment()
        self.environment = self.globals
        self.call_stack: List[str] = ["<main>"]

        for name, builtin in get_global_builtins().items():
            self.globals.define(name, builtin, is_constant=True)

    def interpret(self, program: Program) -> Any:
        result = None
        try:
            for stmt in program.statements:
                result = self.execute(stmt)
            return result
        except (ReturnSignal, BreakSignal, ContinueSignal) as e:
            raise RuntimeError_(
                f"Unexpected control flow: {type(e).__name__}",
                line=program.line,
                column=program.column,
                filename=self.filename,
                source=self.source
            )
        except RuntimeError_ as e:
            raise e
        except Exception as e:
            line = getattr(self, "current_line", 1)
            col = getattr(self, "current_col", 1)
            raise RuntimeError_(
                str(e),
                line=line,
                column=col,
                filename=self.filename,
                source=self.source
            )


    def execute(self, stmt: Stmt) -> Any:
        self.current_line = stmt.line
        self.current_col = stmt.column

        if isinstance(stmt, BlockStmt):
            return self.execute_block(stmt)
        elif isinstance(stmt, SetStmt):
            return self.execute_set(stmt)
        elif isinstance(stmt, ChangeStmt):
            return self.execute_change(stmt)
        elif isinstance(stmt, IfStmt):
            return self.execute_if(stmt)
        elif isinstance(stmt, WhileStmt):
            return self.execute_while(stmt)
        elif isinstance(stmt, ForStmt):
            return self.execute_for(stmt)
        elif isinstance(stmt, RepeatStmt):
            return self.execute_repeat(stmt)
        elif isinstance(stmt, FunctionStmt):
            return self.execute_function(stmt)
        elif isinstance(stmt, ReturnStmt):
            return self.execute_return(stmt)
        elif isinstance(stmt, BreakStmt):
            raise BreakSignal()
        elif isinstance(stmt, ContinueStmt):
            raise ContinueSignal()
        elif isinstance(stmt, TryStmt):
            return self.execute_try(stmt)
        elif isinstance(stmt, RaiseStmt):
            return self.execute_raise(stmt)
        elif isinstance(stmt, ImportStmt):
            return self.execute_import(stmt)
        elif isinstance(stmt, HttpStmt):
            return self.execute_http(stmt)
        elif isinstance(stmt, ServeStmt):
            return self.execute_serve(stmt)
        elif isinstance(stmt, RouteStmt):
            return self.execute_route(stmt)
        elif isinstance(stmt, UseMiddlewareStmt):
            return self.execute_use_middleware(stmt)
        elif isinstance(stmt, RespondStmt):
            return self.execute_respond(stmt)
        elif isinstance(stmt, ValidateStmt):
            return self.execute_validate(stmt)
        elif isinstance(stmt, PrintStmt):
            return self.execute_print(stmt)
        elif isinstance(stmt, AssertStmt):
            return self.execute_assert(stmt)
        elif isinstance(stmt, ExprStmt):
            return self.evaluate(stmt.expression)
        else:
            raise RuntimeError_(f"Unknown statement type {type(stmt).__name__}", line=stmt.line, column=stmt.column)

    def execute_block(self, block: BlockStmt, env: Optional[Environment] = None) -> Any:
        previous_env = self.environment
        if env is not None:
            self.environment = env
        try:
            result = None
            for s in block.statements:
                result = self.execute(s)
            return result
        finally:
            if env is not None:
                self.environment = previous_env

    def execute_set(self, stmt: SetStmt) -> Any:
        value = self.evaluate(stmt.value)
        target = stmt.target

        if isinstance(target, VariableExpr):
            if stmt.is_constant:
                self.environment.define(target.name, value, is_constant=True)
            else:
                if self.environment.contains(target.name):
                    self.environment.assign(target.name, value)
                else:
                    self.environment.define(target.name, value, is_constant=False)
        elif isinstance(target, MemberAccessExpr):
            obj = self.evaluate(target.target)
            if isinstance(obj, dict):
                obj[target.member] = value
            else:
                setattr(obj, target.member, value)
        elif isinstance(target, IndexAccessExpr):
            obj = self.evaluate(target.target)
            idx = self.evaluate(target.index)
            obj[idx] = value
        else:
            raise RuntimeError_(f"Invalid assignment target {type(target).__name__}", line=stmt.line, column=stmt.column)
        return value

    def execute_change(self, stmt: ChangeStmt) -> Any:
        delta = self.evaluate(stmt.value)
        target = stmt.target

        if isinstance(target, VariableExpr):
            curr = self.environment.get(target.name)
            if stmt.operation == "increase":
                new_val = curr + delta
            elif stmt.operation == "decrease":
                new_val = curr - delta
            elif stmt.operation == "change":
                new_val = delta
            else:
                raise RuntimeError_(f"Unknown change operation '{stmt.operation}'", line=stmt.line, column=stmt.column)
            self.environment.assign(target.name, new_val)
            return new_val
        elif isinstance(target, MemberAccessExpr):
            obj = self.evaluate(target.target)
            curr = obj[target.member]
            if stmt.operation == "increase":
                new_val = curr + delta
            elif stmt.operation == "decrease":
                new_val = curr - delta
            else:
                new_val = delta
            obj[target.member] = new_val
            return new_val
        elif isinstance(target, IndexAccessExpr):
            obj = self.evaluate(target.target)
            idx = self.evaluate(target.index)
            curr = obj[idx]
            if stmt.operation == "increase":
                new_val = curr + delta
            elif stmt.operation == "decrease":
                new_val = curr - delta
            else:
                new_val = delta
            obj[idx] = new_val
            return new_val

    def execute_if(self, stmt: IfStmt) -> Any:
        for cond_expr, body in stmt.branches:
            if self.is_truthy(self.evaluate(cond_expr)):
                return self.execute_block(body)
        if stmt.otherwise_branch:
            return self.execute_block(stmt.otherwise_branch)
        return None

    def execute_while(self, stmt: WhileStmt) -> Any:
        result = None
        while self.is_truthy(self.evaluate(stmt.condition)):
            try:
                result = self.execute_block(stmt.body)
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        return result

    def execute_for(self, stmt: ForStmt) -> Any:
        iterable = self.evaluate(stmt.iterable)
        result = None

        if isinstance(iterable, (list, tuple, str)):
            items = iterable
        elif isinstance(iterable, dict):
            items = list(iterable.keys())
        else:
            raise RuntimeError_(f"Cannot iterate over type '{type(iterable).__name__}'", line=stmt.line, column=stmt.column)

        for item in items:
            self.environment.define(stmt.variable, item, is_constant=False)
            try:
                result = self.execute_block(stmt.body)
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        return result

    def execute_repeat(self, stmt: RepeatStmt) -> Any:
        count_val = self.evaluate(stmt.count)
        if not isinstance(count_val, (int, float)):
            raise RuntimeError_(f"Repeat count must be a number, got '{type(count_val).__name__}'", line=stmt.line, column=stmt.column)
        count = int(count_val)
        result = None
        for _ in range(count):
            try:
                result = self.execute_block(stmt.body)
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        return result

    def execute_function(self, stmt: FunctionStmt) -> None:
        func = LyslynFunction(
            name=stmt.name,
            params=stmt.params,
            body=stmt.body,
            closure=self.environment,
            is_async=stmt.is_async,
            interpreter=self
        )
        self.environment.define(stmt.name, func)

    def execute_return(self, stmt: ReturnStmt) -> None:
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)
        raise ReturnSignal(value)

    def execute_try(self, stmt: TryStmt) -> Any:
        try:
            return self.execute_block(stmt.try_block)
        except (ReturnSignal, BreakSignal, ContinueSignal):
            raise
        except Exception as e:
            if stmt.catch_block:
                catch_env = Environment(self.environment)
                if stmt.catch_var:
                    err_msg = str(e)
                    catch_env.define(stmt.catch_var, err_msg)
                return self.execute_block(stmt.catch_block, env=catch_env)
            else:
                raise
        finally:
            if stmt.finally_block:
                self.execute_block(stmt.finally_block)

    def execute_raise(self, stmt: RaiseStmt) -> None:
        val = self.evaluate(stmt.expression)
        raise RuntimeError_(str(val), line=stmt.line, column=stmt.column, filename=self.filename, source=self.source)

    def execute_import(self, stmt: ImportStmt) -> None:
        mod_name = stmt.module_name

        stdlib_mod = get_stdlib_module(mod_name)
        if stdlib_mod is not None:
            if stmt.imported_names:
                for name in stmt.imported_names:
                    val = stdlib_mod.get(name)
                    self.environment.define(name, val)
            else:
                bind_name = stmt.alias or mod_name
                self.environment.define(bind_name, stdlib_mod)
            return

        base_dir = os.path.dirname(self.filename) if self.filename and self.filename != "<input>" else "."
        possible_paths = [
            os.path.join(base_dir, mod_name),
            os.path.join(base_dir, f"{mod_name}.lys"),
            mod_name,
            f"{mod_name}.lys",
        ]
        target_path = None
        for p in possible_paths:
            if os.path.isfile(p):
                target_path = p
                break

        if target_path is None:
            raise RuntimeError_(
                f"Cannot find module '{mod_name}' (checked standard library and file paths)",
                line=stmt.line,
                column=stmt.column,
                filename=self.filename,
                source=self.source
            )

        with open(target_path, "r", encoding="utf-8") as f:
            src = f.read()

        from .lexer import Lexer
        from .parser import Parser

        lexer = Lexer(src, filename=target_path)
        tokens = lexer.tokenize()
        parser = Parser(tokens, filename=target_path, source=src)
        program = parser.parse()

        sub_interp = Interpreter(filename=target_path, source=src)
        sub_interp.interpret(program)

        exports = dict(sub_interp.globals.values)
        mod_obj = LyslynModule(os.path.basename(target_path).replace(".lys", ""), exports)

        if stmt.imported_names:
            for name in stmt.imported_names:
                if name in exports:
                    self.environment.define(name, exports[name])
                else:
                    raise RuntimeError_(f"Module '{mod_name}' does not export '{name}'", line=stmt.line, column=stmt.column)
        else:
            bind_name = stmt.alias or os.path.basename(target_path).replace(".lys", "")
            self.environment.define(bind_name, mod_obj)

    def execute_http(self, stmt: HttpStmt) -> None:
        from .stdlib import http as http_mod
        url = str(self.evaluate(stmt.url))

        options: Dict[str, Any] = {}
        if stmt.headers:
            options["headers"] = self.evaluate(stmt.headers)
        if stmt.data:
            options["data"] = self.evaluate(stmt.data)
        if stmt.params:
            options["params"] = self.evaluate(stmt.params)
        if stmt.timeout:
            options["timeout"] = float(self.evaluate(stmt.timeout))

        resp = http_mod.request(stmt.method, url, options)
        self.environment.define(stmt.response_var, resp)

    def execute_serve(self, stmt: ServeStmt) -> Any:
        from .stdlib.server_mod import ServerApp
        port = int(self.evaluate(stmt.port))
        host = str(self.evaluate(stmt.host)) if stmt.host else "0.0.0.0"

        app = ServerApp()

        for m_expr in stmt.middlewares:
            mid = self.evaluate(m_expr)
            app.use(mid)

        for r_stmt in stmt.routes:
            def make_handler(route_node: RouteStmt):
                def handler(req):
                    req_env = Environment(parent=self.environment)
                    req_dict = {
                        "method": req.method,
                        "path": req.path,
                        "params": req.params,
                        "query": req.query,
                        "headers": req.headers,
                        "body": req.body,
                        "ip": req.ip,
                        "user": getattr(req, "user", None),
                        "context": getattr(req, "context", {})
                    }
                    req_env.define("request", req_dict, is_constant=True)
                    req_env.define("Request", req_dict, is_constant=True)

                    try:
                        self.execute_block(route_node.body, env=req_env)
                        return (200, {"ok": True})
                    except RespondSignal as sig:
                        return (sig.status, sig.payload)
                return handler

            app.add_route(r_stmt.method, r_stmt.path, make_handler(r_stmt))

        blocking = getattr(self, "server_blocking", True)
        self.active_server = app
        app.listen(port=port, host=host, blocking=blocking)
        return app

    def execute_route(self, stmt: RouteStmt) -> None:
        if hasattr(self, "active_server") and self.active_server is not None:
            def handler(req):
                req_env = Environment(parent=self.environment)
                req_dict = {
                    "method": req.method,
                    "path": req.path,
                    "params": req.params,
                    "query": req.query,
                    "headers": req.headers,
                    "body": req.body,
                    "ip": req.ip,
                    "user": getattr(req, "user", None),
                    "context": getattr(req, "context", {})
                }
                req_env.define("request", req_dict, is_constant=True)
                try:
                    self.execute_block(stmt.body, env=req_env)
                    return (200, {"ok": True})
                except RespondSignal as sig:
                    return (sig.status, sig.payload)

            self.active_server.add_route(stmt.method, stmt.path, handler)

    def execute_use_middleware(self, stmt: UseMiddlewareStmt) -> None:
        mid = self.evaluate(stmt.middleware)
        if hasattr(self, "active_server") and self.active_server is not None:
            self.active_server.use(mid)

    def execute_respond(self, stmt: RespondStmt) -> None:
        status_val = self.evaluate(stmt.status)
        status = int(status_val) if status_val is not None else 200
        payload = self.evaluate(stmt.payload)
        headers = self.evaluate(stmt.headers) if stmt.headers else None
        raise RespondSignal(status=status, content_type=stmt.content_type, payload=payload, headers=headers)

    def execute_validate(self, stmt: ValidateStmt) -> None:
        from .stdlib.validation import validate_data
        schema = self.evaluate(stmt.schema)
        try:
            req_dict = self.environment.get("request")
        except NameError:
            raise RuntimeError_("Validate statement must be used within an HTTP route handler context", line=stmt.line, column=stmt.column)

        target_data = req_dict.get(stmt.target, {})
        res = validate_data(target_data, schema)
        if not res["valid"]:
            raise RespondSignal(
                status=400,
                content_type="json",
                payload={"error": "Validation Failed", "details": res["errors"]}
            )


    def execute_print(self, stmt: PrintStmt) -> None:
        values = [self.stringify_val(self.evaluate(e)) for e in stmt.expressions]
        print(*values)

    def execute_assert(self, stmt: AssertStmt) -> None:
        cond = self.evaluate(stmt.condition)
        if not self.is_truthy(cond):
            msg = self.evaluate(stmt.message) if stmt.message else "Assertion failed"
            raise RuntimeError_(
                f"AssertionError: {msg}",
                line=stmt.line,
                column=stmt.column,
                filename=self.filename,
                source=self.source
            )


    def evaluate(self, expr: Expr) -> Any:
        if isinstance(expr, LiteralExpr):
            return expr.value
        elif isinstance(expr, VariableExpr):
            return self.environment.get(expr.name)
        elif isinstance(expr, BinaryExpr):
            return self.evaluate_binary(expr)
        elif isinstance(expr, UnaryExpr):
            return self.evaluate_unary(expr)
        elif isinstance(expr, CallExpr):
            return self.evaluate_call(expr)
        elif isinstance(expr, MemberAccessExpr):
            return self.evaluate_member(expr)
        elif isinstance(expr, IndexAccessExpr):
            return self.evaluate_index(expr)
        elif isinstance(expr, ListExpr):
            return [self.evaluate(e) for e in expr.elements]
        elif isinstance(expr, MapExpr):
            result_map: Dict[str, Any] = {}
            for k_expr, v_expr in expr.entries:
                k = self.evaluate(k_expr)
                v = self.evaluate(v_expr)
                result_map[str(k)] = v
            return result_map
        elif isinstance(expr, StringInterpolationExpr):
            rendered_parts = []
            for part in expr.parts:
                if isinstance(part, str):
                    rendered_parts.append(part)
                else:
                    rendered_parts.append(self.stringify_val(self.evaluate(part)))
            return "".join(rendered_parts)
        elif isinstance(expr, AskExpr):
            prompt = ""
            if expr.prompt:
                prompt = self.stringify_val(self.evaluate(expr.prompt))
            return input(prompt)
        elif isinstance(expr, ConditionalExpr):
            if self.is_truthy(self.evaluate(expr.condition)):
                return self.evaluate(expr.then_expr)
            return self.evaluate(expr.else_expr)
        else:
            raise RuntimeError_(f"Unknown expression type {type(expr).__name__}", line=expr.line, column=expr.column)

    def evaluate_binary(self, expr: BinaryExpr) -> Any:
        op = expr.operator

        if op == "or":
            left = self.evaluate(expr.left)
            if self.is_truthy(left):
                return left
            return self.evaluate(expr.right)

        if op == "and":
            left = self.evaluate(expr.left)
            if not self.is_truthy(left):
                return left
            return self.evaluate(expr.right)

        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self.stringify_val(left) + self.stringify_val(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            return left + right

        elif op == "-":
            return left - right
        elif op == "*":
            if isinstance(left, str) and isinstance(right, (int, float)):
                return left * int(right)
            return left * right
        elif op == "/":
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            res = left / right
            if isinstance(res, float) and res.is_integer() and isinstance(left, int) and isinstance(right, int):
                return int(res)
            return res
        elif op == "%":
            return left % right
        elif op in ("==", "equals"):
            return left == right
        elif op in ("!=", "does not equal"):
            return left != right
        elif op == "<":
            return left < right
        elif op == "<=":
            return left <= right
        elif op == ">":
            return left > right
        elif op == ">=":
            return left >= right
        elif op == "in":
            if isinstance(right, (list, tuple, str)):
                return left in right
            if isinstance(right, dict):
                return str(left) in right
            return False
        elif op == "not in":
            if isinstance(right, (list, tuple, str)):
                return left not in right
            if isinstance(right, dict):
                return str(left) not in right
            return True
        else:
            raise RuntimeError_(f"Unknown operator '{op}'", line=expr.line, column=expr.column)

    def evaluate_unary(self, expr: UnaryExpr) -> Any:
        operand = self.evaluate(expr.operand)
        op = expr.operator
        if op == "-":
            return -operand
        elif op == "+":
            return +operand
        elif op in ("not", "!"):
            return not self.is_truthy(operand)
        elif op == "await":
            return operand
        else:
            raise RuntimeError_(f"Unknown unary operator '{op}'", line=expr.line, column=expr.column)

    def evaluate_member(self, expr: MemberAccessExpr) -> Any:
        target = self.evaluate(expr.target)
        prop = expr.member

        if isinstance(target, LyslynHttpResponse):
            return target.get_property(prop)
        elif isinstance(target, LyslynModule):
            return target.get(prop)
        elif isinstance(target, dict):
            if prop in target:
                return target[prop]
            if prop == "keys":
                return LyslynBuiltin("keys", lambda: list(target.keys()), arity=0)
            if prop == "values":
                return LyslynBuiltin("values", lambda: list(target.values()), arity=0)
            if prop == "has":
                return LyslynBuiltin("has", lambda k: k in target, arity=1)
            if prop == "get":
                return LyslynBuiltin("get", lambda k, d=None: target.get(k, d))
            raise AttributeError(f"Object has no property '{prop}'")
        elif isinstance(target, list):
            if prop in ("length", "count"):
                return len(target)
            if prop == "append":
                return LyslynBuiltin("append", lambda x: target.append(x), arity=1)
            if prop == "pop":
                return LyslynBuiltin("pop", lambda idx=-1: target.pop(idx))
            if prop == "contains":
                return LyslynBuiltin("contains", lambda x: x in target, arity=1)
            if prop == "join":
                return LyslynBuiltin("join", lambda sep="": sep.join(str(x) for x in target))
            raise AttributeError(f"List has no property '{prop}'")
        elif isinstance(target, str):
            if prop == "length":
                return len(target)
            if prop == "uppercase":
                return LyslynBuiltin("uppercase", lambda: target.upper(), arity=0)
            if prop == "lowercase":
                return LyslynBuiltin("lowercase", lambda: target.lower(), arity=0)
            if prop == "trim":
                return LyslynBuiltin("trim", lambda: target.strip(), arity=0)
            if prop == "split":
                return LyslynBuiltin("split", lambda sep=" ": target.split(sep))
            if prop == "contains":
                return LyslynBuiltin("contains", lambda sub: sub in target, arity=1)
            raise AttributeError(f"String has no property '{prop}'")
        elif hasattr(target, prop):
            return getattr(target, prop)

        raise AttributeError(f"Type '{type(target).__name__}' has no property '{prop}'")

    def evaluate_index(self, expr: IndexAccessExpr) -> Any:
        target = self.evaluate(expr.target)
        index = self.evaluate(expr.index)

        if isinstance(target, (list, tuple, str)):
            if not isinstance(index, (int, float)):
                raise TypeError(f"List/String index must be a number, got {type(index).__name__}")
            idx = int(index)
            if idx < -len(target) or idx >= len(target):
                raise IndexError(f"Index {idx} out of range (length {len(target)})")
            return target[idx]

        if isinstance(target, dict):
            key = str(index) if not isinstance(index, str) and index not in target else index
            if key in target:
                return target[key]
            return None

        raise TypeError(f"Cannot index into object of type '{type(target).__name__}'")

    def evaluate_call(self, expr: CallExpr) -> Any:
        callee = self.evaluate(expr.callee)
        args = [self.evaluate(a) for a in expr.arguments]

        if isinstance(callee, LyslynFunction):
            return self.call_function(callee, args)
        elif isinstance(callee, LyslynBuiltin):
            return callee.call(args, self)
        elif callable(callee):
            return callee(*args)
        else:
            raise TypeError(f"'{type(callee).__name__}' is not callable")

    def call_function(self, func: LyslynFunction, args: List[Any]) -> Any:
        if len(args) != len(func.params):
            raise TypeError(f"Function '{func.name}' expects {len(func.params)} arguments, got {len(args)}")

        call_env = Environment(parent=func.closure)
        for param, arg in zip(func.params, args):
            call_env.define(param, arg)

        self.call_stack.append(func.name)
        try:
            self.execute_block(func.body, env=call_env)
            return None
        except ReturnSignal as ret:
            return ret.value
        finally:
            self.call_stack.pop()

    def is_truthy(self, val: Any) -> bool:
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, (str, list, dict)):
            return len(val) > 0
        return True

    def stringify_val(self, val: Any) -> str:
        if val is None:
            return "nil"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            return val
        if isinstance(val, list):
            return "[" + ", ".join(self.stringify_val(x) for x in val) + "]"
        if isinstance(val, dict):
            items = [f'"{k}": {self.stringify_val(v)}' for k, v in val.items()]
            return "{" + ", ".join(items) + "}"
        return str(val)
