use crate::ast::*;
use crate::bytecode::chunk::Chunk;
use crate::bytecode::opcodes::OpCode;
use crate::errors::{ErrorKind, LyslynError, Span};
use crate::values::{LyslynFunction, Value};
use std::rc::Rc;

#[allow(dead_code)]
#[derive(Clone)]
struct Local {
    name: String,
    depth: usize,
    is_captured: bool,
}

pub struct Compiler {
    filename: String,
    source: String,
    chunk: Chunk,
    locals: Vec<Local>,
    scope_depth: usize,
    loop_stack: Vec<(usize, Vec<usize>)>,
    #[allow(dead_code)]
    is_function: bool,
}

impl Compiler {
    pub fn new(filename: &str, source: &str) -> Self {
        Compiler {
            filename: filename.to_string(),
            source: source.to_string(),
            chunk: Chunk::new("<main>"),
            locals: Vec::new(),
            scope_depth: 0,
            loop_stack: Vec::new(),
            is_function: false,
        }
    }

    fn new_function(name: &str, filename: &str, source: &str) -> Self {
        Compiler {
            filename: filename.to_string(),
            source: source.to_string(),
            chunk: Chunk::new(name),
            locals: Vec::new(),
            scope_depth: 0,
            loop_stack: Vec::new(),
            is_function: true,
        }
    }

    pub fn compile(&mut self, program: &Program) -> Result<Chunk, LyslynError> {
        for stmt in &program.statements {
            self.compile_stmt(stmt)?;
        }

        self.emit_opcode(OpCode::Halt, 1);
        Ok(std::mem::replace(&mut self.chunk, Chunk::new("<main>")))
    }

