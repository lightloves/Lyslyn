use crate::bytecode::chunk::Chunk;
use indexmap::IndexMap;
use std::cell::RefCell;
use std::fmt;
use std::rc::Rc;

pub type NativeFn = dyn Fn(Vec<Value>) -> Result<Value, String>;

#[derive(Clone)]
pub struct Environment {
    pub values: IndexMap<String, Value>,
    pub enclosing: Option<Rc<RefCell<Environment>>>,
}

impl Environment {
    pub fn new() -> Self {
        Environment {
            values: IndexMap::new(),
            enclosing: None,
        }
    }

    pub fn with_enclosing(enclosing: Rc<RefCell<Environment>>) -> Self {
        Environment {
            values: IndexMap::new(),
            enclosing: Some(enclosing),
        }
    }

    pub fn get(&self, name: &str) -> Option<Value> {
        if let Some(val) = self.values.get(name) {
            return Some(val.clone());
        }
        if let Some(ref enc) = self.enclosing {
            return enc.borrow().get(name);
        }
        None
    }

    pub fn set(&mut self, name: &str, val: Value) -> bool {
        if self.values.contains_key(name) {
            self.values.insert(name.to_string(), val);
            return true;
        }
        if let Some(ref enc) = self.enclosing {
            return enc.borrow_mut().set(name, val);
        }
        false
    }

    pub fn define(&mut self, name: &str, val: Value) {
        self.values.insert(name.to_string(), val);
    }
}

#[derive(Clone)]
pub struct LyslynFunction {
    pub name: String,
    pub params: Vec<String>,
    pub arity: usize,
    pub chunk: Chunk,
    pub closure_env: Option<Rc<RefCell<Environment>>>,
}

#[derive(Clone)]
pub struct LyslynModule {
    pub name: String,
    pub exports: Rc<RefCell<IndexMap<String, Value>>>,
}

#[derive(Clone)]
pub enum Value {
    Nil,
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
    List(Rc<RefCell<Vec<Value>>>),
    Map(Rc<RefCell<IndexMap<String, Value>>>),
    Function(Rc<LyslynFunction>),
    NativeFunction(String, Rc<NativeFn>),
    Module(Rc<LyslynModule>),
}

impl Value {
    pub fn is_truthy(&self) -> bool {
        match self {
            Value::Nil => false,
            Value::Bool(b) => *b,
            Value::Int(i) => *i != 0,
            Value::Float(f) => *f != 0.0,
            Value::Str(s) => !s.is_empty(),
            Value::List(l) => !l.borrow().is_empty(),
            Value::Map(m) => !m.borrow().is_empty(),
            _ => true,
        }
    }

