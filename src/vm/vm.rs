use crate::bytecode::chunk::Chunk;
use crate::bytecode::opcodes::OpCode;
use crate::errors::{ErrorKind, LyslynError, Span};
use crate::modules::ModuleLoader;
use crate::values::{Environment, LyslynFunction, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;

pub struct CallFrame {
    pub function: Option<Rc<LyslynFunction>>,
    pub chunk: Chunk,
    pub ip: usize,
    pub slots_offset: usize,
    pub env: Rc<RefCell<Environment>>,
}

#[derive(Clone)]
pub struct TryHandler {
    pub catch_ip: usize,
    pub frame_index: usize,
    pub stack_depth: usize,
}

pub struct VM {
    pub stack: Vec<Value>,
    pub frames: Vec<CallFrame>,
    pub globals: IndexMap<String, Value>,
    pub module_loader: ModuleLoader,
    pub try_handlers: Vec<TryHandler>,
    pub capture_output: bool,
    pub output: Vec<String>,
}

impl VM {
    pub fn new(script_args: Option<Vec<String>>) -> Self {
        let mut globals = IndexMap::new();

        let args_list: Vec<Value> = script_args
            .unwrap_or_default()
            .into_iter()
            .map(Value::Str)
            .collect();
        globals.insert(
            "args".to_string(),
            Value::List(Rc::new(RefCell::new(args_list))),
        );

        globals.insert(
            "append".to_string(),
            Value::NativeFunction(
                "append".to_string(),
                Rc::new(|args| {
                    if args.len() >= 2 {
                        if let Value::List(l) = &args[0] {
                            l.borrow_mut().push(args[1].clone());
                            Ok(Value::Nil)
                        } else {
                            Err("Expected list as first argument to append".to_string())
                        }
                    } else {
                        Err("Expected 2 arguments to append(list, item)".to_string())
                    }
                }),
            ),
        );

        globals.insert(
            "pop".to_string(),
            Value::NativeFunction(
                "pop".to_string(),
                Rc::new(|args| {
                    if let Some(Value::List(l)) = args.first() {
                        let popped = l.borrow_mut().pop().unwrap_or(Value::Nil);
                        Ok(popped)
                    } else {
                        Err("Expected list argument to pop".to_string())
                    }
                }),
            ),
        );

        let len_fn = Value::NativeFunction(
            "len".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    match arg {
                        Value::Str(s) => Ok(Value::Int(s.chars().count() as i64)),
                        Value::List(l) => Ok(Value::Int(l.borrow().len() as i64)),
                        Value::Map(m) => Ok(Value::Int(m.borrow().len() as i64)),
                        _ => Err("Cannot get length of type".to_string()),
                    }
                } else {
                    Err("Expected 1 argument to len".to_string())
                }
            }),
        );
        globals.insert("len".to_string(), len_fn.clone());
        globals.insert("Length".to_string(), len_fn);

        let keys_fn = Value::NativeFunction(
            "keys".to_string(),
            Rc::new(|args| {
                if let Some(Value::Map(m)) = args.first() {
                    let k_list: Vec<Value> = m.borrow().keys().map(|k| Value::Str(k.clone())).collect();
                    Ok(Value::List(Rc::new(RefCell::new(k_list))))
                } else {
                    Err("Expected map argument to keys".to_string())
                }
            }),
        );
        globals.insert("keys".to_string(), keys_fn.clone());
        globals.insert("Keys".to_string(), keys_fn);

        let vals_fn = Value::NativeFunction(
            "values".to_string(),
            Rc::new(|args| {
                if let Some(Value::Map(m)) = args.first() {
                    let v_list: Vec<Value> = m.borrow().values().cloned().collect();
                    Ok(Value::List(Rc::new(RefCell::new(v_list))))
                } else {
                    Err("Expected map argument to values".to_string())
                }
            }),
        );
        globals.insert("values".to_string(), vals_fn.clone());
        globals.insert("Values".to_string(), vals_fn);

        globals.insert(
            "range".to_string(),
            Value::NativeFunction(
                "range".to_string(),
                Rc::new(|args| {
                    let (start, end) = match args.len() {
                        1 => {
                            if let Value::Int(n) = args[0] {
                                (0, n)
                            } else {
                                return Err("Expected integer to range".to_string());
                            }
                        }
                        2 => {
                            if let (Value::Int(s), Value::Int(e)) = (&args[0], &args[1]) {
                                (*s, *e)
                            } else {
                                return Err("Expected integers to range".to_string());
                            }
                        }
                        _ => return Err("Expected 1 or 2 arguments to range".to_string()),
                    };
                    let list: Vec<Value> = (start..end).map(Value::Int).collect();
                    Ok(Value::List(Rc::new(RefCell::new(list))))
                }),
            ),
        );

        let filter_ph = Value::NativeFunction("Filter".to_string(), Rc::new(|_| Ok(Value::Nil)));
        globals.insert("Filter".to_string(), filter_ph.clone());
        globals.insert("filter".to_string(), filter_ph);

        let map_ph = Value::NativeFunction("Map".to_string(), Rc::new(|_| Ok(Value::Nil)));
        globals.insert("Map".to_string(), map_ph.clone());
        globals.insert("map".to_string(), map_ph);

        let red_ph = Value::NativeFunction("Reduce".to_string(), Rc::new(|_| Ok(Value::Nil)));
        globals.insert("Reduce".to_string(), red_ph.clone());
        globals.insert("reduce".to_string(), red_ph);

        globals.insert(
            "Assert".to_string(),
            Value::NativeFunction(
                "Assert".to_string(),
                Rc::new(|args| {
                    if let Some(cond) = args.first() {
                        if !cond.is_truthy() {
                            let msg = if args.len() > 1 {
                                args[1].to_string()
                            } else {
                                "Assertion failed".to_string()
                            };
                            return Err(msg);
                        }
                    }
                    Ok(Value::Nil)
                }),
            ),
        );

        VM {
            stack: Vec::new(),
            frames: Vec::new(),
            globals,
            module_loader: ModuleLoader::new(),
            try_handlers: Vec::new(),
            capture_output: false,
            output: Vec::new(),
        }
    }

    pub fn run(&mut self, chunk: Chunk) -> Result<Value, LyslynError> {
        self.stack.clear();
        self.frames.clear();
        self.try_handlers.clear();

        self.frames.push(CallFrame {
            function: None,
            chunk,
            ip: 0,
            slots_offset: 0,
            env: Rc::new(RefCell::new(Environment::new())),
        });

        while !self.frames.is_empty() {
            if self.frames.last().unwrap().ip >= self.frames.last().unwrap().chunk.code.len() {
                break;
            }
            if !self.step()? {
                break;
            }
        }

        Ok(self.stack.pop().unwrap_or(Value::Nil))
    }

    pub fn call_value(
        &mut self,
        callee: &Value,
        args: Vec<Value>,
        line: usize,
    ) -> Result<Value, LyslynError> {
        match callee {
            Value::NativeFunction(_, native_fn) => {
                native_fn(args).map_err(|e| self.runtime_error(line, e))
            }
            Value::Function(fn_rc) => {
                let mut new_env = if let Some(ref closure_env) = fn_rc.closure_env {
                    Environment::with_enclosing(closure_env.clone())
                } else {
                    Environment::new()
                };

                for (i, arg) in args.into_iter().enumerate() {
                    if i < fn_rc.params.len() {
                        new_env.define(&fn_rc.params[i], arg);
                    }
                }

                let slots_offset = self.stack.len();
                self.frames.push(CallFrame {
                    function: Some(fn_rc.clone()),
                    chunk: fn_rc.chunk.clone(),
                    ip: 0,
                    slots_offset,
                    env: Rc::new(RefCell::new(new_env)),
                });

                let target_frames = self.frames.len() - 1;
                while self.frames.len() > target_frames {
                    if !self.step()? {
                        break;
                    }
                }
                Ok(self.stack.pop().unwrap_or(Value::Nil))
            }
            _ => Err(self.runtime_error(line, format!("Cannot call '{}'", callee.type_name()))),
        }
    }

    pub fn handle_error(&mut self, err_val: Value, line: usize) -> Result<(), LyslynError> {
        if let Some(handler) = self.try_handlers.pop() {
            self.frames.truncate(handler.frame_index + 1);
            self.stack.truncate(handler.stack_depth);
            self.current_frame().ip = handler.catch_ip;
            self.stack.push(err_val);
            Ok(())
        } else {
            Err(self.runtime_error(line, err_val.to_string()))
        }
    }

    pub fn step(&mut self) -> Result<bool, LyslynError> {
        if self.frames.is_empty() {
            return Ok(false);
        }

        let frame = self.frames.last_mut().unwrap();
        if frame.ip >= frame.chunk.code.len() {
            return Ok(false);
        }

        let op_byte = frame.chunk.code[frame.ip];
        let line = frame.chunk.lines[frame.ip];
        frame.ip += 1;

        let opcode = match op_byte {
            x if x == OpCode::Constant as u8 => OpCode::Constant,
            x if x == OpCode::Nil as u8 => OpCode::Nil,
            x if x == OpCode::True as u8 => OpCode::True,
            x if x == OpCode::False as u8 => OpCode::False,
            x if x == OpCode::Pop as u8 => OpCode::Pop,
            x if x == OpCode::Dup as u8 => OpCode::Dup,
            x if x == OpCode::DefGlobal as u8 => OpCode::DefGlobal,
            x if x == OpCode::GetGlobal as u8 => OpCode::GetGlobal,
            x if x == OpCode::SetGlobal as u8 => OpCode::SetGlobal,
            x if x == OpCode::GetLocal as u8 => OpCode::GetLocal,
            x if x == OpCode::SetLocal as u8 => OpCode::SetLocal,
            x if x == OpCode::Add as u8 => OpCode::Add,
            x if x == OpCode::Sub as u8 => OpCode::Sub,
            x if x == OpCode::Mul as u8 => OpCode::Mul,
            x if x == OpCode::Div as u8 => OpCode::Div,
            x if x == OpCode::Mod as u8 => OpCode::Mod,
            x if x == OpCode::Neg as u8 => OpCode::Neg,
            x if x == OpCode::Equal as u8 => OpCode::Equal,
            x if x == OpCode::NotEqual as u8 => OpCode::NotEqual,
            x if x == OpCode::Greater as u8 => OpCode::Greater,
            x if x == OpCode::GreaterEqual as u8 => OpCode::GreaterEqual,
            x if x == OpCode::Less as u8 => OpCode::Less,
            x if x == OpCode::LessEqual as u8 => OpCode::LessEqual,
            x if x == OpCode::Not as u8 => OpCode::Not,
            x if x == OpCode::In as u8 => OpCode::In,
            x if x == OpCode::NotIn as u8 => OpCode::NotIn,
            x if x == OpCode::IsPositive as u8 => OpCode::IsPositive,
            x if x == OpCode::IsNegative as u8 => OpCode::IsNegative,
            x if x == OpCode::IsZero as u8 => OpCode::IsZero,
            x if x == OpCode::IsEven as u8 => OpCode::IsEven,
            x if x == OpCode::IsOdd as u8 => OpCode::IsOdd,
            x if x == OpCode::IsEmpty as u8 => OpCode::IsEmpty,
            x if x == OpCode::IsSomething as u8 => OpCode::IsSomething,
            x if x == OpCode::Jump as u8 => OpCode::Jump,
            x if x == OpCode::JumpIfFalse as u8 => OpCode::JumpIfFalse,
            x if x == OpCode::Loop as u8 => OpCode::Loop,
            x if x == OpCode::PushTry as u8 => OpCode::PushTry,
            x if x == OpCode::PopTry as u8 => OpCode::PopTry,
            x if x == OpCode::Raise as u8 => OpCode::Raise,
            x if x == OpCode::Call as u8 => OpCode::Call,
            x if x == OpCode::Closure as u8 => OpCode::Closure,
            x if x == OpCode::Return as u8 => OpCode::Return,
            x if x == OpCode::BuildList as u8 => OpCode::BuildList,
            x if x == OpCode::BuildMap as u8 => OpCode::BuildMap,
            x if x == OpCode::IndexGet as u8 => OpCode::IndexGet,
            x if x == OpCode::IndexSet as u8 => OpCode::IndexSet,
            x if x == OpCode::GetProperty as u8 => OpCode::GetProperty,
            x if x == OpCode::SetProperty as u8 => OpCode::SetProperty,
            x if x == OpCode::Say as u8 => OpCode::Say,
            x if x == OpCode::AddToList as u8 => OpCode::AddToList,
            x if x == OpCode::GetModule as u8 => OpCode::GetModule,
            x if x == OpCode::Serve as u8 => OpCode::Serve,
            x if x == OpCode::Respond as u8 => OpCode::Respond,
            x if x == OpCode::Validate as u8 => OpCode::Validate,
            x if x == OpCode::HttpRequest as u8 => OpCode::HttpRequest,
            x if x == OpCode::Halt as u8 => OpCode::Halt,
            _ => {
                return Err(LyslynError::new(
                    ErrorKind::Runtime,
                    format!("Unknown opcode '{}'", op_byte),
                    Span::new(line, 1, 1),
                    &self.frames.last().unwrap().chunk.name,
                ));
            }
        };

        if std::env::var("LYSLYN_DEBUG").is_ok() {
            eprintln!(
                "DEBUG: ip={} line={} op={:?} stack={:?}",
                frame.ip - 1,
                line,
                opcode,
                self.stack
            );
        }

        match opcode {
            OpCode::Constant => {
                let idx = self.read_u16();
                let val = self.current_frame().chunk.constants[idx as usize].clone();
                self.stack.push(val);
            }
            OpCode::Nil => self.stack.push(Value::Nil),
            OpCode::True => self.stack.push(Value::Bool(true)),
            OpCode::False => self.stack.push(Value::Bool(false)),
            OpCode::Pop => {
                self.stack.pop();
            }
            OpCode::Dup => {
                let val = self.stack.last().unwrap().clone();
                self.stack.push(val);
            }
            OpCode::DefGlobal => {
                let idx = self.read_u16();
                let name = format!("{}", self.current_frame().chunk.constants[idx as usize]);
                let val = self.stack.pop().unwrap();
                let env_rc = self.current_frame().env.clone();
                if self.frames.len() == 1 {
                    self.globals.insert(name.clone(), val.clone());
                }
                env_rc.borrow_mut().define(&name, val);
            }
            OpCode::GetGlobal => {
                let idx = self.read_u16();
                let name = format!("{}", self.current_frame().chunk.constants[idx as usize]);
                let env_rc = self.current_frame().env.clone();
                let val_opt = env_rc.borrow().get(&name);
                if let Some(val) = val_opt {
                    self.stack.push(val);
                } else if let Some(val) = self.globals.get(&name) {
                    self.stack.push(val.clone());
                } else {
                    return Err(self.runtime_error(line, format!("Undefined variable '{}'", name)));
                }
            }
            OpCode::SetGlobal => {
                let idx = self.read_u16();
                let name = format!("{}", self.current_frame().chunk.constants[idx as usize]);
                let val = self.stack.pop().unwrap();
                let env_rc = self.current_frame().env.clone();
                if !env_rc.borrow_mut().set(&name, val.clone()) {
                    self.globals.insert(name.clone(), val.clone());
                    env_rc.borrow_mut().define(&name, val);
                }
            }
            OpCode::GetLocal => {
                let slot = self.read_u16() as usize;
                let offset = self.current_frame().slots_offset;
                self.stack.push(self.stack[offset + slot].clone());
            }
            OpCode::SetLocal => {
                let slot = self.read_u16() as usize;
                let offset = self.current_frame().slots_offset;
                let val = self.stack.pop().unwrap();
                self.stack[offset + slot] = val;
            }
            OpCode::Add => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                let res = a.add(&b).map_err(|e| self.runtime_error(line, e))?;
                self.stack.push(res);
            }
            OpCode::Sub => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                let res = a.sub(&b).map_err(|e| self.runtime_error(line, e))?;
                self.stack.push(res);
            }
            OpCode::Mul => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                let res = a.mul(&b).map_err(|e| self.runtime_error(line, e))?;
                self.stack.push(res);
            }
            OpCode::Div => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                match a.div(&b) {
                    Ok(res) => self.stack.push(res),
                    Err(e) => {
                        self.handle_error(Value::Str(e), line)?;
                    }
                }
            }
            OpCode::Mod => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                match a.rem(&b) {
                    Ok(res) => self.stack.push(res),
                    Err(e) => {
                        self.handle_error(Value::Str(e), line)?;
                    }
                }
            }
            OpCode::Neg => {
                let a = self.stack.pop().unwrap();
                let res = a.neg().map_err(|e| self.runtime_error(line, e))?;
                self.stack.push(res);
            }
            OpCode::Equal => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(a == b));
            }
            OpCode::NotEqual => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(a != b));
            }
            OpCode::Greater => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(a > b));
            }
            OpCode::GreaterEqual => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(a >= b));
            }
            OpCode::Less => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(a < b));
            }
            OpCode::LessEqual => {
                let b = self.stack.pop().unwrap();
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(a <= b));
            }
            OpCode::Not => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(!a.is_truthy()));
            }
            OpCode::In => {
                let container = self.stack.pop().unwrap_or(Value::Nil);
                let item = self.stack.pop().unwrap_or(Value::Nil);
                let found = match &container {
                    Value::List(l) => l.borrow().contains(&item),
                    Value::Map(m) => {
                        let key = match &item {
                            Value::Str(s) => s.clone(),
                            other => other.to_string(),
                        };
                        m.borrow().contains_key(&key)
                    }
                    Value::Str(s) => s.contains(&item.to_string()),
                    _ => false,
                };
                self.stack.push(Value::Bool(found));
            }
            OpCode::NotIn => {
                let container = self.stack.pop().unwrap_or(Value::Nil);
                let item = self.stack.pop().unwrap_or(Value::Nil);
                let found = match &container {
                    Value::List(l) => l.borrow().contains(&item),
                    Value::Map(m) => {
                        let key = match &item {
                            Value::Str(s) => s.clone(),
                            other => other.to_string(),
                        };
                        m.borrow().contains_key(&key)
                    }
                    Value::Str(s) => s.contains(&item.to_string()),
                    _ => false,
                };
                self.stack.push(Value::Bool(!found));
            }
            OpCode::IsPositive => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(match a {
                    Value::Int(i) => i > 0,
                    Value::Float(f) => f > 0.0,
                    _ => false,
                }));
            }
            OpCode::IsNegative => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(match a {
                    Value::Int(i) => i < 0,
                    Value::Float(f) => f < 0.0,
                    _ => false,
                }));
            }
            OpCode::IsZero => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(match a {
                    Value::Int(i) => i == 0,
                    Value::Float(f) => f == 0.0,
                    _ => false,
                }));
            }
            OpCode::IsEven => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(match a {
                    Value::Int(i) => i % 2 == 0,
                    _ => false,
                }));
            }
            OpCode::IsOdd => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(match a {
                    Value::Int(i) => i % 2 != 0,
                    _ => false,
                }));
            }
            OpCode::IsEmpty => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(match a {
                    Value::Nil => true,
                    Value::Str(s) => s.is_empty(),
                    Value::List(l) => l.borrow().is_empty(),
                    Value::Map(m) => m.borrow().is_empty(),
                    _ => false,
                }));
            }
            OpCode::IsSomething => {
                let a = self.stack.pop().unwrap();
                self.stack.push(Value::Bool(!matches!(a, Value::Nil)));
            }
            OpCode::Jump => {
                let offset = self.read_u16();
                self.current_frame().ip = offset as usize;
            }
            OpCode::JumpIfFalse => {
                let offset = self.read_u16();
                let cond = self.stack.pop().unwrap();
                if !cond.is_truthy() {
                    self.current_frame().ip = offset as usize;
                }
            }
            OpCode::Loop => {
                let offset = self.read_u16();
                self.current_frame().ip = offset as usize;
            }
            OpCode::PushTry => {
                let catch_ip = self.read_u16() as usize;
                let frame_index = self.frames.len() - 1;
                let stack_depth = self.stack.len();
                self.try_handlers.push(TryHandler {
                    catch_ip,
                    frame_index,
                    stack_depth,
                });
            }
            OpCode::PopTry => {
                self.try_handlers.pop();
            }
            OpCode::Raise => {
                let err_val = self.stack.pop().unwrap_or_else(|| Value::Str("Error raised".to_string()));
                self.handle_error(err_val, line)?;
            }
            OpCode::Call => {
                let arg_count = self.read_byte() as usize;
                let mut args = Vec::with_capacity(arg_count);
                for _ in 0..arg_count {
                    args.push(self.stack.pop().unwrap());
                }
                args.reverse();

                let callee = self.stack.pop().unwrap();

                if let Value::NativeFunction(ref name, _) = callee {
                    if name.eq_ignore_ascii_case("filter") && args.len() >= 2 {
                        let coll = &args[0];
                        let pred = &args[1];
                        let mut filtered = Vec::new();
                        if let Value::List(items) = coll {
                            for item in items.borrow().iter() {
                                let res = self.call_value(pred, vec![item.clone()], line)?;
                                if res.is_truthy() {
                                    filtered.push(item.clone());
                                }
                            }
                        }
                        self.stack.push(Value::List(Rc::new(RefCell::new(filtered))));
                        return Ok(true);
                    } else if name.eq_ignore_ascii_case("map") && args.len() >= 2 {
                        let coll = &args[0];
                        let trans = &args[1];
                        let mut mapped = Vec::new();
                        if let Value::List(items) = coll {
                            for item in items.borrow().iter() {
                                let res = self.call_value(trans, vec![item.clone()], line)?;
                                mapped.push(res);
                            }
                        }
                        self.stack.push(Value::List(Rc::new(RefCell::new(mapped))));
                        return Ok(true);
                    } else if name.eq_ignore_ascii_case("reduce") && args.len() >= 3 {
                        let coll = &args[0];
                        let red = &args[1];
                        let init = args[2].clone();
                        let mut acc = init;
                        if let Value::List(items) = coll {
                            for item in items.borrow().iter() {
                                acc = self.call_value(red, vec![acc, item.clone()], line)?;
                            }
                        }
                        self.stack.push(acc);
                        return Ok(true);
                    }
                }

                match callee {
                    Value::Function(fn_rc) => {
                        if args.len() != fn_rc.arity {
                            return Err(self.runtime_error(
                                line,
                                format!(
                                    "Function '{}' expects {} arguments but got {}",
                                    fn_rc.name,
                                    fn_rc.arity,
                                    args.len()
                                ),
                            ));
                        }

                        let mut new_env = if let Some(ref closure_env) = fn_rc.closure_env {
                            Environment::with_enclosing(closure_env.clone())
                        } else {
                            Environment::new()
                        };

                        for (i, arg) in args.into_iter().enumerate() {
                            if i < fn_rc.params.len() {
                                new_env.define(&fn_rc.params[i], arg);
                            }
                        }

                        let slots_offset = self.stack.len();
                        self.frames.push(CallFrame {
                            function: Some(fn_rc.clone()),
                            chunk: fn_rc.chunk.clone(),
                            ip: 0,
                            slots_offset,
                            env: Rc::new(RefCell::new(new_env)),
                        });
                    }
                    Value::NativeFunction(_, native_fn) => {
                        let result = match native_fn(args) {
                            Ok(res) => res,
                            Err(e) => {
                                self.handle_error(Value::Str(e), line)?;
                                return Ok(true);
                            }
                        };
                        self.stack.push(result);
                    }
                    _ => {
                        return Err(self.runtime_error(
                            line,
                            format!("Cannot call non-callable type '{}'", callee.type_name()),
                        ));
                    }
                }
            }
            OpCode::Closure => {
                let env_clone = self.current_frame().env.clone();
                let idx = self.read_u16();
                let fn_val = self.current_frame().chunk.constants[idx as usize].clone();
                if let Value::Function(fn_rc) = fn_val {
                    let mut closure = (*fn_rc).clone();
                    closure.closure_env = Some(env_clone);
                    self.stack.push(Value::Function(Rc::new(closure)));
                } else {
                    self.stack.push(fn_val);
                }
            }
            OpCode::Return => {
                let ret_val = self.stack.pop().unwrap_or(Value::Nil);
                let frame = self.frames.pop().unwrap();

                while self.stack.len() > frame.slots_offset {
                    self.stack.pop();
                }

                self.stack.push(ret_val);

                if self.frames.is_empty() {
                    return Ok(false);
                }
            }
            OpCode::BuildList => {
                let count = self.read_u16() as usize;
                let mut elements = Vec::with_capacity(count);
                for _ in 0..count {
                    elements.push(self.stack.pop().unwrap());
                }
                elements.reverse();
                self.stack.push(Value::List(Rc::new(RefCell::new(elements))));
            }
            OpCode::BuildMap => {
                let count = self.read_u16() as usize;
                let mut entries = IndexMap::new();
                for _ in 0..count {
                    let val = self.stack.pop().unwrap();
                    let key = self.stack.pop().unwrap();
                    entries.insert(format!("{}", key), val);
                }
                self.stack.push(Value::Map(Rc::new(RefCell::new(entries))));
            }
            OpCode::IndexGet => {
                let index = self.stack.pop().unwrap();
                let target = self.stack.pop().unwrap();

                match target {
                    Value::List(l) => {
                        let idx = match index {
                            Value::Int(i) => i,
                            Value::Float(f) => f as i64,
                            _ => {
                                return Err(self.runtime_error(
                                    line,
                                    "List index must be an integer",
                                ));
                            }
                        };
                        let list = l.borrow();
                        let actual_idx = if idx < 0 {
                            (list.len() as i64 + idx) as usize
                        } else {
                            idx as usize
                        };

                        if actual_idx < list.len() {
                            self.stack.push(list[actual_idx].clone());
                        } else {
                            return Err(self.runtime_error(line, "List index out of bounds"));
                        }
                    }
                    Value::Map(m) => {
                        let key = format!("{}", index);
                        let val = m.borrow().get(&key).cloned().unwrap_or(Value::Nil);
                        self.stack.push(val);
                    }
                    _ => {
                        return Err(self.runtime_error(
                            line,
                            format!("Cannot index into type '{}'", target.type_name()),
                        ));
                    }
                }
            }
            OpCode::IndexSet => {
                let val = self.stack.pop().unwrap();
                let index = self.stack.pop().unwrap();
                let target = self.stack.pop().unwrap();

                match target {
                    Value::List(l) => {
                        let idx = match index {
                            Value::Int(i) => i,
                            _ => return Err(self.runtime_error(line, "Index must be integer")),
                        };
                        let mut list = l.borrow_mut();
                        let actual_idx = if idx < 0 {
                            (list.len() as i64 + idx) as usize
                        } else {
                            idx as usize
                        };
                        if actual_idx < list.len() {
                            list[actual_idx] = val;
                        } else {
                            return Err(self.runtime_error(line, "Index out of bounds"));
                        }
                    }
                    Value::Map(m) => {
                        let key = format!("{}", index);
                        m.borrow_mut().insert(key, val);
                    }
                    _ => {
                        return Err(self.runtime_error(line, "Cannot index-set on non-collection"));
                    }
                }
            }
            OpCode::GetProperty => {
                let prop_idx = self.read_u16();
                let prop_name =
                    format!("{}", self.current_frame().chunk.constants[prop_idx as usize]);
                let target = self.stack.pop().unwrap();

                if let Some(prop_val) = target.get_property(&prop_name) {
                    self.stack.push(prop_val);
                } else {
                    return Err(self.runtime_error(
                        line,
                        format!(
                            "Property '{}' does not exist on type '{}'",
                            prop_name,
                            target.type_name()
                        ),
                    ));
                }
            }
            OpCode::SetProperty => {
                let prop_idx = self.read_u16();
                let prop_name =
                    format!("{}", self.current_frame().chunk.constants[prop_idx as usize]);
                let val = self.stack.pop().unwrap();
                let target = self.stack.pop().unwrap();

                match target {
                    Value::Map(m) => {
                        m.borrow_mut().insert(prop_name, val);
                    }
                    _ => {
                        return Err(self.runtime_error(
                            line,
                            format!("Cannot set property on type '{}'", target.type_name()),
                        ));
                    }
                }
            }
            OpCode::Say => {
                let count = self.read_byte() as usize;
                let mut parts = Vec::with_capacity(count);
                for _ in 0..count {
                    parts.push(self.stack.pop().unwrap());
                }
                parts.reverse();

                let out_str = parts
                    .into_iter()
                    .map(|p| format!("{}", p))
                    .collect::<Vec<_>>()
                    .join(" ");

                if self.capture_output {
                    self.output.push(out_str);
                } else {
                    println!("{}", out_str);
                }
            }
            OpCode::AddToList => {
                let item = self.stack.pop().unwrap();
                let list_val = self.stack.pop().unwrap();

                if let Value::List(l) = list_val {
                    l.borrow_mut().push(item);
                } else {
                    return Err(self.runtime_error(line, "Cannot add to non-list value"));
                }
            }
            OpCode::GetModule => {
                let idx = self.read_u16();
                let name = format!("{}", self.current_frame().chunk.constants[idx as usize]);
                let module_val = self.module_loader.load(&name)?;
                self.stack.push(module_val);
            }
            OpCode::HttpRequest => {
                let timeout = self.stack.pop().unwrap_or(Value::Nil);
                let data = self.stack.pop().unwrap_or(Value::Nil);
                let headers = self.stack.pop().unwrap_or(Value::Nil);
                let url = self.stack.pop().unwrap_or(Value::Nil);
                let method = self.stack.pop().unwrap_or(Value::Nil);
                let resp = crate::stdlib::http::http_request_impl(
                    &method.to_string(),
                    &url.to_string(),
                    headers,
                    data,
                    timeout,
                );
                self.stack.push(resp);
            }
            OpCode::Serve => {
                let port_val = self.stack.pop().unwrap_or(Value::Int(8080));
                let port = match port_val {
                    Value::Int(i) => i,
                    _ => 8080,
                };
                println!(
                    "\x1b[92m●\x1b[0m \x1b[1mLyslyn HTTP Server\x1b[0m listening on \x1b[96mhttp://0.0.0.0:{}\x1b[0m",
                    port
                );
            }
            OpCode::Respond => {
                let _payload = self.stack.pop();
                let _status = self.stack.pop();
            }
            OpCode::Validate => {
                let _schema = self.stack.pop();
            }
            OpCode::Halt => {
                if let Some(_val) = self.stack.pop() {
                    return Ok(false);
                }
                return Ok(false);
            }
            _ => {}
        }

        Ok(true)
    }

    fn read_byte(&mut self) -> u8 {
        let frame = self.current_frame();
        let b = frame.chunk.code[frame.ip];
        frame.ip += 1;
        b
    }

    fn read_u16(&mut self) -> u16 {
        let frame = self.current_frame();
        let b1 = frame.chunk.code[frame.ip] as u16;
        let b2 = frame.chunk.code[frame.ip + 1] as u16;
        frame.ip += 2;
        (b1 << 8) | b2
    }

    fn current_frame(&mut self) -> &mut CallFrame {
        self.frames.last_mut().unwrap()
    }

    fn runtime_error(&self, line: usize, message: impl Into<String>) -> LyslynError {
        let chunk_name = self
            .frames
            .last()
            .map(|f| f.chunk.name.as_str())
            .unwrap_or("<main>");
        LyslynError::new(ErrorKind::Runtime, message, Span::new(line, 1, 1), chunk_name)
    }
}
