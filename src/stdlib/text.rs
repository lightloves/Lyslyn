use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;

pub fn create_text_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "trim".to_string(),
        Value::NativeFunction(
            "trim".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    Ok(Value::Str(arg.to_string().trim().to_string()))
                } else {
                    Err("Expected 1 argument to text.trim".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "uppercase".to_string(),
        Value::NativeFunction(
            "uppercase".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    Ok(Value::Str(arg.to_string().to_uppercase()))
                } else {
                    Err("Expected 1 argument to text.uppercase".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "lowercase".to_string(),
        Value::NativeFunction(
            "lowercase".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    Ok(Value::Str(arg.to_string().to_lowercase()))
                } else {
                    Err("Expected 1 argument to text.lowercase".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "split".to_string(),
        Value::NativeFunction(
            "split".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let s = arg.to_string();
                    let sep = if args.len() > 1 {
                        args[1].to_string()
                    } else {
                        " ".to_string()
                    };
                    let parts: Vec<Value> = if sep.is_empty() {
                        s.chars().map(|c| Value::Str(c.to_string())).collect()
                    } else {
                        s.split(&sep).map(|p| Value::Str(p.to_string())).collect()
                    };
                    Ok(Value::List(Rc::new(RefCell::new(parts))))
                } else {
                    Err("Expected at least 1 argument to text.split".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "join".to_string(),
        Value::NativeFunction(
            "join".to_string(),
            Rc::new(|args| {
                if let Some(Value::List(items)) = args.first() {
                    let sep = if args.len() > 1 {
                        args[1].to_string()
                    } else {
                        String::new()
                    };
                    let str_items: Vec<String> = items.borrow().iter().map(|v| v.to_string()).collect();
                    Ok(Value::Str(str_items.join(&sep)))
                } else {
                    Err("Expected list as first argument to text.join".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "replace".to_string(),
        Value::NativeFunction(
            "replace".to_string(),
            Rc::new(|args| {
                if args.len() >= 3 {
                    let s = args[0].to_string();
                    let old = args[1].to_string();
                    let new = args[2].to_string();
                    Ok(Value::Str(s.replace(&old, &new)))
                } else {
                    Err("Expected 3 arguments to text.replace(str, old, new)".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "starts_with".to_string(),
        Value::NativeFunction(
            "starts_with".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let s = args[0].to_string();
                    let prefix = args[1].to_string();
                    Ok(Value::Bool(s.starts_with(&prefix)))
                } else {
                    Err("Expected 2 arguments to text.starts_with".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "ends_with".to_string(),
        Value::NativeFunction(
            "ends_with".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let s = args[0].to_string();
                    let suffix = args[1].to_string();
                    Ok(Value::Bool(s.ends_with(&suffix)))
                } else {
                    Err("Expected 2 arguments to text.ends_with".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "contains".to_string(),
        Value::NativeFunction(
            "contains".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let s = args[0].to_string();
                    let sub = args[1].to_string();
                    Ok(Value::Bool(s.contains(&sub)))
                } else {
                    Err("Expected 2 arguments to text.contains".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "length".to_string(),
        Value::NativeFunction(
            "length".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    match arg {
                        Value::Str(s) => Ok(Value::Int(s.chars().count() as i64)),
                        Value::List(l) => Ok(Value::Int(l.borrow().len() as i64)),
                        Value::Map(m) => Ok(Value::Int(m.borrow().len() as i64)),
                        _ => Ok(Value::Int(arg.to_string().chars().count() as i64)),
                    }
                } else {
                    Err("Expected 1 argument to text.length".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "text".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