    pub fn type_name(&self) -> &'static str {
        match self {
            Value::Nil => "nil",
            Value::Bool(_) => "bool",
            Value::Int(_) => "int",
            Value::Float(_) => "float",
            Value::Str(_) => "string",
            Value::List(_) => "list",
            Value::Map(_) => "object",
            Value::Function(_) => "function",
            Value::NativeFunction(_, _) => "native_function",
            Value::Module(_) => "module",
        }
    }

    pub fn is_empty(&self) -> bool {
        match self {
            Value::Nil => true,
            Value::Str(s) => s.is_empty(),
            Value::List(l) => l.borrow().is_empty(),
            Value::Map(m) => m.borrow().is_empty(),
            _ => false,
        }
    }

    pub fn is_positive(&self) -> bool {
        match self {
            Value::Int(i) => *i > 0,
            Value::Float(f) => *f > 0.0,
            _ => false,
        }
    }

    pub fn is_negative(&self) -> bool {
        match self {
            Value::Int(i) => *i < 0,
            Value::Float(f) => *f < 0.0,
            _ => false,
        }
    }

    pub fn is_zero(&self) -> bool {
        match self {
            Value::Int(i) => *i == 0,
            Value::Float(f) => *f == 0.0,
            _ => false,
        }
    }

    pub fn is_even(&self) -> bool {
        match self {
            Value::Int(i) => i % 2 == 0,
            _ => false,
        }
    }

    pub fn is_odd(&self) -> bool {
        match self {
            Value::Int(i) => i % 2 != 0,
            _ => false,
        }
    }

    pub fn add(&self, other: &Value) -> Result<Value, String> {
        match (self, other) {
            (Value::Int(a), Value::Int(b)) => Ok(Value::Int(a + b)),
            (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a + b)),
            (Value::Int(a), Value::Float(b)) => Ok(Value::Float(*a as f64 + b)),
            (Value::Float(a), Value::Int(b)) => Ok(Value::Float(a + *b as f64)),
            (Value::Str(a), b) => Ok(Value::Str(format!("{}{}", a, b))),
            (a, Value::Str(b)) => Ok(Value::Str(format!("{}{}", a, b))),
            (Value::List(a), Value::List(b)) => {
                let mut combined = a.borrow().clone();
                combined.extend(b.borrow().clone());
                Ok(Value::List(Rc::new(RefCell::new(combined))))
            }
            _ => Err(format!(
                "Cannot add types '{}' and '{}'",
                self.type_name(),
                other.type_name()
            )),
        }
    }

    pub fn sub(&self, other: &Value) -> Result<Value, String> {
        match (self, other) {
            (Value::Int(a), Value::Int(b)) => Ok(Value::Int(a - b)),
            (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a - b)),
            (Value::Int(a), Value::Float(b)) => Ok(Value::Float(*a as f64 - b)),
            (Value::Float(a), Value::Int(b)) => Ok(Value::Float(a - *b as f64)),
            _ => Err(format!(
                "Cannot subtract types '{}' and '{}'",
                self.type_name(),
                other.type_name()
            )),
        }
    }

    pub fn mul(&self, other: &Value) -> Result<Value, String> {
        match (self, other) {
            (Value::Int(a), Value::Int(b)) => Ok(Value::Int(a * b)),
            (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a * b)),
            (Value::Int(a), Value::Float(b)) => Ok(Value::Float(*a as f64 * b)),
            (Value::Float(a), Value::Int(b)) => Ok(Value::Float(a * *b as f64)),
            (Value::Str(s), Value::Int(n)) | (Value::Int(n), Value::Str(s)) => {
                if *n <= 0 {
                    Ok(Value::Str(String::new()))
                } else {
                    Ok(Value::Str(s.repeat(*n as usize)))
                }
            }
            _ => Err(format!(
                "Cannot multiply types '{}' and '{}'",
                self.type_name(),
                other.type_name()
            )),
        }
    }

    pub fn div(&self, other: &Value) -> Result<Value, String> {
        match (self, other) {
            (Value::Int(a), Value::Int(b)) => {
                if *b == 0 {
                    return Err("Division by zero".to_string());
                }
                if a % b == 0 {
                    Ok(Value::Int(a / b))
                } else {
                    Ok(Value::Float(*a as f64 / *b as f64))
                }
            }
            (Value::Float(a), Value::Float(b)) => {
                if *b == 0.0 {
                    return Err("Division by zero".to_string());
                }
                Ok(Value::Float(a / b))
            }
            (Value::Int(a), Value::Float(b)) => {
                if *b == 0.0 {
                    return Err("Division by zero".to_string());
                }
                Ok(Value::Float(*a as f64 / b))
            }
            (Value::Float(a), Value::Int(b)) => {
                if *b == 0 {
                    return Err("Division by zero".to_string());
                }
                Ok(Value::Float(a / *b as f64))
            }
            _ => Err(format!(
                "Cannot divide types '{}' and '{}'",
                self.type_name(),
                other.type_name()
            )),
        }
    }

    pub fn rem(&self, other: &Value) -> Result<Value, String> {
        match (self, other) {
            (Value::Int(a), Value::Int(b)) => {
                if *b == 0 {
                    return Err("Modulo by zero".to_string());
                }
                Ok(Value::Int(a % b))
            }
            _ => Err(format!(
                "Cannot compute modulo of types '{}' and '{}'",
                self.type_name(),
                other.type_name()
            )),
        }
    }

    pub fn neg(&self) -> Result<Value, String> {
        match self {
            Value::Int(i) => Ok(Value::Int(-i)),
            Value::Float(f) => Ok(Value::Float(-f)),
            _ => Err(format!("Cannot negate type '{}'", self.type_name())),
        }
    }

    pub fn get_property(&self, prop: &str) -> Option<Value> {
        match self {
            Value::Str(s) => match prop {
                "length" => Some(Value::Int(s.chars().count() as i64)),
                _ => None,
            },
            Value::List(l) => match prop {
                "length" => Some(Value::Int(l.borrow().len() as i64)),
                "append" => {
                    let l_clone = l.clone();
                    Some(Value::NativeFunction(
                        "append".to_string(),
                        Rc::new(move |args| {
                            if let Some(item) = args.first() {
                                l_clone.borrow_mut().push(item.clone());
                                Ok(Value::Nil)
                            } else {
                                Err("Expected 1 argument to list.append".to_string())
                            }
                        }),
                    ))
                }
                "pop" => {
                    let l_clone = l.clone();
                    Some(Value::NativeFunction(
                        "pop".to_string(),
                        Rc::new(move |_| {
                            let popped = l_clone.borrow_mut().pop().unwrap_or(Value::Nil);
                            Ok(popped)
                        }),
                    ))
                }
                _ => None,
            },
            Value::Map(m) => {
                if let Some(val) = m.borrow().get(prop) {
                    return Some(val.clone());
                }
                match prop {
                    "keys" => {
                        let m_clone = m.clone();
                        Some(Value::NativeFunction(
                            "keys".to_string(),
                            Rc::new(move |_| {
                                let keys_list: Vec<Value> = m_clone
                                    .borrow()
                                    .keys()
                                    .map(|k| Value::Str(k.clone()))
                                    .collect();
                                Ok(Value::List(Rc::new(RefCell::new(keys_list))))
                            }),
                        ))
                    }
                    "values" => {
                        let m_clone = m.clone();
                        Some(Value::NativeFunction(
                            "values".to_string(),
                            Rc::new(move |_| {
                                let vals_list: Vec<Value> = m_clone
                                    .borrow()
                                    .values()
                                    .cloned()
                                    .collect();
                                Ok(Value::List(Rc::new(RefCell::new(vals_list))))
                            }),
                        ))
                    }
                    _ => None,
                }
            }
            Value::Module(m) => m.exports.borrow().get(prop).cloned(),
            _ => None,
        }
    }

    pub fn set_property(&self, prop: &str, val: Value) -> Result<(), String> {
        match self {
            Value::Map(m) => {
                m.borrow_mut().insert(prop.to_string(), val);
                Ok(())
            }
            Value::Module(m) => {
                m.exports.borrow_mut().insert(prop.to_string(), val);
                Ok(())
            }
            _ => Err(format!("Cannot set property on type '{}'", self.type_name())),
        }
    }

    pub fn get_index(&self, index: &Value) -> Result<Value, String> {
        match (self, index) {
            (Value::List(l), Value::Int(i)) => {
                let borrowed = l.borrow();
                let len = borrowed.len() as i64;
                let actual_idx = if *i < 0 { len + *i } else { *i };
                if actual_idx < 0 || actual_idx >= len {
                    Err(format!("Index {} out of bounds for list of length {}", i, len))
                } else {
                    Ok(borrowed[actual_idx as usize].clone())
                }
            }
            (Value::Str(s), Value::Int(i)) => {
                let chars: Vec<char> = s.chars().collect();
                let len = chars.len() as i64;
                let actual_idx = if *i < 0 { len + *i } else { *i };
                if actual_idx < 0 || actual_idx >= len {
                    Err(format!("Index {} out of bounds for string of length {}", i, len))
                } else {
                    Ok(Value::Str(chars[actual_idx as usize].to_string()))
                }
            }
            (Value::Map(m), key) => {
                let key_str = format!("{}", key);
                Ok(m.borrow().get(&key_str).cloned().unwrap_or(Value::Nil))
            }
            _ => Err(format!(
                "Cannot index '{}' with '{}'",
                self.type_name(),
                index.type_name()
            )),
        }
    }

    pub fn set_index(&self, index: &Value, val: Value) -> Result<(), String> {
        match (self, index) {
            (Value::List(l), Value::Int(i)) => {
                let mut borrowed = l.borrow_mut();
                let len = borrowed.len() as i64;
                let actual_idx = if *i < 0 { len + *i } else { *i };
                if actual_idx < 0 || actual_idx >= len {
                    Err(format!("Index {} out of bounds for list of length {}", i, len))
                } else {
                    borrowed[actual_idx as usize] = val;
                    Ok(())
                }
            }
            (Value::Map(m), key) => {
                let key_str = format!("{}", key);
                m.borrow_mut().insert(key_str, val);
                Ok(())
            }
            _ => Err(format!(
                "Cannot set index on '{}' with '{}'",
                self.type_name(),
                index.type_name()
            )),
        }
    }
}

