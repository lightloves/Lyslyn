"""Recursive-descent parser for Lyslyn."""
import re
from typing import List, Tuple, Optional, Any, Union
from .tokens import Token, TokenType
from .ast_nodes import (
    ASTNode, Expr, Stmt, Program,
    LiteralExpr, VariableExpr, BinaryExpr, UnaryExpr,
    ListExpr, MapExpr, MemberAccessExpr, IndexAccessExpr,
    CallExpr, StringInterpolationExpr, AskExpr, ConditionalExpr,
    BlockStmt, SetStmt, ChangeStmt, IfStmt, WhileStmt,
    ForStmt, RepeatStmt, FunctionStmt, ReturnStmt, AssertStmt,
    BreakStmt, ContinueStmt, TryStmt, RaiseStmt,
    ImportStmt, HttpStmt, PrintStmt, ExprStmt,
    ServeStmt, RouteStmt, UseMiddlewareStmt, RespondStmt, ValidateStmt
)
from .diagnostics import ParseError


CONTEXTUAL_IDENTIFIER_TYPES = {
    TokenType.IDENTIFIER,
    TokenType.DATA,
    TokenType.HEADERS,
    TokenType.PARAMS,
    TokenType.TIMEOUT,
    TokenType.RESPONSE,
    TokenType.ERROR,
    TokenType.TIMES,
    TokenType.EACH,
    TokenType.CALLED,
    TokenType.METHOD,
    TokenType.REQUEST,
    TokenType.WITH,
    TokenType.BY,
    TokenType.TO,
    TokenType.AS,
    TokenType.PORT,
    TokenType.ROUTE,
    TokenType.USE,
    TokenType.MIDDLEWARE,
    TokenType.RESPOND,
    TokenType.STATUS,
    TokenType.VALIDATE,
    TokenType.BODY,
}