    fn compile_stmt(&mut self, stmt: &Stmt) -> Result<(), LyslynError> {
        match stmt {
            Stmt::Set {
                target,
                value,
                is_constant: _,
                span,
            } => self.compile_set(target, value, span.line)?,
            Stmt::Class {
                name,
                superclass,
                constructor,
                methods,
                span,
            } => self.compile_class(name, superclass, constructor, methods, span.line)?,
            Stmt::CallParent { method, args, span } => {
                self.compile_call_parent(method, args, span.line)?;
            }
            Stmt::Change {
                target,
                operation,
                value,
                span,
            } => self.compile_change(target, operation, value, span.line)?,
            Stmt::If {
                branches,
                otherwise_branch,
                span: _,
            } => self.compile_if(branches, otherwise_branch)?,
            Stmt::While {
                condition,
                body,
                span: _,
            } => self.compile_while(condition, body)?,
            Stmt::For {
                variable,
                iterable,
                body,
                span: _,
            } => self.compile_for(variable, iterable, body)?,
            Stmt::Repeat {
                count,
                body,
                span: _,
            } => self.compile_repeat(count, body)?,
            Stmt::Function {
                name,
                params,
                body,
                is_async: _,
                span,
            } => self.compile_function(name, params, body, span.line)?,
            Stmt::Return { value, span } => {
                if let Some(ref val_expr) = value {
                    self.compile_expr(val_expr)?;
                } else {
                    self.emit_opcode(OpCode::Nil, span.line);
                }
                self.emit_opcode(OpCode::Return, span.line);
            }
            Stmt::Break(span) => {
                if self.loop_stack.is_empty() {
                    return Err(self.error(span, "Cannot break outside loop"));
                }
                let jump = self.emit_jump(OpCode::Jump, span.line);
                self.loop_stack.last_mut().unwrap().1.push(jump);
            }
            Stmt::Continue(span) => {
                if self.loop_stack.is_empty() {
                    return Err(self.error(span, "Cannot continue outside loop"));
                }
                let start = self.loop_stack.last().unwrap().0;
                self.emit_loop(start, span.line);
            }
            Stmt::Say { expressions, span } => {
                for expr in expressions {
                    self.compile_expr(expr)?;
                }
                self.emit_opcode(OpCode::Say, span.line);
                self.chunk.write_byte(expressions.len() as u8, span.line);
            }
            Stmt::Assert {
                condition,
                message,
                span,
            } => {
                self.compile_expr(condition)?;
                let ok_jump = self.emit_jump(OpCode::JumpIfFalse, span.line);
                let skip_raise = self.emit_jump(OpCode::Jump, span.line);
                self.patch_jump(ok_jump);

                if let Some(msg) = message {
                    self.compile_expr(msg)?;
                } else {
                    let c = self
                        .chunk
                        .add_constant(Value::Str("Assertion failed".to_string()));
                    self.emit_opcode(OpCode::Constant, span.line);
                    self.chunk.write_u16(c, span.line);
                }
                self.emit_opcode(OpCode::Halt, span.line);
                self.patch_jump(skip_raise);
            }
            Stmt::Get {
                module_name,
                alias,
                span,
            }
            | Stmt::Import {
                module_name,
                alias,
                names: _,
                span,
            } => {
                let const_idx = self
                    .chunk
                    .add_constant(Value::Str(module_name.clone()));
                self.emit_opcode(OpCode::GetModule, span.line);
                self.chunk.write_u16(const_idx, span.line);

                let default_name = std::path::Path::new(module_name)
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or(module_name);
                let bind_name = alias.as_deref().unwrap_or(default_name);
                self.define_variable(bind_name, span.line);
            }
            Stmt::Try {
                try_block,
                catch_var,
                catch_block,
                finally_block,
                span,
            } => {
                let catch_jump = self.emit_jump(OpCode::PushTry, span.line);
                self.begin_scope();
                for s in try_block {
                    self.compile_stmt(s)?;
                }
                self.end_scope(span.line);
                self.emit_opcode(OpCode::PopTry, span.line);
                let skip_catch = self.emit_jump(OpCode::Jump, span.line);

                self.patch_jump(catch_jump);
                if let Some(ref c_block) = catch_block {
                    self.begin_scope();
                    if let Some(ref var_name) = catch_var {
                        self.define_or_set_variable(var_name, span.line);
                    } else {
                        self.emit_opcode(OpCode::Pop, span.line);
                    }
                    for s in c_block {
                        self.compile_stmt(s)?;
                    }
                    self.end_scope(span.line);
                } else {
                    self.emit_opcode(OpCode::Pop, span.line);
                }

                self.patch_jump(skip_catch);
                if let Some(ref f_block) = finally_block {
                    self.begin_scope();
                    for s in f_block {
                        self.compile_stmt(s)?;
                    }
                    self.end_scope(span.line);
                }
            }
            Stmt::Raise { expression, span } => {
                self.compile_expr(expression)?;
                self.emit_opcode(OpCode::Raise, span.line);
            }
            Stmt::HttpRequest {
                method,
                url,
                headers,
                data,
                params: _,
                timeout,
                response_var,
                span,
            } => {
                let m_idx = self.chunk.add_constant(Value::Str(method.clone()));
                self.emit_opcode(OpCode::Constant, span.line);
                self.chunk.write_u16(m_idx, span.line);

                self.compile_expr(url)?;

                if let Some(h) = headers {
                    self.compile_expr(h)?;
                } else {
                    self.emit_opcode(OpCode::Nil, span.line);
                }

                if let Some(d) = data {
                    self.compile_expr(d)?;
                } else {
                    self.emit_opcode(OpCode::Nil, span.line);
                }

                if let Some(t) = timeout {
                    self.compile_expr(t)?;
                } else {
                    self.emit_opcode(OpCode::Nil, span.line);
                }

                self.emit_opcode(OpCode::HttpRequest, span.line);
                self.define_or_set_variable(response_var, span.line);
            }
            Stmt::Serve { port, .. } => {
                self.compile_expr(port)?;
                self.emit_opcode(OpCode::Serve, port.span().line);
            }
            Stmt::Respond { status, payload, .. } => {
                self.compile_expr(status)?;
                self.compile_expr(payload)?;
                self.emit_opcode(OpCode::Respond, status.span().line);
            }
            Stmt::Validate { schema, .. } => {
                self.compile_expr(schema)?;
                self.emit_opcode(OpCode::Validate, schema.span().line);
            }
            Stmt::AddToList { item, list, span } => {
                self.compile_expr(list)?;
                self.compile_expr(item)?;
                self.emit_opcode(OpCode::AddToList, span.line);
            }
            Stmt::Expr(expr) => {
                self.compile_expr(expr)?;
                self.emit_opcode(OpCode::Pop, expr.span().line);
            }
            Stmt::Block(stmts, _) => {
                self.begin_scope();
                for s in stmts {
                    self.compile_stmt(s)?;
                }
                self.end_scope(stmts.last().map(|s| s.span().line).unwrap_or(1));
            }
        }

        Ok(())
    }

