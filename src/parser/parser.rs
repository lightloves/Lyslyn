use crate::ast::*;
use crate::errors::{ErrorKind, LyslynError, Span};
use crate::lexer::scanner::Scanner;
use crate::lexer::token::{Token, TokenType};

pub struct Parser {
    tokens: Vec<Token>,
    current: usize,
    filename: String,
    source: String,
}

impl Parser {
    pub fn new(tokens: Vec<Token>, filename: &str, source: &str) -> Self {
        Parser {
            tokens,
            current: 0,
            filename: filename.to_string(),
            source: source.to_string(),
        }
    }

    pub fn parse(&mut self) -> Result<Program, LyslynError> {
        let mut statements = Vec::new();

        while !self.is_at_end() {
            while self.match_token(&TokenType::Newline) {}
            if self.is_at_end() {
                break;
            }
            statements.push(self.statement()?);
            while self.match_token(&TokenType::Newline) {}
        }

        Ok(Program { statements })
    }

    fn statement(&mut self) -> Result<Stmt, LyslynError> {
        if self.match_token(&TokenType::Set) || self.match_token(&TokenType::Let) {
            self.set_statement(false)
        } else if self.match_token(&TokenType::Constant) {
            self.constant_statement()
        } else if self.match_token(&TokenType::Change) {
            self.change_statement()
        } else if self.match_token(&TokenType::Increase) {
            self.increase_statement()
        } else if self.match_token(&TokenType::Decrease) {
            self.decrease_statement()
        } else if self.match_token(&TokenType::Say)
            || self.match_token(&TokenType::Display)
            || self.match_token(&TokenType::Print)
        {
            self.say_statement()
        } else if self.match_token(&TokenType::If) {
            self.if_statement()
        } else if self.match_token(&TokenType::While) {
            self.while_statement()
        } else if self.match_token(&TokenType::For) {
            self.for_statement()
        } else if self.match_token(&TokenType::Repeat) || self.match_token(&TokenType::Do) {
            self.repeat_statement()
        } else if self.match_token(&TokenType::Create) || self.match_token(&TokenType::Define) {
            self.create_or_define_statement()
        } else if self.match_token(&TokenType::Function) {
            self.function_statement()
        } else if self.match_token(&TokenType::Return) {
            self.return_statement()
        } else if self.match_token(&TokenType::Give) {
            self.give_back_statement()
        } else if self.match_token(&TokenType::Break) {
            let span = self.previous().span.clone();
            while !self.check(&TokenType::Newline) && !self.is_at_end() && !self.check(&TokenType::Dedent) {
                self.advance();
            }
            Ok(Stmt::Break(span))
        } else if self.match_token(&TokenType::Stop) {
            let span = self.previous().span.clone();
            while !self.check(&TokenType::Newline) && !self.is_at_end() && !self.check(&TokenType::Dedent) {
                self.advance();
            }
            Ok(Stmt::Break(span))
        } else if self.match_token(&TokenType::Continue) {
            let span = self.previous().span.clone();
            while !self.check(&TokenType::Newline) && !self.is_at_end() && !self.check(&TokenType::Dedent) {
                self.advance();
            }
            Ok(Stmt::Continue(span))
        } else if self.match_token(&TokenType::Skip) {
            let span = self.previous().span.clone();
            while !self.check(&TokenType::Newline) && !self.is_at_end() && !self.check(&TokenType::Dedent) {
                self.advance();
            }
            Ok(Stmt::Continue(span))
        } else if self.match_token(&TokenType::Assert) {
            self.assert_statement()
        } else if self.match_token(&TokenType::Get) {
            self.get_statement()
        } else if self.match_token(&TokenType::Import) {
            self.import_statement()
        } else if self.match_token(&TokenType::Try) {
            self.try_statement()
        } else if self.match_token(&TokenType::Raise) || self.match_token(&TokenType::Throw) {
            self.raise_statement()
        } else if self.match_token(&TokenType::Add) {
            self.add_statement()
        } else if self.match_token(&TokenType::Serve) {
            self.serve_statement()
        } else if self.match_token(&TokenType::Respond) {
            self.respond_statement()
        } else if self.match_token(&TokenType::Validate) {
            self.validate_statement()
        } else if self.match_token(&TokenType::Send) {
            self.send_http_statement()
        } else {
            self.expression_statement()
        }
    }

    fn set_statement(&mut self, is_constant: bool) -> Result<Stmt, LyslynError> {
        let span_start = self.previous().span.clone();
        let target = self.call()?;

        if !self.match_token(&TokenType::To) && !self.match_token(&TokenType::EqualSign) {
            return Err(self.error("Expected 'to' or '=' after variable name in assignment"));
        }

        let value = self.expression()?;
        Ok(Stmt::Set {
            target,
            value,
            is_constant,
            span: span_start,
        })
    }

    fn constant_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span_start = self.previous().span.clone();
        let name_tok = self.consume_identifier("Expected constant name after 'Constant'")?;
        let target = Expr::Variable(name_tok.lexeme.clone(), name_tok.span.clone());

        if !self.match_token(&TokenType::Is)
            && !self.match_token(&TokenType::To)
            && !self.match_token(&TokenType::EqualSign)
        {
            return Err(self.error("Expected 'is', 'to', or '=' after constant name"));
        }