class Parser:
    def __init__(self, tokens: List[Token], filename: str = "<input>", source: str = ""):
        self.tokens = tokens
        self.filename = filename
        self.source = source
        self.current = 0

    def is_identifier_like(self, token: Token) -> bool:
        return token.type in CONTEXTUAL_IDENTIFIER_TYPES

    def consume_identifier(self, message: str) -> Token:
        if self.is_identifier_like(self.peek()):
            return self.advance()
        raise self.error(self.peek(), message)

    def consume_property_name(self, message: str) -> Token:
        tok = self.peek()
        if tok.lexeme and tok.lexeme.isidentifier():
            return self.advance()
        if self.is_identifier_like(tok):
            return self.advance()
        raise self.error(tok, message)


    def parse(self) -> Program:
        statements: List[Stmt] = []
        self.skip_newlines()
        while not self.is_at_end():
            stmt = self.statement()
            if stmt is not None:
                statements.append(stmt)
            self.skip_newlines()
        return Program(statements=statements)


    def statement(self) -> Stmt:
        self.skip_newlines()

        if self.match(TokenType.SET, TokenType.LET):
            return self.set_statement()

        if self.match(TokenType.CONSTANT):
            return self.constant_statement()

        if self.check(TokenType.DEFINE) and self.check_next(TokenType.CONSTANT):
            self.advance()
            self.advance()
            return self.constant_statement()

        if self.match(TokenType.INCREASE):
            return self.change_statement("increase")
        if self.match(TokenType.DECREASE):
            return self.change_statement("decrease")
        if self.match(TokenType.CHANGE):
            return self.change_statement("change")

        if self.match(TokenType.IF):
            return self.if_statement()

        if self.match(TokenType.WHILE):
            return self.while_statement()

        if self.match(TokenType.FOR):
            return self.for_statement()

        if self.match(TokenType.REPEAT):
            return self.repeat_statement()

        if self.check_identifier("do"):
            start_pos = self.current
            do_tok = self.advance()
            if self.check_identifier("this"):
                self.advance()
            try:
                count = self.expression()
                if self.match(TokenType.TIMES) or self.check_identifier("times"):
                    self.consume(TokenType.COLON, "Expected ':' after repeat statement")
                    body = self.block()
                    return RepeatStmt(count=count, body=body, line=do_tok.line, column=do_tok.column)
            except Exception:
                pass
            self.current = start_pos

        if self.match(TokenType.ASYNC):
            return self.function_statement(is_async=True)

        if self.match(TokenType.FUNCTION):
            return self.function_statement(is_async=False)

        if self.match(TokenType.DEFINE):
            if self.check_identifier("a") or self.check_identifier("an"):
                self.advance()
            if self.match(TokenType.FUNCTION) or self.check_identifier("function"):
                if self.previous().type != TokenType.FUNCTION:
                    self.advance()
                if self.match(TokenType.CALLED) or self.check_identifier("called"):
                    pass
                return self.function_statement(is_async=False)
            raise self.error(self.previous(), "Expected 'function' or 'constant' after 'define'")

        if self.match(TokenType.CREATE):
            if self.check_identifier("a") or self.check_identifier("an"):
                self.advance()
            self.consume(TokenType.FUNCTION, "Expected 'function' after 'create'")
            if self.match(TokenType.CALLED) or self.check_identifier("called"):
                pass
            return self.function_statement(is_async=False)

        if self.match(TokenType.RETURN):
            return self.return_statement()

        if self.check_identifier("give"):
            give_tok = self.advance()
            if self.check_identifier("back"):
                self.advance()
                val = None
                if not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
                    val = self.expression()
                self.consume_statement_end()
                return ReturnStmt(value=val, line=give_tok.line, column=give_tok.column)
            self.current -= 1

        if self.match(TokenType.BREAK):
            return self.break_statement()

        if self.check_identifier("stop"):
            stop_tok = self.advance()
            if self.check_identifier("the"):
                self.advance()
            if self.check_identifier("loop"):
                self.advance()
            self.consume_statement_end()
            return BreakStmt(line=stop_tok.line, column=stop_tok.column)

        if self.match(TokenType.CONTINUE):
            return self.continue_statement()

        if self.check_identifier("skip"):
            skip_tok = self.advance()
            if self.check_identifier("to"):
                self.advance()
            if self.check_identifier("next"):
                self.advance()
            self.consume_statement_end()
            return ContinueStmt(line=skip_tok.line, column=skip_tok.column)

        if self.match(TokenType.TRY):
            return self.try_statement()

        if self.match(TokenType.RAISE, TokenType.THROW):
            return self.raise_statement()

        if self.match(TokenType.IMPORT):
            return self.import_statement()

        if self.match(TokenType.FROM):
            return self.from_import_statement()

        if self.match(TokenType.SEND):
            return self.http_statement()

        if self.match(TokenType.SERVE):
            return self.serve_statement()

        if self.match(TokenType.ROUTE):
            return self.route_statement()

        if self.match(TokenType.USE):
            return self.use_statement()

        if self.match(TokenType.RESPOND):
            return self.respond_statement()

        if self.match(TokenType.VALIDATE):
            return self.validate_statement()

        if self.match(TokenType.PRINT) or self.check_identifier("display") or self.check_identifier("show"):
            if self.previous().type != TokenType.PRINT:
                self.advance()
            return self.print_statement()

        if self.match(TokenType.ASK):
            ask_tok = self.previous()
            prompt_expr = None
            if self.check(TokenType.STRING):
                prompt_expr = self.expression()
            if self.match(TokenType.AND) or self.check_identifier("and"):
                pass
            if self.match(TokenType.SAVE) or self.check_identifier("save"):
                pass
            if self.match(TokenType.AS) or self.match(TokenType.TO) or self.check_identifier("as") or self.check_identifier("to"):
                pass
            var_tok = self.consume_identifier("Expected variable name to save input as")
            self.consume_statement_end()
            ask_call = AskExpr(prompt_expr, ask_tok.line, ask_tok.column)
            return SetStmt(target=VariableExpr(var_tok.lexeme, var_tok.line, var_tok.column), value=ask_call, is_constant=False, line=ask_tok.line, column=ask_tok.column)

        if self.check_identifier("add") or self.check_identifier("append"):
            start_pos = self.current
            kw = self.advance()
            try:
                val = self.expression()
                if self.match(TokenType.TO) or self.check_identifier("to"):
                    target_tok = self.consume_identifier("Expected variable name to add to")
                    target = VariableExpr(target_tok.lexeme, target_tok.line, target_tok.column)
                    self.consume_statement_end()
                    append_call = CallExpr(VariableExpr("append", kw.line, kw.column), [target, val], kw.line, kw.column)
                    return ExprStmt(append_call, kw.line, kw.column)
            except Exception:
                pass
            self.current = start_pos

        if self.match(TokenType.ASSERT):
            return self.assert_statement()

        if self.check_identifier("run") or self.check_identifier("call") or self.check_identifier("execute"):
            run_tok = self.advance()
            callee_name = self.consume_identifier("Expected function name")
            callee = VariableExpr(callee_name.lexeme, callee_name.line, callee_name.column)
            args: List[Expr] = []
            if self.match(TokenType.WITH) or self.check_identifier("with"):
                args.append(self.comparison())
                while self.match(TokenType.COMMA) or self.match(TokenType.AND):
                    args.append(self.comparison())
            self.consume_statement_end()
            return ExprStmt(CallExpr(callee, args, run_tok.line, run_tok.column), run_tok.line, run_tok.column)

        return self.expression_statement()

    def set_statement(self) -> SetStmt:
        keyword = self.previous()
        target = self.target_expression()
        if not self.match(TokenType.TO, TokenType.EQUAL_SIGN):
            raise self.error(self.peek(), "Expected 'to' or '=' after assignment target")
        value = self.expression()
        self.consume_statement_end()
        return SetStmt(target=target, value=value, is_constant=False, line=keyword.line, column=keyword.column)

    def constant_statement(self) -> SetStmt:
        keyword = self.previous()
        name_tok = self.consume_identifier( "Expected constant name")
        target = VariableExpr(name_tok.lexeme, name_tok.line, name_tok.column)
        if not (self.match(TokenType.IS, TokenType.TO, TokenType.AS, TokenType.EQUAL_SIGN)):
            raise self.error(self.peek(), "Expected 'is', 'as', or '=' after constant name")
        value = self.expression()
        self.consume_statement_end()
        return SetStmt(target=target, value=value, is_constant=True, line=keyword.line, column=keyword.column)

    def change_statement(self, op: str) -> ChangeStmt:
        keyword = self.previous()
        target = self.target_expression()
        if op in ("increase", "decrease"):
            self.consume(TokenType.BY, f"Expected 'by' after target in {op} statement")
        else:
            self.consume(TokenType.TO, "Expected 'to' after target in change statement")
        value = self.expression()
        self.consume_statement_end()
        return ChangeStmt(target=target, operation=op, value=value, line=keyword.line, column=keyword.column)

    def target_expression(self) -> Expr:
        """Parse lvalue: variable, member access, or index access."""
        name_tok = self.consume_identifier( "Expected variable name")
        expr: Expr = VariableExpr(name_tok.lexeme, name_tok.line, name_tok.column)

        while True:
            if self.match(TokenType.DOT):
                member_tok = self.consume_property_name("Expected property name after '.'")
                expr = MemberAccessExpr(expr, member_tok.lexeme, member_tok.line, member_tok.column)
            elif self.match(TokenType.LBRACKET):
                index_expr = self.expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexAccessExpr(expr, index_expr, name_tok.line, name_tok.column)
            else:
                break
        return expr

    def if_statement(self) -> IfStmt:
        keyword = self.previous()
        condition = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after if condition")
        body = self.block()

        branches: List[Tuple[Expr, BlockStmt]] = [(condition, body)]
        otherwise_branch: Optional[BlockStmt] = None

        while True:
            self.skip_newlines()
            if self.match(TokenType.OTHERWISE) or self.match(TokenType.ELSE):
                if self.match(TokenType.IF):
                    cond = self.expression()
                    self.consume(TokenType.COLON, "Expected ':' after condition")
                    b = self.block()
                    branches.append((cond, b))
                else:
                    self.consume(TokenType.COLON, "Expected ':' after 'otherwise' / 'else'")
                    otherwise_branch = self.block()
                    break
            else:
                break

        return IfStmt(branches=branches, otherwise_branch=otherwise_branch, line=keyword.line, column=keyword.column)

    def while_statement(self) -> WhileStmt:
        keyword = self.previous()
        condition = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after while condition")
        body = self.block()
        return WhileStmt(condition=condition, body=body, line=keyword.line, column=keyword.column)

    def for_statement(self) -> ForStmt:
        keyword = self.previous()
        if self.match(TokenType.EACH) or self.check_identifier("each") or self.check_identifier("every"):
            if self.previous().type != TokenType.EACH:
                self.advance()
        var_tok = self.consume_identifier( "Expected variable name in for loop")
        self.consume(TokenType.IN, "Expected 'in' after for loop variable")
        iterable = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after for loop target")
        body = self.block()
        return ForStmt(variable=var_tok.lexeme, iterable=iterable, body=body, line=keyword.line, column=keyword.column)

    def repeat_statement(self) -> RepeatStmt:
        keyword = self.previous()
        count = self.expression()
        self.consume(TokenType.TIMES, "Expected 'times' after repeat count")
        self.consume(TokenType.COLON, "Expected ':' after repeat statement")
        body = self.block()
        return RepeatStmt(count=count, body=body, line=keyword.line, column=keyword.column)

    def function_statement(self, is_async: bool) -> FunctionStmt:
        keyword = self.previous()
        name_tok = self.consume_identifier( "Expected function name")
        params: List[str] = []

        if self.match(TokenType.WITH):
            p = self.consume_identifier( "Expected parameter name")
            params.append(p.lexeme)
            while self.match(TokenType.COMMA, TokenType.AND):
                p = self.consume_identifier( "Expected parameter name")
                params.append(p.lexeme)
        elif self.match(TokenType.LPAREN):
            if not self.check(TokenType.RPAREN):
                p = self.consume_identifier( "Expected parameter name")
                params.append(p.lexeme)
                while self.match(TokenType.COMMA):
                    p = self.consume_identifier( "Expected parameter name")
                    params.append(p.lexeme)
            self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        self.consume(TokenType.COLON, "Expected ':' before function body")
        body = self.block()
        return FunctionStmt(
            name=name_tok.lexeme,
            params=params,
            body=body,
            is_async=is_async,
            line=keyword.line,
            column=keyword.column
        )

    def return_statement(self) -> ReturnStmt:
        keyword = self.previous()
        if self.check_identifier("back"):
            self.advance()
        value: Optional[Expr] = None
        if not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
            if self.match(TokenType.NIL) or self.check_identifier("nothing"):
                if self.previous().type != TokenType.NIL:
                    self.advance()
                value = LiteralExpr(None, keyword.line, keyword.column)
            else:
                value = self.expression()
        self.consume_statement_end()
        return ReturnStmt(value=value, line=keyword.line, column=keyword.column)

    def break_statement(self) -> BreakStmt:
        keyword = self.previous()
        if self.check_identifier("out"):
            self.advance()
            if self.check_identifier("of"):
                self.advance()
            if self.check_identifier("loop"):
                self.advance()
        self.consume_statement_end()
        return BreakStmt(line=keyword.line, column=keyword.column)

    def continue_statement(self) -> ContinueStmt:
        keyword = self.previous()
        if self.match(TokenType.TO):
            if self.check_identifier("next"):
                self.advance()
            if self.check_identifier("iteration"):
                self.advance()
        self.consume_statement_end()
        return ContinueStmt(line=keyword.line, column=keyword.column)

    def try_statement(self) -> TryStmt:
        keyword = self.previous()
        self.consume(TokenType.COLON, "Expected ':' after 'try'")
        try_block = self.block()

        self.skip_newlines()
        self.consume(TokenType.CATCH, "Expected 'catch' block after 'try'")
        if self.match(TokenType.ERROR):
            pass
        catch_var: Optional[str] = None
        if self.match(TokenType.AS):
            var_tok = self.consume_identifier( "Expected variable name after 'catch error as'")
            catch_var = var_tok.lexeme
        elif not self.check(TokenType.COLON):
            var_tok = self.consume_identifier( "Expected variable name after 'catch'")
            catch_var = var_tok.lexeme
        self.consume(TokenType.COLON, "Expected ':' after 'catch'")
        catch_block = self.block()

        finally_block: Optional[BlockStmt] = None
        self.skip_newlines()
        if self.match(TokenType.FINALLY):
            self.consume(TokenType.COLON, "Expected ':' after 'finally'")
            finally_block = self.block()

        return TryStmt(
            try_block=try_block,
            catch_var=catch_var,
            catch_block=catch_block,
            finally_block=finally_block,
            line=keyword.line,
            column=keyword.column
        )

    def raise_statement(self) -> RaiseStmt:
        keyword = self.previous()
        if self.match(TokenType.ERROR):
            pass
        expr = self.expression()
        self.consume_statement_end()
        return RaiseStmt(expression=expr, line=keyword.line, column=keyword.column)

    def import_statement(self) -> ImportStmt:
        keyword = self.previous()
        if self.match(TokenType.STRING):
            mod_name = self.previous().literal
        else:
            name_tok = self.consume_identifier( "Expected module name to import")
            mod_name = name_tok.lexeme

        alias: Optional[str] = None
        if self.match(TokenType.AS):
            alias_tok = self.consume_identifier( "Expected alias name after 'as'")
            alias = alias_tok.lexeme

        self.consume_statement_end()
        return ImportStmt(module_name=mod_name, alias=alias, imported_names=None, line=keyword.line, column=keyword.column)

    def from_import_statement(self) -> ImportStmt:
        keyword = self.previous()
        if self.match(TokenType.STRING):
            mod_name = self.previous().literal
        else:
            name_tok = self.consume_identifier( "Expected module name after 'from'")
            mod_name = name_tok.lexeme

        self.consume(TokenType.IMPORT, "Expected 'import' after module in 'from ... import'")
        names: List[str] = []
        name1 = self.consume_identifier( "Expected name to import")
        names.append(name1.lexeme)
        while self.match(TokenType.COMMA):
            n = self.consume_identifier( "Expected name after ','")
            names.append(n.lexeme)

        self.consume_statement_end()
        return ImportStmt(module_name=mod_name, alias=None, imported_names=names, line=keyword.line, column=keyword.column)

    def http_statement(self) -> HttpStmt:
        keyword = self.previous()
        if self.check_identifier("a") or self.check_identifier("an"):
            self.advance()

        method_tok = self.consume_identifier( "Expected HTTP method (GET, POST, PUT, DELETE, etc.)")
        method = method_tok.lexeme.upper()

        self.consume(TokenType.REQUEST, "Expected 'request' after HTTP method")
        self.consume(TokenType.TO, "Expected 'to' after 'request'")
        url = self.expression()

        headers: Optional[Expr] = None
        data: Optional[Expr] = None
        params: Optional[Expr] = None
        timeout: Optional[Expr] = None
        response_var: str = "response"

        if self.match(TokenType.COLON):
            self.consume(TokenType.NEWLINE, "Expected newline after ':' in HTTP statement")
            self.consume(TokenType.INDENT, "Expected indented block for HTTP options")

            while not self.check(TokenType.DEDENT) and not self.is_at_end():
                self.skip_newlines()
                if self.check(TokenType.DEDENT):
                    break

                if self.check_identifier("include") or self.check_identifier("with"):
                    self.advance()
                if self.check_identifier("send"):
                    self.advance()

                if self.match(TokenType.HEADERS) or self.check_identifier("headers"):
                    if not self.previous().type == TokenType.HEADERS:
                        self.advance()
                    if self.match(TokenType.COLON, TokenType.EQUAL_SIGN):
                        pass
                    headers = self.expression()
                    self.consume_statement_end()
                elif self.match(TokenType.DATA) or self.check_identifier("data") or self.check_identifier("body"):
                    if not self.previous().type == TokenType.DATA:
                        self.advance()
                    if self.match(TokenType.COLON, TokenType.EQUAL_SIGN):
                        pass
                    data = self.expression()
                    self.consume_statement_end()
                elif self.match(TokenType.PARAMS) or self.check_identifier("params"):
                    if not self.previous().type == TokenType.PARAMS:
                        self.advance()
                    if self.match(TokenType.COLON, TokenType.EQUAL_SIGN):
                        pass
                    params = self.expression()
                    self.consume_statement_end()
                elif self.match(TokenType.TIMEOUT) or self.check_identifier("timeout"):
                    if not self.previous().type == TokenType.TIMEOUT:
                        self.advance()
                    if self.match(TokenType.COLON, TokenType.EQUAL_SIGN):
                        pass
                    timeout = self.expression()
                    self.consume_statement_end()
                elif self.match(TokenType.SAVE):
                    if self.check_identifier("the"):
                        self.advance()
                    self.consume(TokenType.RESPONSE, "Expected 'response' after 'save'")
                    self.consume(TokenType.AS, "Expected 'as' after 'response'")
                    resp_tok = self.consume_identifier( "Expected response variable name")
                    response_var = resp_tok.lexeme
                    self.consume_statement_end()
                else:
                    raise self.error(self.peek(), f"Unexpected option '{self.peek().lexeme}' in HTTP request block")

            self.consume(TokenType.DEDENT, "Expected dedent after HTTP request block")

        else:
            if self.match(TokenType.SAVE):
                if self.check_identifier("the"):
                    self.advance()
                self.consume(TokenType.RESPONSE, "Expected 'response' after 'save'")
                self.consume(TokenType.AS, "Expected 'as' after 'response'")
                resp_tok = self.consume_identifier( "Expected variable name for response")
                response_var = resp_tok.lexeme
            self.consume_statement_end()

        return HttpStmt(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=params,
            timeout=timeout,
            response_var=response_var,
            line=keyword.line,
            column=keyword.column
        )

    def serve_statement(self) -> ServeStmt:
        keyword = self.previous()
        if self.check_identifier("http") or self.check_identifier("server"):
            self.advance()
        if self.check_identifier("on"):
            self.advance()
        self.consume(TokenType.PORT, "Expected 'port' in serve statement")
        port_expr = self.expression()

        host_expr = None
        if self.check_identifier("host"):
            self.advance()
            host_expr = self.expression()

        self.consume(TokenType.COLON, "Expected ':' after serve statement header")
        self.consume(TokenType.NEWLINE, "Expected newline after ':' in serve statement")
        self.consume(TokenType.INDENT, "Expected indented block for server definition")

        middlewares: List[Expr] = []
        routes: List[RouteStmt] = []

        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            self.skip_newlines()
            if self.check(TokenType.DEDENT):
                break

            if self.match(TokenType.USE):
                if self.match(TokenType.MIDDLEWARE):
                    pass
                mid = self.expression()
                self.consume_statement_end()
                middlewares.append(mid)
            elif self.match(TokenType.ROUTE):
                route = self.route_statement()
                routes.append(route)
            else:
                stmt = self.statement()
                if isinstance(stmt, RouteStmt):
                    routes.append(stmt)
                elif isinstance(stmt, UseMiddlewareStmt):
                    middlewares.append(stmt.middleware)
                else:
                    raise self.error(self.peek(), "Expected 'Route' or 'Use middleware' inside Serve block")

        self.consume(TokenType.DEDENT, "Expected dedent at end of serve block")
        return ServeStmt(
            port=port_expr,
            host=host_expr,
            middlewares=middlewares,
            routes=routes,
            line=keyword.line,
            column=keyword.column
        )

    def route_statement(self) -> RouteStmt:
        keyword = self.previous()
        method_tok = self.consume_identifier("Expected HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)")
        method = method_tok.lexeme.upper()

        if self.match(TokenType.STRING):
            path_str = self.previous().literal
        elif self.check(TokenType.IDENTIFIER) or self.is_identifier_like(self.peek()):
            path_str = self.advance().lexeme
        else:
            raise self.error(self.peek(), 'Expected route path string e.g. "/api/users"')

        self.consume(TokenType.COLON, "Expected ':' after route path")
        body = self.block()
        return RouteStmt(method=method, path=str(path_str), body=body, line=keyword.line, column=keyword.column)

    def use_statement(self) -> UseMiddlewareStmt:
        keyword = self.previous()
        if self.match(TokenType.MIDDLEWARE):
            pass
        mid = self.expression()
        self.consume_statement_end()
        return UseMiddlewareStmt(middleware=mid, line=keyword.line, column=keyword.column)

    def respond_statement(self) -> RespondStmt:
        keyword = self.previous()
        if self.match(TokenType.WITH) or self.check_identifier("with"):
            pass

        status_expr: Expr = LiteralExpr(200, keyword.line, keyword.column)
        content_type = "json"
        payload_expr: Optional[Expr] = None
        headers_expr: Optional[Expr] = None

        if self.match(TokenType.STATUS) or self.check_identifier("status"):
            status_expr = self.term()
            if self.match(TokenType.AND) or self.check_identifier("and"):
                pass

        if self.check_identifier("json"):
            self.advance()
            content_type = "json"
            payload_expr = self.expression()
        elif self.check_identifier("text"):
            self.advance()
            content_type = "text"
            payload_expr = self.expression()
        elif self.check_identifier("redirect"):
            self.advance()
            content_type = "redirect"
            payload_expr = self.expression()
        elif not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
            payload_expr = self.expression()

        if payload_expr is None:
            payload_expr = LiteralExpr({"ok": True}, keyword.line, keyword.column)

        self.consume_statement_end()
        return RespondStmt(
            status=status_expr,
            content_type=content_type,
            payload=payload_expr,
            headers=headers_expr,
            line=keyword.line,
            column=keyword.column
        )

    def validate_statement(self) -> ValidateStmt:
        keyword = self.previous()
        target = "body"
        if self.match(TokenType.BODY) or self.check_identifier("body"):
            target = "body"
        elif self.check_identifier("query"):
            self.advance()
            target = "query"
        elif self.check_identifier("params"):
            self.advance()
            target = "params"

        if self.match(TokenType.WITH) or self.check_identifier("with"):
            pass
        schema_expr = self.expression()
        self.consume_statement_end()
        return ValidateStmt(target=target, schema=schema_expr, line=keyword.line, column=keyword.column)


    def print_statement(self) -> PrintStmt:
        keyword = self.previous()
        exprs: List[Expr] = []
        if not self.check(TokenType.NEWLINE) and not self.check(TokenType.EOF):
            exprs.append(self.expression())
            while self.match(TokenType.COMMA):
                exprs.append(self.expression())
        self.consume_statement_end()
        return PrintStmt(expressions=exprs, line=keyword.line, column=keyword.column)

    def assert_statement(self) -> Stmt:
        keyword = self.previous()
        if self.match(TokenType.LPAREN):
            callee = VariableExpr(keyword.lexeme, keyword.line, keyword.column)
            call = self.finish_call(callee)
            self.consume_statement_end()
            return ExprStmt(call, keyword.line, keyword.column)

        cond = self.expression()
        msg = None
        if self.match(TokenType.COMMA):
            msg = self.expression()
        self.consume_statement_end()
        return AssertStmt(condition=cond, message=msg, line=keyword.line, column=keyword.column)

    def finish_call(self, callee: Expr) -> CallExpr:
        args: List[Expr] = []
        if not self.check(TokenType.RPAREN):
            args.append(self.expression())
            while self.match(TokenType.COMMA):
                args.append(self.expression())
        self.consume(TokenType.RPAREN, "Expected ')' after arguments")
        return CallExpr(callee, args, callee.line, callee.column)

    def expression_statement(self) -> ExprStmt:
        expr = self.expression()
        self.consume_statement_end()
        return ExprStmt(expression=expr, line=expr.line, column=expr.column)

    def block(self) -> BlockStmt:
        start_tok = self.previous()
        self.consume(TokenType.NEWLINE, "Expected newline before block")
        self.consume(TokenType.INDENT, "Expected indentation for block")

        stmts: List[Stmt] = []
        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            self.skip_newlines()
            if self.check(TokenType.DEDENT):
                break
            s = self.statement()
            if s is not None:
                stmts.append(s)

        self.consume(TokenType.DEDENT, "Expected dedent at end of block")
        return BlockStmt(statements=stmts, line=start_tok.line, column=start_tok.column)


    def expression(self) -> Expr:
        return self.logic_or()

    def logic_or(self) -> Expr:
        expr = self.logic_and()
        while self.match(TokenType.OR):
            op = self.previous()
            right = self.logic_and()
            expr = BinaryExpr(expr, "or", right, op.line, op.column)
        return expr

    def logic_and(self) -> Expr:
        expr = self.logic_not()
        while self.match(TokenType.AND):
            op = self.previous()
            right = self.logic_not()
            expr = BinaryExpr(expr, "and", right, op.line, op.column)
        return expr

    def logic_not(self) -> Expr:
        if self.match(TokenType.NOT):
            op = self.previous()
            right = self.logic_not()
            return UnaryExpr("not", right, op.line, op.column)
        return self.comparison()

    def comparison(self) -> Expr:
        expr = self.term()

        while True:
            if self.match(
                TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL,
                TokenType.LESS_THAN, TokenType.LESS_EQUAL,
                TokenType.GREATER_THAN, TokenType.GREATER_EQUAL
            ):
                op = self.previous()
                right = self.term()
                expr = BinaryExpr(expr, op.lexeme, right, op.line, op.column)
                continue

            if self.check_identifier("does"):
                start_pos = self.current
                self.advance()
                if self.match(TokenType.NOT):
                    matched_equal = False
                    if self.match(TokenType.EQUAL, TokenType.EQUALS):
                        matched_equal = True
                    elif self.check_identifier("equal") or self.check_identifier("equals"):
                        self.advance()
                        matched_equal = True
                    if matched_equal:
                        if self.match(TokenType.TO):
                            pass
                        right = self.term()
                        expr = BinaryExpr(expr, "!=", right, self.previous().line, self.previous().column)
                        continue
                self.current = start_pos

            if self.match(TokenType.EQUALS):
                op = self.previous()
                right = self.term()
                expr = BinaryExpr(expr, "==", right, op.line, op.column)
                continue

            if self.match(TokenType.IS):
                op = self.previous()
                if self.match(TokenType.NOT):
                    if self.check_identifier("empty"):
                        self.advance()
                        len_call = CallExpr(VariableExpr("Length", op.line, op.column), [expr], op.line, op.column)
                        expr = BinaryExpr(len_call, ">", LiteralExpr(0, op.line, op.column), op.line, op.column)
                        continue
                    if self.check_identifier("negative"):
                        self.advance()
                        expr = BinaryExpr(expr, ">=", LiteralExpr(0, op.line, op.column), op.line, op.column)
                        continue
                    if self.check_identifier("positive"):
                        self.advance()
                        expr = BinaryExpr(expr, "<=", LiteralExpr(0, op.line, op.column), op.line, op.column)
                        continue
                    if self.check_identifier("zero"):
                        self.advance()
                        expr = BinaryExpr(expr, "!=", LiteralExpr(0, op.line, op.column), op.line, op.column)
                        continue
                    if self.check_identifier("even"):
                        self.advance()
                        mod_expr = BinaryExpr(expr, "%", LiteralExpr(2, op.line, op.column), op.line, op.column)
                        expr = BinaryExpr(mod_expr, "!=", LiteralExpr(0, op.line, op.column), op.line, op.column)
                        continue
                    if self.check_identifier("odd"):
                        self.advance()
                        mod_expr = BinaryExpr(expr, "%", LiteralExpr(2, op.line, op.column), op.line, op.column)
                        expr = BinaryExpr(mod_expr, "==", LiteralExpr(0, op.line, op.column), op.line, op.column)
                        continue
                    if self.match(TokenType.NIL) or self.check_identifier("nothing") or self.check_identifier("null"):
                        if self.previous().type != TokenType.NIL:
                            self.advance()
                        expr = BinaryExpr(expr, "!=", LiteralExpr(None, op.line, op.column), op.line, op.column)
                        continue
                    if self.match(TokenType.EQUAL):
                        if self.match(TokenType.TO):
                            pass
                        right = self.term()
                        expr = BinaryExpr(expr, "!=", right, op.line, op.column)
                        continue
                    elif self.match(TokenType.IN):
                        right = self.term()
                        expr = BinaryExpr(expr, "not in", right, op.line, op.column)
                        continue
                    else:
                        right = self.term()
                        expr = BinaryExpr(expr, "!=", right, op.line, op.column)
                        continue

                if self.check_identifier("empty"):
                    self.advance()
                    len_call = CallExpr(VariableExpr("Length", op.line, op.column), [expr], op.line, op.column)
                    expr = BinaryExpr(len_call, "==", LiteralExpr(0, op.line, op.column), op.line, op.column)
                    continue

                if self.check_identifier("positive"):
                    self.advance()
                    expr = BinaryExpr(expr, ">", LiteralExpr(0, op.line, op.column), op.line, op.column)
                    continue

                if self.check_identifier("negative"):
                    self.advance()
                    expr = BinaryExpr(expr, "<", LiteralExpr(0, op.line, op.column), op.line, op.column)
                    continue

                if self.check_identifier("zero"):
                    self.advance()
                    expr = BinaryExpr(expr, "==", LiteralExpr(0, op.line, op.column), op.line, op.column)
                    continue

                if self.check_identifier("even"):
                    self.advance()
                    mod_expr = BinaryExpr(expr, "%", LiteralExpr(2, op.line, op.column), op.line, op.column)
                    expr = BinaryExpr(mod_expr, "==", LiteralExpr(0, op.line, op.column), op.line, op.column)
                    continue

                if self.check_identifier("odd"):
                    self.advance()
                    mod_expr = BinaryExpr(expr, "%", LiteralExpr(2, op.line, op.column), op.line, op.column)
                    expr = BinaryExpr(mod_expr, "!=", LiteralExpr(0, op.line, op.column), op.line, op.column)
                    continue

                if self.check_identifier("something"):
                    self.advance()
                    expr = BinaryExpr(expr, "!=", LiteralExpr(None, op.line, op.column), op.line, op.column)
                    continue

                if self.match(TokenType.NIL) or self.check_identifier("nothing") or self.check_identifier("null"):
                    if self.previous().type != TokenType.NIL:
                        self.advance()
                    expr = BinaryExpr(expr, "==", LiteralExpr(None, op.line, op.column), op.line, op.column)
                    continue

                if self.match(TokenType.TRUE):
                    expr = BinaryExpr(expr, "==", LiteralExpr(True, op.line, op.column), op.line, op.column)
                    continue

                if self.match(TokenType.FALSE):
                    expr = BinaryExpr(expr, "==", LiteralExpr(False, op.line, op.column), op.line, op.column)
                    continue

                elif self.match(TokenType.EQUAL):
                    if self.match(TokenType.TO):
                        pass
                    right = self.term()
                    expr = BinaryExpr(expr, "==", right, op.line, op.column)
                elif self.match(TokenType.AT):
                    if self.match(TokenType.LEAST):
                        right = self.term()
                        expr = BinaryExpr(expr, ">=", right, op.line, op.column)
                    elif self.match(TokenType.MOST):
                        right = self.term()
                        expr = BinaryExpr(expr, "<=", right, op.line, op.column)
                    else:
                        raise self.error(self.peek(), "Expected 'least' or 'most' after 'is at'")
                elif self.match(TokenType.GREATER):
                    if self.match(TokenType.THAN):
                        if self.match(TokenType.OR):
                            self.consume(TokenType.EQUAL, "Expected 'equal' after 'is greater than or'")
                            if self.match(TokenType.TO):
                                pass
                            right = self.term()
                            expr = BinaryExpr(expr, ">=", right, op.line, op.column)
                        else:
                            right = self.term()
                            expr = BinaryExpr(expr, ">", right, op.line, op.column)
                    else:
                        raise self.error(self.peek(), "Expected 'than' after 'is greater'")
                elif self.match(TokenType.LESS):
                    if self.match(TokenType.THAN):
                        if self.match(TokenType.OR):
                            self.consume(TokenType.EQUAL, "Expected 'equal' after 'is less than or'")
                            if self.match(TokenType.TO):
                                pass
                            right = self.term()
                            expr = BinaryExpr(expr, "<=", right, op.line, op.column)
                        else:
                            right = self.term()
                            expr = BinaryExpr(expr, "<", right, op.line, op.column)
                    else:
                        raise self.error(self.peek(), "Expected 'than' after 'is less'")
                elif self.match(TokenType.IN):
                    right = self.term()
                    expr = BinaryExpr(expr, "in", right, op.line, op.column)
                else:
                    right = self.term()
                    expr = BinaryExpr(expr, "==", right, op.line, op.column)
                continue

            if self.match(TokenType.NOT):
                op = self.previous()
                if self.match(TokenType.IN):
                    right = self.term()
                    expr = BinaryExpr(expr, "not in", right, op.line, op.column)
                    continue
                else:
                    self.current -= 1

            if self.match(TokenType.IN):
                op = self.previous()
                right = self.term()
                expr = BinaryExpr(expr, "in", right, op.line, op.column)
                continue

            break

        return expr

    def term(self) -> Expr:
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.previous()
            right = self.factor()
            expr = BinaryExpr(expr, op.lexeme, right, op.line, op.column)
        return expr

    def factor(self) -> Expr:
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.previous()
            right = self.unary()
            expr = BinaryExpr(expr, op.lexeme, right, op.line, op.column)
        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.MINUS, TokenType.PLUS):
            op = self.previous()
            right = self.unary()
            return UnaryExpr(op.lexeme, right, op.line, op.column)

        if self.match(TokenType.WAIT):
            op = self.previous()
            if self.check_identifier("for"):
                self.advance()
            right = self.unary()
            return UnaryExpr("await", right, op.line, op.column)

        if self.check_identifier("await"):
            op = self.advance()
            right = self.unary()
            return UnaryExpr("await", right, op.line, op.column)

        return self.call_or_access()

    def call_or_access(self) -> Expr:
        expr = self.primary()

        while True:
            if self.match(TokenType.LPAREN):
                expr = self.finish_call(expr)

            elif self.match(TokenType.DOT):
                name_tok = self.consume_property_name("Expected property name after '.'")
                expr = MemberAccessExpr(expr, name_tok.lexeme, name_tok.line, name_tok.column)

            elif self.match(TokenType.LBRACKET):
                index_expr = self.expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexAccessExpr(expr, index_expr, expr.line, expr.column)

            else:
                break

        return expr

    def primary(self) -> Expr:
        if self.match(TokenType.INT, TokenType.FLOAT):
            tok = self.previous()
            return LiteralExpr(tok.literal, tok.line, tok.column)

        if self.match(TokenType.STRING):
            tok = self.previous()
            return self.parse_string_with_interpolation(tok)

        if self.match(TokenType.TRUE):
            tok = self.previous()
            return LiteralExpr(True, tok.line, tok.column)

        if self.match(TokenType.FALSE):
            tok = self.previous()
            return LiteralExpr(False, tok.line, tok.column)

        if self.match(TokenType.NIL):
            tok = self.previous()
            return LiteralExpr(None, tok.line, tok.column)

        if self.match(TokenType.ASK):
            tok = self.previous()
            prompt_expr: Optional[Expr] = None
            if not self.check(TokenType.NEWLINE) and not self.check(TokenType.COMMA) and not self.check(TokenType.RPAREN) and not self.is_at_end():
                if self.check(TokenType.STRING):
                    prompt_expr = self.expression()
            return AskExpr(prompt=prompt_expr, line=tok.line, column=tok.column)

        if self.match(TokenType.IF):
            tok = self.previous()
            cond = self.expression()
            if self.match(TokenType.COLON):
                pass
            elif self.check_identifier("then"):
                self.advance()
            true_expr = self.expression()
            if not self.match(TokenType.OTHERWISE, TokenType.ELSE):
                raise self.error(self.peek(), "Expected 'otherwise' or 'else' in conditional expression")
            if self.match(TokenType.COLON):
                pass
            false_expr = self.expression()
            return ConditionalExpr(cond, true_expr, false_expr, tok.line, tok.column)

        if self.check_identifier("a") and (self.check_next_identifier("list") or self.check_next_identifier("collection")):
            tok = self.advance()
            self.advance()
            elements: List[Expr] = []
            if self.check_identifier("of") or self.check_identifier("containing") or self.check_identifier("with"):
                self.advance()
                elements.append(self.comparison())
                while self.match(TokenType.COMMA) or self.match(TokenType.AND):
                    self.skip_newlines()
                    elements.append(self.comparison())
            return ListExpr(elements, tok.line, tok.column)

        if self.check_identifier("an") and self.check_next_identifier("empty"):
            tok = self.advance()
            self.advance()
            if self.check_identifier("list") or self.check_identifier("array") or self.check_identifier("collection"):
                self.advance()
                return ListExpr([], tok.line, tok.column)
            if self.check_identifier("object") or self.check_identifier("map") or self.check_identifier("dictionary"):
                self.advance()
                return MapExpr([], tok.line, tok.column)

        if self.check_identifier("an") and (self.check_next_identifier("object") or self.check_next_identifier("dictionary") or self.check_next_identifier("map")):
            tok = self.advance()
            self.advance()
            entries: List[Tuple[Expr, Expr]] = []
            if self.match(TokenType.WITH) or self.check_identifier("with"):
                pass
            if self.match(TokenType.COLON):
                self.skip_newlines()
                self.consume(TokenType.INDENT, "Expected indentation for object")
                while not self.check(TokenType.DEDENT) and not self.is_at_end():
                    self.skip_newlines()
                    if self.check(TokenType.DEDENT):
                        break
                    entries.append(self.map_entry())
                    self.match(TokenType.COMMA)
                    self.skip_newlines()
                self.consume(TokenType.DEDENT, "Expected dedent after object")
                return MapExpr(entries, tok.line, tok.column)
            else:
                entries.append(self.map_entry())
                while self.match(TokenType.COMMA) or self.match(TokenType.AND):
                    self.skip_newlines()
                    entries.append(self.map_entry())
                return MapExpr(entries, tok.line, tok.column)

        if self.match(TokenType.LBRACKET):
            tok = self.previous()
            elements: List[Expr] = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.match(TokenType.COMMA):
                    self.skip_newlines()
                    if self.check(TokenType.RBRACKET):
                        break
                    elements.append(self.expression())
            self.consume(TokenType.RBRACKET, "Expected ']' at end of list")
            return ListExpr(elements, tok.line, tok.column)

        if self.match(TokenType.LBRACE):
            tok = self.previous()
            entries: List[Tuple[Expr, Expr]] = []
            if not self.check(TokenType.RBRACE):
                entries.append(self.map_entry())
                while self.match(TokenType.COMMA):
                    self.skip_newlines()
                    if self.check(TokenType.RBRACE):
                        break
                    entries.append(self.map_entry())
            self.consume(TokenType.RBRACE, "Expected '}' at end of object")
            return MapExpr(entries, tok.line, tok.column)

        if self.is_identifier_like(self.peek()):
            tok = self.advance()
            return VariableExpr(tok.lexeme, tok.line, tok.column)

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise self.error(self.peek(), f"Expected expression, found '{self.peek().lexeme}'")

    def map_entry(self) -> Tuple[Expr, Expr]:
        self.skip_newlines()
        if self.match(TokenType.STRING):
            key = LiteralExpr(self.previous().literal, self.previous().line, self.previous().column)
        elif self.match(TokenType.IDENTIFIER):
            tok = self.previous()
            key = LiteralExpr(tok.lexeme, tok.line, tok.column)
        else:
            key = self.expression()

        if not self.match(TokenType.COLON, TokenType.EQUAL_SIGN, TokenType.TO):
            raise self.error(self.peek(), "Expected ':' or '=' between key and value in object literal")

        value = self.comparison()
        return (key, value)

    def parse_string_with_interpolation(self, token: Token) -> Expr:
        val: str = token.literal
        if "{" not in val:
            return LiteralExpr(val, token.line, token.column)

        parts: List[Union[str, Expr]] = []
        pattern = re.compile(r"\{([^}]+)\}")
        last_end = 0

        for match in pattern.finditer(val):
            start, end = match.span()
            if start > last_end:
                parts.append(val[last_end:start])
            expr_code = match.group(1).strip()
            from .lexer import Lexer
            sub_lexer = Lexer(expr_code, filename=self.filename)
            sub_tokens = sub_lexer.tokenize()
            sub_parser = Parser(sub_tokens, filename=self.filename, source=self.source)
            inner_expr = sub_parser.expression()
            parts.append(inner_expr)
            last_end = end

        if last_end < len(val):
            parts.append(val[last_end:])

        return StringInterpolationExpr(parts, token.line, token.column)


    def check_identifier(self, name: str) -> bool:
        if self.is_at_end():
            return False
        tok = self.peek()
        return (tok.type in CONTEXTUAL_IDENTIFIER_TYPES or tok.type == TokenType.IDENTIFIER or bool(tok.lexeme and tok.lexeme.isidentifier())) and tok.lexeme.lower() == name.lower()

    def check_next_identifier(self, name: str) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        tok = self.tokens[self.current + 1]
        return (tok.type in CONTEXTUAL_IDENTIFIER_TYPES or tok.type == TokenType.IDENTIFIER or bool(tok.lexeme and tok.lexeme.isidentifier())) and tok.lexeme.lower() == name.lower()

    def match(self, *types: TokenType) -> bool:
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == token_type

    def check_next(self, token_type: TokenType) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        raise self.error(self.peek(), message)

    def consume_statement_end(self) -> None:
        if self.match(TokenType.NEWLINE, TokenType.EOF):
            return
        if self.check(TokenType.DEDENT):
            return
        if self.previous().type in (TokenType.DEDENT, TokenType.NEWLINE):
            return
        raise self.error(self.peek(), f"Expected end of line or statement, found '{self.peek().lexeme}'")

    def skip_newlines(self) -> None:
        while self.match(TokenType.NEWLINE):
            pass

    def error(self, token: Token, message: str) -> ParseError:
        return ParseError(
            message=message,
            line=token.line,
            column=token.column,
            length=token.length,
            filename=self.filename,
            source=self.source
        )