    fn compile_set(&mut self, target: &Expr, value: &Expr, line: usize) -> Result<(), LyslynError> {
        match target {
            Expr::Variable(name, _) => {
                self.compile_expr(value)?;
                self.define_or_set_variable(name, line);
            }
            Expr::MemberAccess(obj, prop, _) => {
                self.compile_expr(obj)?;
                self.compile_expr(value)?;
                let prop_idx = self.chunk.add_constant(Value::Str(prop.clone()));
                self.emit_opcode(OpCode::SetProperty, line);
                self.chunk.write_u16(prop_idx, line);
            }
            Expr::IndexAccess(target, index, _) => {
                self.compile_expr(target)?;
                self.compile_expr(index)?;
                self.compile_expr(value)?;
                self.emit_opcode(OpCode::IndexSet, line);
            }
            _ => return Err(self.error(&target.span(), "Invalid assignment target")),
        }
        Ok(())
    }

    fn compile_change(
        &mut self,
        target: &Expr,
        op: &str,
        value: &Expr,
        line: usize,
    ) -> Result<(), LyslynError> {
        match target {
            Expr::Variable(name, _) => {
                self.compile_variable_load(name, line);
                self.compile_expr(value)?;
                match op {
                    "+" => self.emit_opcode(OpCode::Add, line),
                    "-" => self.emit_opcode(OpCode::Sub, line),
                    "*" => self.emit_opcode(OpCode::Mul, line),
                    "/" => self.emit_opcode(OpCode::Div, line),
                    _ => self.emit_opcode(OpCode::Add, line),
                }
                self.compile_variable_store(name, line);
            }
            _ => return Err(self.error(&target.span(), "Invalid target in change statement")),
        }
        Ok(())
    }

    fn compile_if(
        &mut self,
        branches: &[(Expr, Vec<Stmt>)],
        otherwise: &Option<Vec<Stmt>>,
    ) -> Result<(), LyslynError> {
        let mut end_jumps = Vec::new();

        for (cond, body) in branches {
            self.compile_expr(cond)?;
            let false_jump = self.emit_jump(OpCode::JumpIfFalse, cond.span().line);

            self.begin_scope();
            for s in body {
                self.compile_stmt(s)?;
            }
            self.end_scope(cond.span().line);

            let exit_jump = self.emit_jump(OpCode::Jump, cond.span().line);
            end_jumps.push(exit_jump);

            self.patch_jump(false_jump);
        }

        if let Some(otherwise_body) = otherwise {
            self.begin_scope();
            for s in otherwise_body {
                self.compile_stmt(s)?;
            }
            self.end_scope(1);
        }

        for j in end_jumps {
            self.patch_jump(j);
        }

        Ok(())
    }

    fn compile_while(&mut self, cond: &Expr, body: &[Stmt]) -> Result<(), LyslynError> {
        let loop_start = self.chunk.code.len();
        self.loop_stack.push((loop_start, Vec::new()));

        self.compile_expr(cond)?;
        let exit_jump = self.emit_jump(OpCode::JumpIfFalse, cond.span().line);

        self.begin_scope();
        for s in body {
            self.compile_stmt(s)?;
        }
        self.end_scope(cond.span().line);

        self.emit_loop(loop_start, cond.span().line);
        self.patch_jump(exit_jump);

        let (_, breaks) = self.loop_stack.pop().unwrap();
        for b in breaks {
            self.patch_jump(b);
        }

        Ok(())
    }