impl PartialEq for Value {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Value::Nil, Value::Nil) => true,
            (Value::Bool(a), Value::Bool(b)) => a == b,
            (Value::Int(a), Value::Int(b)) => a == b,
            (Value::Float(a), Value::Float(b)) => (a - b).abs() < f64::EPSILON,
            (Value::Int(a), Value::Float(b)) => (*a as f64 - b).abs() < f64::EPSILON,
            (Value::Float(a), Value::Int(b)) => (a - *b as f64).abs() < f64::EPSILON,
            (Value::Str(a), Value::Str(b)) => a == b,
            (Value::List(a), Value::List(b)) => *a.borrow() == *b.borrow(),
            (Value::Map(a), Value::Map(b)) => *a.borrow() == *b.borrow(),
            _ => false,
        }
    }
}

impl PartialOrd for Value {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        match (self, other) {
            (Value::Int(a), Value::Int(b)) => a.partial_cmp(b),
            (Value::Float(a), Value::Float(b)) => a.partial_cmp(b),
            (Value::Int(a), Value::Float(b)) => (*a as f64).partial_cmp(b),
            (Value::Float(a), Value::Int(b)) => a.partial_cmp(&(*b as f64)),
            (Value::Str(a), Value::Str(b)) => a.partial_cmp(b),
            _ => None,
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Value::Nil => write!(f, "nothing"),
            Value::Bool(b) => write!(f, "{}", if *b { "true" } else { "false" }),
            Value::Int(i) => write!(f, "{}", i),
            Value::Float(fl) => write!(f, "{}", fl),
            Value::Str(s) => write!(f, "{}", s),
            Value::List(l) => {
                write!(f, "[")?;
                let borrowed = l.borrow();
                for (i, item) in borrowed.iter().enumerate() {
                    if i > 0 {
                        write!(f, ", ")?;
                    }
                    write!(f, "{}", item)?;
                }
                write!(f, "]")
            }
            Value::Map(m) => {
                write!(f, "{{")?;
                let borrowed = m.borrow();
                for (i, (k, v)) in borrowed.iter().enumerate() {
                    if i > 0 {
                        write!(f, ", ")?;
                    }
                    write!(f, "{}: {}", k, v)?;
                }
                write!(f, "}}")
            }
            Value::Function(func) => write!(f, "<function {}>", func.name),
            Value::NativeFunction(name, _) => write!(f, "<native function {}>", name),
            Value::Module(m) => write!(f, "<module '{}'>", m.name),
        }
    }
}

impl fmt::Debug for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Value::Str(s) => write!(f, "{:?}", s),
            _ => write!(f, "{}", self),
        }
    }
}