        let value = self.expression()?;
        Ok(Stmt::Set {
            target,
            value,
            is_constant: true,
            span: span_start,
        })
    }

    fn change_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span_start = self.previous().span.clone();
        let target = self.call()?;

        self.consume(&TokenType::By, "Expected 'by' in change statement")?;

        let op = if self.match_token(&TokenType::Plus) {
            "+"
        } else if self.match_token(&TokenType::Minus) {
            "-"
        } else if self.match_token(&TokenType::Star) {
            "*"
        } else if self.match_token(&TokenType::Slash) {
            "/"
        } else {
            "+"
        };

        let value = self.expression()?;
        Ok(Stmt::Change {
            target,
            operation: op.to_string(),
            value,
            span: span_start,
        })
    }

    fn increase_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span_start = self.previous().span.clone();
        let target = self.call()?;
        self.consume(&TokenType::By, "Expected 'by' after variable in 'Increase'")?;
        let value = self.expression()?;
        Ok(Stmt::Change {
            target,
            operation: "+".to_string(),
            value,
            span: span_start,
        })
    }

    fn decrease_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span_start = self.previous().span.clone();
        let target = self.call()?;
        self.consume(&TokenType::By, "Expected 'by' after variable in 'Decrease'")?;
        let value = self.expression()?;
        Ok(Stmt::Change {
            target,
            operation: "-".to_string(),
            value,
            span: span_start,
        })
    }

    fn say_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let mut expressions = Vec::new();

        if !self.check(&TokenType::Newline) && !self.is_at_end() {
            expressions.push(self.expression()?);
            while self.match_token(&TokenType::Comma) {
                expressions.push(self.expression()?);
            }
        }

        Ok(Stmt::Say { expressions, span })
    }

    fn if_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let mut branches = Vec::new();

        let condition = self.expression()?;
        self.consume(&TokenType::Colon, "Expected ':' after if condition")?;
        let body = self.block()?;
        branches.push((condition, body));

        while self.match_token(&TokenType::Otherwise) || self.match_token(&TokenType::Else) {
            if self.match_token(&TokenType::If) {
                let cond = self.expression()?;
                self.consume(&TokenType::Colon, "Expected ':' after if condition")?;
                let b = self.block()?;
                branches.push((cond, b));
            } else {
                self.consume(&TokenType::Colon, "Expected ':' after otherwise/else")?;
                let otherwise_body = self.block()?;
                return Ok(Stmt::If {
                    branches,
                    otherwise_branch: Some(otherwise_body),
                    span,
                });
            }
        }

        Ok(Stmt::If {
            branches,
            otherwise_branch: None,
            span,
        })
    }

    fn while_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let condition = self.expression()?;
        self.consume(&TokenType::Colon, "Expected ':' after while condition")?;
        let body = self.block()?;
        Ok(Stmt::While {
            condition,
            body,
            span,
        })
    }

    fn for_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let _ = self.match_token(&TokenType::Every) || self.match_token(&TokenType::Each);

        let var_tok = self.consume_identifier("Expected variable name in for loop")?;
        self.consume(&TokenType::In, "Expected 'in' in for loop")?;
        let iterable = self.expression()?;
        self.consume(&TokenType::Colon, "Expected ':' after for loop iterable")?;
        let body = self.block()?;

        Ok(Stmt::For {
            variable: var_tok.lexeme,
            iterable,
            body,
            span,
        })
    }

    fn repeat_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let count = self.expression()?;
        let _ = self.match_token(&TokenType::Times);
        self.consume(&TokenType::Colon, "Expected ':' after repeat count")?;
        let body = self.block()?;
        Ok(Stmt::Repeat { count, body, span })
    }

    fn create_or_define_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let _ = self.match_token(&TokenType::A);
        self.consume(&TokenType::Function, "Expected 'function' after 'create/define'")?;
        let _ = self.match_token(&TokenType::Called);

        let name_tok = self.consume_identifier("Expected function name")?;
        let mut params = Vec::new();

        if self.match_token(&TokenType::With) {
            if !self.check(&TokenType::Colon) {
                let p = self.consume_identifier("Expected parameter name")?;
                params.push(p.lexeme);
                while self.match_token(&TokenType::Comma) || self.match_token(&TokenType::And) {
                    let p2 = self.consume_identifier("Expected parameter name")?;
                    params.push(p2.lexeme);
                }
            }
        } else if self.match_token(&TokenType::LParen) {
            if !self.check(&TokenType::RParen) {
                let p = self.consume_identifier("Expected parameter name")?;
                params.push(p.lexeme);
                while self.match_token(&TokenType::Comma) {
                    let p2 = self.consume_identifier("Expected parameter name")?;
                    params.push(p2.lexeme);
                }
            }
            self.consume(&TokenType::RParen, "Expected ')' after parameters")?;
        }

        self.consume(&TokenType::Colon, "Expected ':' before function body")?;
        let body = self.block()?;

        Ok(Stmt::Function {
            name: name_tok.lexeme,
            params,
            body,
            is_async: false,
            span,
        })
    }

    fn function_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let name_tok = self.consume_identifier("Expected function name")?;
        let mut params = Vec::new();

        if self.match_token(&TokenType::LParen) {
            if !self.check(&TokenType::RParen) {
                let p = self.consume_identifier("Expected parameter name")?;
                params.push(p.lexeme);
                while self.match_token(&TokenType::Comma) {
                    let p2 = self.consume_identifier("Expected parameter name")?;
                    params.push(p2.lexeme);
                }
            }
            self.consume(&TokenType::RParen, "Expected ')' after parameters")?;
        } else if self.match_token(&TokenType::With) {
            if !self.check(&TokenType::Colon) {
                let p = self.consume_identifier("Expected parameter name")?;
                params.push(p.lexeme);
                while self.match_token(&TokenType::Comma) || self.match_token(&TokenType::And) {
                    let p2 = self.consume_identifier("Expected parameter name")?;
                    params.push(p2.lexeme);
                }
            }
        }

        self.consume(&TokenType::Colon, "Expected ':' before function body")?;
        let body = self.block()?;

        Ok(Stmt::Function {
            name: name_tok.lexeme,
            params,
            body,
            is_async: false,
            span,
        })
    }

    fn return_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        if self.match_token(&TokenType::Nil) || self.check(&TokenType::Newline) || self.is_at_end() {
            Ok(Stmt::Return { value: None, span })
        } else {
            let val = self.expression()?;
            Ok(Stmt::Return {
                value: Some(val),
                span,
            })
        }
    }

    fn give_back_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        self.consume(&TokenType::Back, "Expected 'back' after 'Give'")?;
        if self.match_token(&TokenType::Nil) || self.check(&TokenType::Newline) || self.is_at_end() {
            Ok(Stmt::Return { value: None, span })
        } else {
            let val = self.expression()?;
            Ok(Stmt::Return {
                value: Some(val),
                span,
            })
        }
    }

    fn assert_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let has_paren = self.match_token(&TokenType::LParen);
        let condition = self.expression()?;
        let message = if self.match_token(&TokenType::Comma) {
            Some(self.expression()?)
        } else {
            None
        };
        if has_paren {
            self.consume(&TokenType::RParen, "Expected ')' after assert arguments")?;
        }
        Ok(Stmt::Assert {
            condition,
            message,
            span,
        })
    }

    fn get_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let mod_name = if let TokenType::String(ref s) = self.peek().token_type {
            let s = s.clone();
            self.advance();
            s
        } else {
            self.consume_identifier("Expected module name after 'Get'")?.lexeme
        };
        let alias = if self.match_token(&TokenType::As) {
            Some(self.consume_identifier("Expected alias after 'as'")?.lexeme)
        } else {
            None
        };
        Ok(Stmt::Get {
            module_name: mod_name,
            alias,
            span,
        })
    }

    fn import_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let mod_name = if let TokenType::String(ref s) = self.peek().token_type {
            let s = s.clone();
            self.advance();
            s
        } else {
            self.consume_identifier("Expected module name after 'Import'")?.lexeme
        };
        let alias = if self.match_token(&TokenType::As) {
            Some(self.consume_identifier("Expected alias after 'as'")?.lexeme)
        } else {
            None
        };
        Ok(Stmt::Import {
            module_name: mod_name,
            alias,
            names: None,
            span,
        })
    }

    fn try_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        self.consume(&TokenType::Colon, "Expected ':' after 'Try'")?;
        let try_block = self.block()?;

        let mut catch_var = None;
        let mut catch_block = None;

        if self.match_token(&TokenType::Catch) {
            if self.check(&TokenType::Colon) {
            } else if let TokenType::Identifier(ref name) = self.peek().token_type.clone() {
                let first = name.clone();
                self.advance();
                if self.match_token(&TokenType::As) {
                    let alias = self.consume_identifier("Expected alias after 'as'")?;
                    catch_var = Some(alias.lexeme);
                } else if first != "error" || !self.check(&TokenType::Colon) {
                    catch_var = Some(first);
                } else {
                    catch_var = Some("error".to_string());
                }
            } else if self.peek().token_type == TokenType::Error {
                self.advance();
                if self.match_token(&TokenType::As) {
                    let alias = self.consume_identifier("Expected alias after 'as'")?;
                    catch_var = Some(alias.lexeme);
                } else {
                    catch_var = Some("error".to_string());
                }
            }
            self.consume(&TokenType::Colon, "Expected ':' after 'Catch'")?;
            catch_block = Some(self.block()?);
        }

        let mut finally_block = None;
        if self.match_token(&TokenType::Finally) {
            self.consume(&TokenType::Colon, "Expected ':' after 'Finally'")?;
            finally_block = Some(self.block()?);
        }

        Ok(Stmt::Try {
            try_block,
            catch_var,
            catch_block,
            finally_block,
            span,
        })
    }

    fn raise_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        if self.peek().token_type == TokenType::Error {
            self.advance();
        } else if let TokenType::Identifier(ref id) = self.peek().token_type {
            if id.eq_ignore_ascii_case("error") || id.eq_ignore_ascii_case("exception") {
                self.advance();
            }
        }
        let expression = self.expression()?;
        Ok(Stmt::Raise { expression, span })
    }

    fn add_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let item = self.expression()?;
        self.consume(&TokenType::To, "Expected 'to' in Add statement")?;
        let list = self.expression()?;
        Ok(Stmt::AddToList { item, list, span })
    }

    fn serve_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        if let TokenType::Identifier(ref id) = self.peek().token_type {
            if id.eq_ignore_ascii_case("http") || id.eq_ignore_ascii_case("server") {
                self.advance();
            }
        }
        if let TokenType::Identifier(ref id) = self.peek().token_type {
            if id.eq_ignore_ascii_case("on") {
                self.advance();
            }
        }
        self.consume(&TokenType::Port, "Expected 'port' in serve statement")?;
        let port = self.expression()?;
        let mut host = None;
        if let TokenType::Identifier(ref id) = self.peek().token_type {
            if id.eq_ignore_ascii_case("host") {
                self.advance();
                host = Some(self.expression()?);
            }
        }
        self.consume(&TokenType::Colon, "Expected ':' after serve statement header")?;
        while self.match_token(&TokenType::Newline) {}
        self.consume(&TokenType::Indent, "Expected indented block for server definition")?;

        let mut middlewares = Vec::new();
        let mut routes = Vec::new();

        while !self.check(&TokenType::Dedent) && !self.is_at_end() {
            while self.match_token(&TokenType::Newline) {}
            if self.check(&TokenType::Dedent) || self.is_at_end() {
                break;
            }
            if self.match_token(&TokenType::Use) {
                let _ = self.match_token(&TokenType::Middleware);
                let mid = self.expression()?;
                middlewares.push(mid);
            } else if self.match_token(&TokenType::Route) {
                let route_span = self.previous().span.clone();
                let method_tok = self.consume_identifier("Expected HTTP method (GET, POST, PUT, DELETE, etc.)")?;
                let method = method_tok.lexeme.to_uppercase();
                let path = if let TokenType::String(ref s) = self.peek().token_type {
                    let p = s.clone();
                    self.advance();
                    p
                } else {
                    self.consume_identifier("Expected route path string e.g. \"/api/products\"")?.lexeme
                };
                self.consume(&TokenType::Colon, "Expected ':' after route path")?;
                let body = self.block()?;
                routes.push(crate::ast::RouteStmt {
                    method,
                    path,
                    body,
                    span: route_span,
                });
            } else {
                return Err(self.error("Expected 'Route' or 'Use middleware' inside Serve block"));
            }
        }
        self.consume(&TokenType::Dedent, "Expected dedent at end of serve block")?;

        Ok(Stmt::Serve {
            port,
            host,
            middlewares,
            routes,
            span,
        })
    }

    fn respond_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let _ = self.match_token(&TokenType::With);
        self.consume(&TokenType::Status, "Expected 'status' after 'Respond [with]'")?;
        let status = self.term()?;
        let _ = self.match_token(&TokenType::And);

        let content_type = if let TokenType::Identifier(ref id) = self.peek().token_type {
            let t = id.to_lowercase();
            self.advance();
            t
        } else {
            "json".to_string()
        };

        let payload = self.expression()?;
        Ok(Stmt::Respond {
            status,
            content_type,
            payload,
            headers: None,
            span,
        })
    }

    fn validate_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let target = if self.match_token(&TokenType::Body) {
            "body".to_string()
        } else if self.match_token(&TokenType::Params) {
            "params".to_string()
        } else if let TokenType::Identifier(ref id) = self.peek().token_type {
            let t = id.clone();
            self.advance();
            t
        } else {
            "body".to_string()
        };
        let _ = self.match_token(&TokenType::With);
        let schema = self.expression()?;
        Ok(Stmt::Validate {
            target,
            schema,
            span,
        })
    }

    fn send_http_statement(&mut self) -> Result<Stmt, LyslynError> {
        let span = self.previous().span.clone();
        let _ = self.match_token(&TokenType::A) || self.match_token(&TokenType::An);
        let method_tok = self.consume_identifier("Expected HTTP method (GET, POST, etc.)")?;
        let method = method_tok.lexeme.to_uppercase();
        self.consume(&TokenType::Request, "Expected 'request' after HTTP method")?;
        self.consume(&TokenType::To, "Expected 'to' after 'request'")?;
        let url = self.expression()?;

        let mut headers = None;
        let mut data = None;
        let mut params = None;
        let mut timeout = None;
        let mut response_var = "response".to_string();

        if self.match_token(&TokenType::Colon) {
            while self.match_token(&TokenType::Newline) {}
            self.consume(&TokenType::Indent, "Expected indented block for HTTP options")?;

            while !self.check(&TokenType::Dedent) && !self.is_at_end() {
                while self.match_token(&TokenType::Newline) {}
                if self.check(&TokenType::Dedent) || self.is_at_end() {
                    break;
                }
                if self.match_token(&TokenType::Headers) {
                    let _ = self.match_token(&TokenType::Colon) || self.match_token(&TokenType::EqualSign);
                    headers = Some(self.expression()?);
                } else if self.match_token(&TokenType::Data) {
                    let _ = self.match_token(&TokenType::Colon) || self.match_token(&TokenType::EqualSign);
                    data = Some(self.expression()?);
                } else if self.match_token(&TokenType::Params) {
                    let _ = self.match_token(&TokenType::Colon) || self.match_token(&TokenType::EqualSign);
                    params = Some(self.expression()?);
                } else if self.match_token(&TokenType::Timeout) {
                    let _ = self.match_token(&TokenType::Colon) || self.match_token(&TokenType::EqualSign);
                    timeout = Some(self.expression()?);
                } else if self.match_token(&TokenType::Save) {
                    let _ = self.match_token(&TokenType::The);
                    self.consume(&TokenType::Response, "Expected 'response' after 'save'")?;
                    self.consume(&TokenType::As, "Expected 'as' after 'response'")?;
                    let resp_tok = self.consume_identifier("Expected variable name for response")?;
                    response_var = resp_tok.lexeme;
                } else {
                    return Err(self.error("Unexpected option in HTTP request block"));
                }
            }
            self.consume(&TokenType::Dedent, "Expected dedent after HTTP request block")?;
        } else {
            if self.match_token(&TokenType::Save) {
                let _ = self.match_token(&TokenType::The);
                self.consume(&TokenType::Response, "Expected 'response' after 'save'")?;
                self.consume(&TokenType::As, "Expected 'as' after 'response'")?;
                let resp_tok = self.consume_identifier("Expected variable name for response")?;
                response_var = resp_tok.lexeme;
            }
        }

        Ok(Stmt::HttpRequest {
            method,
            url,
            headers,
            data,
            params,
            timeout,
            response_var,
            span,
        })
    }

    fn expression_statement(&mut self) -> Result<Stmt, LyslynError> {
        let expr = self.expression()?;
        Ok(Stmt::Expr(expr))
    }

    fn block(&mut self) -> Result<Vec<Stmt>, LyslynError> {
        while self.match_token(&TokenType::Newline) {}
        self.consume(&TokenType::Indent, "Expected indented block")?;

        let mut statements = Vec::new();
        while !self.check(&TokenType::Dedent) && !self.is_at_end() {
            while self.match_token(&TokenType::Newline) {}
            if self.check(&TokenType::Dedent) || self.is_at_end() {
                break;
            }
            statements.push(self.statement()?);
            while self.match_token(&TokenType::Newline) {}
        }

        self.consume(&TokenType::Dedent, "Expected dedent at end of block")?;
        Ok(statements)
    }

    pub fn expression(&mut self) -> Result<Expr, LyslynError> {
        self.logical_or()
    }

    fn logical_or(&mut self) -> Result<Expr, LyslynError> {
        let mut expr = self.logical_and()?;

        while self.match_token(&TokenType::Or) {
            let span = self.previous().span.clone();
            let right = self.logical_and()?;
            expr = Expr::Binary(Box::new(expr), BinaryOp::Or, Box::new(right), span);
        }

        Ok(expr)
    }

    fn logical_and(&mut self) -> Result<Expr, LyslynError> {
        let mut expr = self.comparison()?;

        while self.match_token(&TokenType::And) {
            let span = self.previous().span.clone();
            let right = self.comparison()?;
            expr = Expr::Binary(Box::new(expr), BinaryOp::And, Box::new(right), span);
        }

        Ok(expr)
    }

    fn comparison(&mut self) -> Result<Expr, LyslynError> {
        let mut expr = self.term()?;

        loop {
            if self.match_token(&TokenType::Is) {
                let span = self.previous().span.clone();

                if self.match_token(&TokenType::At) {
                    if self.match_token(&TokenType::Least) {
                        let right = self.term()?;
                        expr = Expr::Binary(Box::new(expr), BinaryOp::GreaterEqual, Box::new(right), span);
                    } else if self.match_token(&TokenType::Most) {
                        let right = self.term()?;
                        expr = Expr::Binary(Box::new(expr), BinaryOp::LessEqual, Box::new(right), span);
                    } else {
                        return Err(self.error("Expected 'least' or 'most' after 'is at'"));
                    }
                } else if self.match_token(&TokenType::Greater) {
                    let _ = self.match_token(&TokenType::Than);
                    let right = self.term()?;
                    expr = Expr::Binary(Box::new(expr), BinaryOp::Greater, Box::new(right), span);
                } else if self.match_token(&TokenType::Less) {
                    let _ = self.match_token(&TokenType::Than);
                    let right = self.term()?;
                    expr = Expr::Binary(Box::new(expr), BinaryOp::Less, Box::new(right), span);
                } else if self.match_token(&TokenType::Equal) {
                    let _ = self.match_token(&TokenType::To);
                    let right = self.term()?;
                    expr = Expr::Binary(Box::new(expr), BinaryOp::Equal, Box::new(right), span);
                } else if self.match_token(&TokenType::Not) {
                    if self.match_token(&TokenType::Equal) {
                        let _ = self.match_token(&TokenType::To);
                        let right = self.term()?;
                        expr = Expr::Binary(Box::new(expr), BinaryOp::NotEqual, Box::new(right), span);
                    } else if self.match_token(&TokenType::Positive) {
                        expr = Expr::Unary(UnaryOp::IsNotPositive, Box::new(expr), span);
                    } else if self.match_token(&TokenType::Negative) {
                        expr = Expr::Unary(UnaryOp::IsNotNegative, Box::new(expr), span);
                    } else if self.match_token(&TokenType::Zero) {
                        expr = Expr::Unary(UnaryOp::IsNotZero, Box::new(expr), span);
                    } else if self.match_token(&TokenType::Even) {
                        expr = Expr::Unary(UnaryOp::IsNotEven, Box::new(expr), span);
                    } else if self.match_token(&TokenType::Odd) {
                        expr = Expr::Unary(UnaryOp::IsNotOdd, Box::new(expr), span);
                    } else if self.match_token(&TokenType::Empty) {
                        expr = Expr::Unary(UnaryOp::IsNotEmpty, Box::new(expr), span);
                    } else {
                        let right = self.term()?;
                        expr = Expr::Binary(Box::new(expr), BinaryOp::NotEqual, Box::new(right), span);
                    }
                } else if self.match_token(&TokenType::Positive) {
                    expr = Expr::Unary(UnaryOp::IsPositive, Box::new(expr), span);
                } else if self.match_token(&TokenType::Negative) {
                    expr = Expr::Unary(UnaryOp::IsNegative, Box::new(expr), span);
                } else if self.match_token(&TokenType::Zero) {
                    expr = Expr::Unary(UnaryOp::IsZero, Box::new(expr), span);
                } else if self.match_token(&TokenType::Even) {
                    expr = Expr::Unary(UnaryOp::IsEven, Box::new(expr), span);
                } else if self.match_token(&TokenType::Odd) {
                    expr = Expr::Unary(UnaryOp::IsOdd, Box::new(expr), span);
                } else if self.match_token(&TokenType::Empty) {
                    expr = Expr::Unary(UnaryOp::IsEmpty, Box::new(expr), span);
                } else if self.match_token(&TokenType::Something) {
                    expr = Expr::Unary(UnaryOp::IsSomething, Box::new(expr), span);
                } else {
                    let right = self.term()?;
                    expr = Expr::Binary(Box::new(expr), BinaryOp::Equal, Box::new(right), span);
                }
            } else if self.match_token(&TokenType::Equals) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::Equal, Box::new(right), span);
            } else if self.match_token(&TokenType::Does) {
                let span = self.previous().span.clone();
                self.consume(&TokenType::Not, "Expected 'not' after 'does'")?;
                self.consume(&TokenType::Equal, "Expected 'equal' after 'does not'")?;
                let _ = self.match_token(&TokenType::To);
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::NotEqual, Box::new(right), span);
            } else if self.match_token(&TokenType::EqualEqual) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::Equal, Box::new(right), span);
            } else if self.match_token(&TokenType::BangEqual) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::NotEqual, Box::new(right), span);
            } else if self.match_token(&TokenType::GreaterThan) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::Greater, Box::new(right), span);
            } else if self.match_token(&TokenType::GreaterEqual) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::GreaterEqual, Box::new(right), span);
            } else if self.match_token(&TokenType::LessThan) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::Less, Box::new(right), span);
            } else if self.match_token(&TokenType::LessEqual) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::LessEqual, Box::new(right), span);
            } else if self.match_token(&TokenType::In) {
                let span = self.previous().span.clone();
                let right = self.term()?;
                expr = Expr::Binary(Box::new(expr), BinaryOp::In, Box::new(right), span);
            } else if self.check(&TokenType::Not) {
                if self.current + 1 < self.tokens.len() && self.tokens[self.current + 1].token_type == TokenType::In {
                    self.advance();
                    self.advance();
                    let span = self.previous().span.clone();
                    let right = self.term()?;
                    expr = Expr::Binary(Box::new(expr), BinaryOp::NotIn, Box::new(right), span);
                } else {
                    break;
                }
            } else {
                break;
            }
        }

        Ok(expr)
    }

    fn term(&mut self) -> Result<Expr, LyslynError> {
        let mut expr = self.factor()?;

        while self.match_token(&TokenType::Plus) || self.match_token(&TokenType::Minus) {
            let op_tok = self.previous().clone();
            let op = if op_tok.token_type == TokenType::Plus {
                BinaryOp::Add
            } else {
                BinaryOp::Sub
            };
            let right = self.factor()?;
            expr = Expr::Binary(Box::new(expr), op, Box::new(right), op_tok.span);
        }

        Ok(expr)
    }

    fn factor(&mut self) -> Result<Expr, LyslynError> {
        let mut expr = self.unary()?;

        while self.match_token(&TokenType::Star)
            || self.match_token(&TokenType::Slash)
            || self.match_token(&TokenType::Percent)
        {
            let op_tok = self.previous().clone();
            let op = match op_tok.token_type {
                TokenType::Star => BinaryOp::Mul,
                TokenType::Slash => BinaryOp::Div,
                _ => BinaryOp::Mod,
            };
            let right = self.unary()?;
            expr = Expr::Binary(Box::new(expr), op, Box::new(right), op_tok.span);
        }

        Ok(expr)
    }

    fn unary(&mut self) -> Result<Expr, LyslynError> {
        if self.match_token(&TokenType::Not) {
            let span = self.previous().span.clone();
            let right = self.unary()?;
            Ok(Expr::Unary(UnaryOp::Not, Box::new(right), span))
        } else if self.match_token(&TokenType::Minus) {
            let span = self.previous().span.clone();
            let right = self.unary()?;
            Ok(Expr::Unary(UnaryOp::Neg, Box::new(right), span))
        } else {
            self.call()
        }
    }

    fn call(&mut self) -> Result<Expr, LyslynError> {
        let mut expr = self.primary()?;

        loop {
            if self.match_token(&TokenType::LParen) {
                expr = self.finish_call(expr)?;
            } else if self.match_token(&TokenType::Dot) {
                let name = self.consume_property_name()?;
                let span = name.span.clone();
                expr = Expr::MemberAccess(Box::new(expr), name.lexeme, span);
            } else if self.match_token(&TokenType::LBracket) {
                let index = self.expression()?;
                let span = self.consume(&TokenType::RBracket, "Expected ']' after index")?.span.clone();
                expr = Expr::IndexAccess(Box::new(expr), Box::new(index), span);
            } else {
                break;
            }
        }

        Ok(expr)
    }

    fn finish_call(&mut self, callee: Expr) -> Result<Expr, LyslynError> {
        let mut args = Vec::new();
        if !self.check(&TokenType::RParen) {
            args.push(self.expression()?);
            while self.match_token(&TokenType::Comma) {
                args.push(self.expression()?);
            }
        }
        let span = self.consume(&TokenType::RParen, "Expected ')' after arguments")?.span.clone();
        Ok(Expr::Call(Box::new(callee), args, span))
    }

    fn consume_property_name(&mut self) -> Result<Token, LyslynError> {
        if let TokenType::Identifier(_) = self.peek().token_type {
            Ok(self.advance().clone())
        } else if self.peek().lexeme.chars().all(|c| c.is_alphabetic() || c == '_') {
            Ok(self.advance().clone())
        } else {
            Err(self.error("Expected property name after '.'"))
        }
    }

    fn primary(&mut self) -> Result<Expr, LyslynError> {
        let tok = self.peek().clone();

        match tok.token_type {
            TokenType::Int(val) => {
                self.advance();
                Ok(Expr::Literal(LiteralValue::Int(val), tok.span))
            }
            TokenType::Float(val) => {
                self.advance();
                Ok(Expr::Literal(LiteralValue::Float(val), tok.span))
            }
            TokenType::String(ref s) => {
                let s_clone = s.clone();
                let span_clone = tok.span.clone();
                self.advance();
                Ok(self.parse_string_with_interpolation(&s_clone, &span_clone))
            }
            TokenType::True => {
                self.advance();
                Ok(Expr::Literal(LiteralValue::Bool(true), tok.span))
            }
            TokenType::False => {
                self.advance();
                Ok(Expr::Literal(LiteralValue::Bool(false), tok.span))
            }
            TokenType::Nil => {
                self.advance();
                Ok(Expr::Literal(LiteralValue::Nil, tok.span))
            }
            TokenType::Identifier(ref name) => {
                self.advance();
                Ok(Expr::Variable(name.clone(), tok.span))
            }
            TokenType::LParen => {
                self.advance();
                let expr = self.expression()?;
                self.consume(&TokenType::RParen, "Expected ')' after expression")?;
                Ok(expr)
            }
            TokenType::LBracket => {
                self.advance();
                let mut elements = Vec::new();
                if !self.check(&TokenType::RBracket) {
                    elements.push(self.expression()?);
                    while self.match_token(&TokenType::Comma) {
                        elements.push(self.expression()?);
                    }
                }
                let span = self.consume(&TokenType::RBracket, "Expected ']' after list")?.span.clone();
                Ok(Expr::List(elements, span))
            }
            TokenType::LBrace => {
                self.advance();
                let mut entries = Vec::new();
                if !self.check(&TokenType::RBrace) {
                    loop {
                        let key = self.expression()?;
                        self.consume(&TokenType::Colon, "Expected ':' after map key")?;
                        let val = self.expression()?;
                        entries.push((key, val));
                        if !self.match_token(&TokenType::Comma) {
                            break;
                        }
                    }
                }
                let span = self.consume(&TokenType::RBrace, "Expected '}' after map")?.span.clone();
                Ok(Expr::Map(entries, span))
            }
            TokenType::A | TokenType::An => {
                let next_is_coll = if self.current + 1 < self.tokens.len() {
                    matches!(
                        self.tokens[self.current + 1].token_type,
                        TokenType::List | TokenType::Object | TokenType::Empty
                    )
                } else {
                    false
                };

                if !next_is_coll {
                    self.advance();
                    return Ok(Expr::Variable(tok.lexeme, tok.span));
                }

                self.advance();
                let span = tok.span;

                if self.match_token(&TokenType::Empty) {
                    if self.match_token(&TokenType::List) {
                        return Ok(Expr::List(Vec::new(), span));
                    } else if self.match_token(&TokenType::Object) {
                        return Ok(Expr::Map(Vec::new(), span));
                    }
                }

                if self.match_token(&TokenType::List) {
                    let _ = self.match_token(&TokenType::Of);
                    let mut elements = Vec::new();
                    if !self.check(&TokenType::Newline) && !self.is_at_end() {
                        elements.push(self.comparison()?);
                        while self.match_token(&TokenType::Comma) || self.match_token(&TokenType::And) {
                            elements.push(self.comparison()?);
                        }
                    }
                    return Ok(Expr::List(elements, span));
                }

                if self.match_token(&TokenType::Object) {
                    let _ = self.match_token(&TokenType::With);
                    self.consume(&TokenType::Colon, "Expected ':' after 'an object with'")?;
                    while self.match_token(&TokenType::Newline) {}
                    self.consume(&TokenType::Indent, "Expected indented block for object fields")?;

                    let mut entries = Vec::new();
                    while !self.check(&TokenType::Dedent) && !self.is_at_end() {
                        while self.match_token(&TokenType::Newline) {}
                        if self.check(&TokenType::Dedent) || self.is_at_end() {
                            break;
                        }

                        let key_tok = self.consume_property_name()?;
                        let key_expr = Expr::Literal(LiteralValue::String(key_tok.lexeme), key_tok.span.clone());
                        self.consume(&TokenType::Colon, "Expected ':' after object field name")?;
                        let val_expr = self.expression()?;
                        entries.push((key_expr, val_expr));

                        while self.match_token(&TokenType::Newline) {}
                    }

                    self.consume(&TokenType::Dedent, "Expected dedent at end of object block")?;
                    return Ok(Expr::Map(entries, span));
                }

                Err(self.error("Expected 'list' or 'object' after 'a'/'an'"))
            }
            TokenType::Ask => {
                self.advance();
                let prompt = if !self.check(&TokenType::Newline) && !self.is_at_end() {
                    Some(Box::new(self.expression()?))
                } else {
                    None
                };
                Ok(Expr::Ask(prompt, tok.span))
            }
            TokenType::Call => {
                self.advance();
                let span = tok.span;
                let callee = self.primary()?;
                let mut args = Vec::new();
                if self.match_token(&TokenType::With) {
                    args.push(self.comparison()?);
                    while self.match_token(&TokenType::Comma) || self.match_token(&TokenType::And) {
                        args.push(self.comparison()?);
                    }
                }
                Ok(Expr::Call(Box::new(callee), args, span))
            }
            TokenType::If => {
                self.advance();
                let span = tok.span.clone();
                let cond = self.expression()?;
                let _ = self.match_token(&TokenType::Colon);
                let then_expr = self.expression()?;
                if self.match_token(&TokenType::Otherwise) || self.match_token(&TokenType::Else) {
                    let _ = self.match_token(&TokenType::Colon);
                    let else_expr = self.expression()?;
                    Ok(Expr::If(
                        Box::new(cond),
                        Box::new(then_expr),
                        Box::new(else_expr),
                        span,
                    ))
                } else {
                    Err(self.error("Expected 'Otherwise:' or 'Else:' in inline if expression"))
                }
            }
            TokenType::Port
            | TokenType::Body
            | TokenType::Data
            | TokenType::Headers
            | TokenType::Params
            | TokenType::Timeout
            | TokenType::Response
            | TokenType::Request
            | TokenType::Status
            | TokenType::Add
            | TokenType::Error => {
                self.advance();
                Ok(Expr::Variable(tok.lexeme.clone(), tok.span))
            }
            _ => Err(self.error(format!("Unexpected token '{:?}' in expression", tok.token_type))),
        }
    }

    fn consume(&mut self, expected: &TokenType, message: &str) -> Result<&Token, LyslynError> {
        if self.check(expected) {
            Ok(self.advance())
        } else {
            Err(self.error(message))
        }
    }

    fn consume_identifier(&mut self, message: &str) -> Result<Token, LyslynError> {
        let tok = self.peek().clone();
        if let TokenType::Identifier(_) = tok.token_type {
            self.advance();
            return Ok(tok);
        }
        if !tok.lexeme.is_empty() && tok.lexeme.chars().all(|c| c.is_alphabetic() || c == '_') {
            self.advance();
            return Ok(tok);
        }
        Err(self.error(message))
    }

    fn match_token(&mut self, token_type: &TokenType) -> bool {
        if self.check(token_type) {
            self.advance();
            true
        } else {
            false
        }
    }

    fn check(&self, token_type: &TokenType) -> bool {
        if self.is_at_end() {
            *token_type == TokenType::Eof
        } else {
            std::mem::discriminant(&self.peek().token_type) == std::mem::discriminant(token_type)
        }
    }

    fn advance(&mut self) -> &Token {
        if !self.is_at_end() {
            self.current += 1;
        }
        self.previous()
    }

    fn is_at_end(&self) -> bool {
        self.peek().token_type == TokenType::Eof
    }

    fn peek(&self) -> &Token {
        &self.tokens[self.current]
    }

    fn previous(&self) -> &Token {
        &self.tokens[self.current - 1]
    }

    fn parse_string_with_interpolation(&mut self, s: &str, span: &Span) -> Expr {
        if !s.contains('{') || !s.contains('}') {
            return Expr::Literal(LiteralValue::String(s.to_string()), span.clone());
        }

        let mut parts: Vec<Expr> = Vec::new();
        let mut last_idx = 0;
        let chars: Vec<char> = s.chars().collect();
        let mut i = 0;

        while i < chars.len() {
            if chars[i] == '{' {
                let start = i;
                let mut end = start + 1;
                while end < chars.len() && chars[end] != '}' {
                    end += 1;
                }

                if end < chars.len() && chars[end] == '}' {
                    if start > last_idx {
                        let text: String = chars[last_idx..start].iter().collect();
                        parts.push(Expr::Literal(LiteralValue::String(text), span.clone()));
                    }

                    let expr_str: String = chars[start + 1..end].iter().collect();
                    let expr_str_trimmed = expr_str.trim();

                    if !expr_str_trimmed.contains(':') && !expr_str_trimmed.is_empty() {
                        let mut sub_scanner = Scanner::new(expr_str_trimmed, &self.filename);
                        if let Ok(tokens) = sub_scanner.scan_tokens() {
                            let mut sub_parser = Parser::new(tokens, &self.filename, expr_str_trimmed);
                            if let Ok(inner) = sub_parser.expression() {
                                if sub_parser.is_at_end() || sub_parser.check(&TokenType::Newline) {
                                    parts.push(inner);
                                    i = end + 1;
                                    last_idx = i;
                                    continue;
                                }
                            }
                        }
                    }

                    parts.push(Expr::Literal(
                        LiteralValue::String(format!("{{{}}}", expr_str)),
                        span.clone(),
                    ));

                    i = end + 1;
                    last_idx = i;
                    continue;
                }
            }
            i += 1;
        }

        if last_idx < chars.len() {
            let text: String = chars[last_idx..].iter().collect();
            parts.push(Expr::Literal(LiteralValue::String(text), span.clone()));
        }

        if parts.is_empty() {
            return Expr::Literal(LiteralValue::String(String::new()), span.clone());
        }

        let mut result = parts.remove(0);
        for part in parts {
            let part_span = part.span();
            result = Expr::Binary(Box::new(result), BinaryOp::Add, Box::new(part), part_span);
        }

        result
    }

    fn error(&self, message: impl Into<String>) -> LyslynError {
        let tok = self.peek();
        LyslynError::new(ErrorKind::Parser, message, tok.span.clone(), &self.filename)
            .with_source(&self.source)
    }
}