    fn compile_for(&mut self, var: &str, iter: &Expr, body: &[Stmt]) -> Result<(), LyslynError> {
        self.begin_scope();

        self.compile_expr(iter)?;
        let iter_slot = self.locals.len();
        self.locals.push(Local {
            name: "$iter".to_string(),
            depth: self.scope_depth,
            is_captured: false,
        });

        let zero = self.chunk.add_constant(Value::Int(0));
        self.emit_opcode(OpCode::Constant, iter.span().line);
        self.chunk.write_u16(zero, iter.span().line);
        let idx_slot = self.locals.len();
        self.locals.push(Local {
            name: "$idx".to_string(),
            depth: self.scope_depth,
            is_captured: false,
        });

        let loop_start = self.chunk.code.len();
        self.loop_stack.push((loop_start, Vec::new()));

        self.emit_opcode(OpCode::GetLocal, iter.span().line);
        self.chunk.write_u16(idx_slot as u16, iter.span().line);

        self.emit_opcode(OpCode::GetLocal, iter.span().line);
        self.chunk.write_u16(iter_slot as u16, iter.span().line);

        let len_idx = self
            .chunk
            .add_constant(Value::Str("length".to_string()));
        self.emit_opcode(OpCode::GetProperty, iter.span().line);
        self.chunk.write_u16(len_idx, iter.span().line);

        self.emit_opcode(OpCode::Less, iter.span().line);
        let exit_jump = self.emit_jump(OpCode::JumpIfFalse, iter.span().line);

        self.emit_opcode(OpCode::GetLocal, iter.span().line);
        self.chunk.write_u16(iter_slot as u16, iter.span().line);

        self.emit_opcode(OpCode::GetLocal, iter.span().line);
        self.chunk.write_u16(idx_slot as u16, iter.span().line);

        self.emit_opcode(OpCode::IndexGet, iter.span().line);
        self.define_or_set_variable(var, iter.span().line);

        self.emit_opcode(OpCode::GetLocal, iter.span().line);
        self.chunk.write_u16(idx_slot as u16, iter.span().line);
        let one = self.chunk.add_constant(Value::Int(1));
        self.emit_opcode(OpCode::Constant, iter.span().line);
        self.chunk.write_u16(one, iter.span().line);
        self.emit_opcode(OpCode::Add, iter.span().line);
        self.emit_opcode(OpCode::SetLocal, iter.span().line);
        self.chunk.write_u16(idx_slot as u16, iter.span().line);

        self.begin_scope();
        for s in body {
            self.compile_stmt(s)?;
        }
        self.end_scope(iter.span().line);

        self.emit_loop(loop_start, iter.span().line);
        self.patch_jump(exit_jump);

        let (_, breaks) = self.loop_stack.pop().unwrap();
        for b in breaks {
            self.patch_jump(b);
        }

        self.end_scope(iter.span().line);
        Ok(())
    }

    fn compile_repeat(&mut self, count: &Expr, body: &[Stmt]) -> Result<(), LyslynError> {
        self.begin_scope();

        self.compile_expr(count)?;
        let count_slot = self.locals.len();
        self.locals.push(Local {
            name: "$count".to_string(),
            depth: self.scope_depth,
            is_captured: false,
        });

        let zero = self.chunk.add_constant(Value::Int(0));
        self.emit_opcode(OpCode::Constant, count.span().line);
        self.chunk.write_u16(zero, count.span().line);
        let idx_slot = self.locals.len();
        self.locals.push(Local {
            name: "$idx".to_string(),
            depth: self.scope_depth,
            is_captured: false,
        });

        let loop_start = self.chunk.code.len();
        self.loop_stack.push((loop_start, Vec::new()));

        self.emit_opcode(OpCode::GetLocal, count.span().line);
        self.chunk.write_u16(idx_slot as u16, count.span().line);

        self.emit_opcode(OpCode::GetLocal, count.span().line);
        self.chunk.write_u16(count_slot as u16, count.span().line);

        self.emit_opcode(OpCode::Less, count.span().line);
        let exit_jump = self.emit_jump(OpCode::JumpIfFalse, count.span().line);

        self.emit_opcode(OpCode::GetLocal, count.span().line);
        self.chunk.write_u16(idx_slot as u16, count.span().line);
        let one = self.chunk.add_constant(Value::Int(1));
        self.emit_opcode(OpCode::Constant, count.span().line);
        self.chunk.write_u16(one, count.span().line);
        self.emit_opcode(OpCode::Add, count.span().line);
        self.emit_opcode(OpCode::SetLocal, count.span().line);
        self.chunk.write_u16(idx_slot as u16, count.span().line);

        self.begin_scope();
        for s in body {
            self.compile_stmt(s)?;
        }
        self.end_scope(count.span().line);

        self.emit_loop(loop_start, count.span().line);
        self.patch_jump(exit_jump);

        let (_, breaks) = self.loop_stack.pop().unwrap();
        for b in breaks {
            self.patch_jump(b);
        }

        self.end_scope(count.span().line);
        Ok(())
    }

    fn compile_function(
        &mut self,
        name: &str,
        params: &[String],
        body: &[Stmt],
        line: usize,
    ) -> Result<(), LyslynError> {
        let mut fn_compiler = Compiler::new_function(name, &self.filename, &self.source);
        fn_compiler.begin_scope();

        for s in body {
            fn_compiler.compile_stmt(s)?;
        }

        fn_compiler.emit_opcode(OpCode::Nil, line);
        fn_compiler.emit_opcode(OpCode::Return, line);

        let fn_chunk = fn_compiler.chunk;
        let lys_fn = LyslynFunction {
            name: name.to_string(),
            params: params.to_vec(),
            arity: params.len(),
            chunk: fn_chunk,
            closure_env: None,
        };

        let fn_const = self.chunk.add_constant(Value::Function(Rc::new(lys_fn)));
        self.emit_opcode(OpCode::Closure, line);
        self.chunk.write_u16(fn_const, line);

        self.define_variable(name, line);
        Ok(())
    }

    fn compile_class(
        &mut self,
        name: &str,
        superclass: &Option<String>,
        constructor: &Option<ClassMethod>,
        methods: &[ClassMethod],
        line: usize,
    ) -> Result<(), LyslynError> {
        let name_const = self.chunk.add_constant(Value::Str(name.to_string()));
        self.emit_opcode(OpCode::Class, line);
        self.chunk.write_u16(name_const, line);

        if let Some(ref sup) = superclass {
            self.compile_variable_load(sup, line);
            self.emit_opcode(OpCode::Inherit, line);
        }

        if let Some(ref c) = constructor {
            let mut fn_compiler =
                Compiler::new_function(&format!("{}.initialize", name), &self.filename, &self.source);
            fn_compiler.begin_scope();
            for s in &c.body {
                fn_compiler.compile_stmt(s)?;
            }
            fn_compiler.emit_opcode(OpCode::Nil, line);
            fn_compiler.emit_opcode(OpCode::Return, line);

            let fn_chunk = fn_compiler.chunk;
            let lys_fn = LyslynFunction {
                name: "initialize".to_string(),
                params: c.params.clone(),
                arity: c.params.len(),
                chunk: fn_chunk,
                closure_env: None,
            };
            let fn_const = self.chunk.add_constant(Value::Function(Rc::new(lys_fn)));
            self.emit_opcode(OpCode::Constant, line);
            self.chunk.write_u16(fn_const, line);
            self.emit_opcode(OpCode::Constructor, line);
        }

        for m in methods {
            let mut fn_compiler =
                Compiler::new_function(&format!("{}.{}", name, m.name), &self.filename, &self.source);
            fn_compiler.begin_scope();
            for s in &m.body {
                fn_compiler.compile_stmt(s)?;
            }
            fn_compiler.emit_opcode(OpCode::Nil, line);
            fn_compiler.emit_opcode(OpCode::Return, line);

            let fn_chunk = fn_compiler.chunk;
            let lys_fn = LyslynFunction {
                name: m.name.clone(),
                params: m.params.clone(),
                arity: m.params.len(),
                chunk: fn_chunk,
                closure_env: None,
            };
            let fn_const = self.chunk.add_constant(Value::Function(Rc::new(lys_fn)));
            self.emit_opcode(OpCode::Constant, line);
            self.chunk.write_u16(fn_const, line);

            let m_name_const = self.chunk.add_constant(Value::Str(m.name.clone()));
            self.emit_opcode(OpCode::Method, line);
            self.chunk.write_u16(m_name_const, line);
        }

        self.define_variable(name, line);
        Ok(())
    }

    fn compile_call_parent(
        &mut self,
        method: &Option<String>,
        args: &[Expr],
        line: usize,
    ) -> Result<(), LyslynError> {
        let m_name = method.clone().unwrap_or_else(|| "initialize".to_string());
        let m_const = self.chunk.add_constant(Value::Str(m_name));
        self.compile_variable_load("this", line);
        for arg in args {
            self.compile_expr(arg)?;
        }
        self.emit_opcode(OpCode::CallParent, line);
        self.chunk.write_u16(m_const, line);
        self.chunk.write_byte(args.len() as u8, line);
        self.emit_opcode(OpCode::Pop, line);
        Ok(())
    }

    pub fn compile_expr(&mut self, expr: &Expr) -> Result<(), LyslynError> {
        match expr {
            Expr::Literal(val, span) => match val {
                LiteralValue::Int(i) => {
                    let c = self.chunk.add_constant(Value::Int(*i));
                    self.emit_opcode(OpCode::Constant, span.line);
                    self.chunk.write_u16(c, span.line);
                }
                LiteralValue::Float(f) => {
                    let c = self.chunk.add_constant(Value::Float(*f));
                    self.emit_opcode(OpCode::Constant, span.line);
                    self.chunk.write_u16(c, span.line);
                }
                LiteralValue::String(s) => {
                    let c = self.chunk.add_constant(Value::Str(s.clone()));
                    self.emit_opcode(OpCode::Constant, span.line);
                    self.chunk.write_u16(c, span.line);
                }
                LiteralValue::Bool(true) => self.emit_opcode(OpCode::True, span.line),
                LiteralValue::Bool(false) => self.emit_opcode(OpCode::False, span.line),
                LiteralValue::Nil => self.emit_opcode(OpCode::Nil, span.line),
            },
            Expr::Variable(name, span) => {
                self.compile_variable_load(name, span.line);
            }
            Expr::Binary(left, op, right, span) => {
                match op {
                    BinaryOp::And => {
                        self.compile_expr(left)?;
                        self.emit_opcode(OpCode::Dup, span.line);
                        let jump = self.emit_jump(OpCode::JumpIfFalse, span.line);
                        self.emit_opcode(OpCode::Pop, span.line);
                        self.compile_expr(right)?;
                        self.patch_jump(jump);
                        return Ok(());
                    }
                    BinaryOp::Or => {
                        self.compile_expr(left)?;
                        self.emit_opcode(OpCode::Dup, span.line);
                        let else_jump = self.emit_jump(OpCode::JumpIfFalse, span.line);
                        let end_jump = self.emit_jump(OpCode::Jump, span.line);
                        self.patch_jump(else_jump);
                        self.emit_opcode(OpCode::Pop, span.line);
                        self.compile_expr(right)?;
                        self.patch_jump(end_jump);
                        return Ok(());
                    }
                    _ => {}
                }

                self.compile_expr(left)?;
                self.compile_expr(right)?;

                match op {
                    BinaryOp::Add => self.emit_opcode(OpCode::Add, span.line),
                    BinaryOp::Sub => self.emit_opcode(OpCode::Sub, span.line),
                    BinaryOp::Mul => self.emit_opcode(OpCode::Mul, span.line),
                    BinaryOp::Div => self.emit_opcode(OpCode::Div, span.line),
                    BinaryOp::Mod => self.emit_opcode(OpCode::Mod, span.line),
                    BinaryOp::Equal => self.emit_opcode(OpCode::Equal, span.line),
                    BinaryOp::NotEqual => self.emit_opcode(OpCode::NotEqual, span.line),
                    BinaryOp::Greater => self.emit_opcode(OpCode::Greater, span.line),
                    BinaryOp::GreaterEqual => self.emit_opcode(OpCode::GreaterEqual, span.line),
                    BinaryOp::Less => self.emit_opcode(OpCode::Less, span.line),
                    BinaryOp::LessEqual => self.emit_opcode(OpCode::LessEqual, span.line),
                    BinaryOp::In => self.emit_opcode(OpCode::In, span.line),
                    BinaryOp::NotIn => self.emit_opcode(OpCode::NotIn, span.line),
                    _ => {}
                }
            }
            Expr::Unary(op, operand, span) => {
                self.compile_expr(operand)?;
                match op {
                    UnaryOp::Neg => self.emit_opcode(OpCode::Neg, span.line),
                    UnaryOp::Not => self.emit_opcode(OpCode::Not, span.line),
                    UnaryOp::IsPositive => self.emit_opcode(OpCode::IsPositive, span.line),
                    UnaryOp::IsNegative => self.emit_opcode(OpCode::IsNegative, span.line),
                    UnaryOp::IsZero => self.emit_opcode(OpCode::IsZero, span.line),
                    UnaryOp::IsEven => self.emit_opcode(OpCode::IsEven, span.line),
                    UnaryOp::IsOdd => self.emit_opcode(OpCode::IsOdd, span.line),
                    UnaryOp::IsEmpty => self.emit_opcode(OpCode::IsEmpty, span.line),
                    UnaryOp::IsSomething => self.emit_opcode(OpCode::IsSomething, span.line),
                    UnaryOp::IsNotPositive => {
                        self.emit_opcode(OpCode::IsPositive, span.line);
                        self.emit_opcode(OpCode::Not, span.line);
                    }
                    UnaryOp::IsNotNegative => {
                        self.emit_opcode(OpCode::IsNegative, span.line);
                        self.emit_opcode(OpCode::Not, span.line);
                    }
                    UnaryOp::IsNotZero => {
                        self.emit_opcode(OpCode::IsZero, span.line);
                        self.emit_opcode(OpCode::Not, span.line);
                    }
                    UnaryOp::IsNotEven => {
                        self.emit_opcode(OpCode::IsEven, span.line);
                        self.emit_opcode(OpCode::Not, span.line);
                    }
                    UnaryOp::IsNotOdd => {
                        self.emit_opcode(OpCode::IsOdd, span.line);
                        self.emit_opcode(OpCode::Not, span.line);
                    }
                    UnaryOp::IsNotEmpty => {
                        self.emit_opcode(OpCode::IsEmpty, span.line);
                        self.emit_opcode(OpCode::Not, span.line);
                    }
                    UnaryOp::IsString => self.emit_opcode(OpCode::IsString, span.line),
                    UnaryOp::IsNumber => self.emit_opcode(OpCode::IsNumber, span.line),
                    UnaryOp::IsInteger => self.emit_opcode(OpCode::IsInteger, span.line),
                    UnaryOp::IsFloat => self.emit_opcode(OpCode::IsFloat, span.line),
                    UnaryOp::IsBoolean => self.emit_opcode(OpCode::IsBoolean, span.line),
                    UnaryOp::IsList => self.emit_opcode(OpCode::IsList, span.line),
                    UnaryOp::IsMap => self.emit_opcode(OpCode::IsMap, span.line),
                    UnaryOp::IsFunction => self.emit_opcode(OpCode::IsFunction, span.line),
                }
            }
            Expr::List(elements, span) => {
                for el in elements {
                    self.compile_expr(el)?;
                }
                self.emit_opcode(OpCode::BuildList, span.line);
                self.chunk.write_u16(elements.len() as u16, span.line);
            }
            Expr::Map(entries, span) => {
                for (k, v) in entries {
                    self.compile_expr(k)?;
                    self.compile_expr(v)?;
                }
                self.emit_opcode(OpCode::BuildMap, span.line);
                self.chunk.write_u16(entries.len() as u16, span.line);
            }
            Expr::MemberAccess(target, member, span) => {
                self.compile_expr(target)?;
                let prop_idx = self
                    .chunk
                    .add_constant(Value::Str(member.clone()));
                self.emit_opcode(OpCode::GetProperty, span.line);
                self.chunk.write_u16(prop_idx, span.line);
            }
            Expr::IndexAccess(target, index, span) => {
                self.compile_expr(target)?;
                self.compile_expr(index)?;
                self.emit_opcode(OpCode::IndexGet, span.line);
            }
            Expr::Call(callee, args, span) => {
                self.compile_expr(callee)?;
                for arg in args {
                    self.compile_expr(arg)?;
                }
                self.emit_opcode(OpCode::Call, span.line);
                self.chunk.write_byte(args.len() as u8, span.line);
            }
            Expr::If(cond, then_branch, else_branch, span) => {
                self.compile_expr(cond)?;
                let else_jump = self.emit_jump(OpCode::JumpIfFalse, span.line);
                self.compile_expr(then_branch)?;
                let end_jump = self.emit_jump(OpCode::Jump, span.line);
                self.patch_jump(else_jump);
                self.compile_expr(else_branch)?;
                self.patch_jump(end_jump);
            }
            Expr::This(span) => {
                self.compile_variable_load("this", span.line);
            }
            Expr::New { class_name, args, span } => {
                self.compile_variable_load(class_name, span.line);
                for arg in args {
                    self.compile_expr(arg)?;
                }
                self.emit_opcode(OpCode::New, span.line);
                self.chunk.write_byte(args.len() as u8, span.line);
            }
            Expr::IsInstance(expr, class_name, span) => {
                self.compile_expr(expr)?;
                let c = self.chunk.add_constant(Value::Str(class_name.clone()));
                self.emit_opcode(OpCode::IsInstance, span.line);
                self.chunk.write_u16(c, span.line);
            }
            Expr::TypeOf(expr, span) => {
                self.compile_expr(expr)?;
                self.emit_opcode(OpCode::TypeOf, span.line);
            }
            _ => {}
        }
        Ok(())
    }

    fn compile_variable_load(&mut self, name: &str, line: usize) {
        let c = self.chunk.add_constant(Value::Str(name.to_string()));
        self.emit_opcode(OpCode::GetGlobal, line);
        self.chunk.write_u16(c, line);
    }

    fn compile_variable_store(&mut self, name: &str, line: usize) {
        let c = self.chunk.add_constant(Value::Str(name.to_string()));
        self.emit_opcode(OpCode::SetGlobal, line);
        self.chunk.write_u16(c, line);
    }

    fn define_or_set_variable(&mut self, name: &str, line: usize) {
        let c = self.chunk.add_constant(Value::Str(name.to_string()));
        self.emit_opcode(OpCode::SetGlobal, line);
        self.chunk.write_u16(c, line);
    }

    fn define_variable(&mut self, name: &str, line: usize) {
        let c = self.chunk.add_constant(Value::Str(name.to_string()));
        self.emit_opcode(OpCode::DefGlobal, line);
        self.chunk.write_u16(c, line);
    }

    fn begin_scope(&mut self) {
        self.scope_depth += 1;
    }

    fn end_scope(&mut self, line: usize) {
        self.scope_depth -= 1;
        while let Some(local) = self.locals.last() {
            if local.depth > self.scope_depth {
                self.emit_opcode(OpCode::Pop, line);
                self.locals.pop();
            } else {
                break;
            }
        }
    }

    fn emit_opcode(&mut self, op: OpCode, line: usize) {
        self.chunk.write_opcode(op, line);
    }

    fn emit_jump(&mut self, op: OpCode, line: usize) -> usize {
        self.chunk.write_opcode(op, line);
        self.chunk.write_byte(0xff, line);
        self.chunk.write_byte(0xff, line);
        self.chunk.code.len() - 2
    }

    fn patch_jump(&mut self, offset: usize) {
        let target = self.chunk.code.len();
        self.chunk.code[offset] = ((target >> 8) & 0xff) as u8;
        self.chunk.code[offset + 1] = (target & 0xff) as u8;
    }

    fn emit_loop(&mut self, loop_start: usize, line: usize) {
        self.emit_opcode(OpCode::Loop, line);
        self.chunk.write_u16(loop_start as u16, line);
    }

    fn error(&self, span: &Span, msg: impl Into<String>) -> LyslynError {
        LyslynError::new(ErrorKind::Compile, msg, span.clone(), &self.filename)
            .with_source(&self.source)
    }
}
