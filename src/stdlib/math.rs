use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;

pub fn create_math_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert("pi".to_string(), Value::Float(std::f64::consts::PI));
    exports.insert("e".to_string(), Value::Float(std::f64::consts::E));

    exports.insert(
        "sqrt".to_string(),
        Value::NativeFunction(
            "sqrt".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let num = match arg {
                        Value::Int(i) => *i as f64,
                        Value::Float(f) => *f,
                        _ => return Err("Expected number argument to sqrt".to_string()),
                    };
                    if num < 0.0 {
                        return Err("Cannot take square root of negative number".to_string());
                    }
                    Ok(Value::Float(num.sqrt()))
                } else {
                    Err("Expected 1 argument to sqrt".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "floor".to_string(),
        Value::NativeFunction(
            "floor".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let num = match arg {
                        Value::Int(i) => *i as f64,
                        Value::Float(f) => *f,
                        _ => return Err("Expected number argument to floor".to_string()),
                    };
                    Ok(Value::Int(num.floor() as i64))
                } else {
                    Err("Expected 1 argument to floor".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "ceil".to_string(),
        Value::NativeFunction(
            "ceil".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let num = match arg {
                        Value::Int(i) => *i as f64,
                        Value::Float(f) => *f,
                        _ => return Err("Expected number argument to ceil".to_string()),
                    };
                    Ok(Value::Int(num.ceil() as i64))
                } else {
                    Err("Expected 1 argument to ceil".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "round".to_string(),
        Value::NativeFunction(
            "round".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let num = match arg {
                        Value::Int(i) => *i as f64,
                        Value::Float(f) => *f,
                        _ => return Err("Expected number argument to round".to_string()),
                    };
                    if args.len() > 1 {
                        if let Value::Int(decimals) = args[1] {
                            let factor = 10f64.powi(decimals as i32);
                            return Ok(Value::Float((num * factor).round() / factor));
                        }
                    }
                    Ok(Value::Int(num.round() as i64))
                } else {
                    Err("Expected 1 or 2 arguments to round".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "abs".to_string(),
        Value::NativeFunction(
            "abs".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    match arg {
                        Value::Int(i) => Ok(Value::Int(i.abs())),
                        Value::Float(f) => Ok(Value::Float(f.abs())),
                        _ => Err("Expected number argument to abs".to_string()),
                    }
                } else {
                    Err("Expected 1 argument to abs".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "min".to_string(),
        Value::NativeFunction(
            "min".to_string(),
            Rc::new(|args| {
                if args.len() < 2 {
                    return Err("Expected at least 2 arguments to min".to_string());
                }
                let mut min_val = args[0].clone();
                for a in &args[1..] {
                    if a < &min_val {
                        min_val = a.clone();
                    }
                }
                Ok(min_val)
            }),
        ),
    );

    exports.insert(
        "max".to_string(),
        Value::NativeFunction(
            "max".to_string(),
            Rc::new(|args| {
                if args.len() < 2 {
                    return Err("Expected at least 2 arguments to max".to_string());
                }
                let mut max_val = args[0].clone();
                for a in &args[1..] {
                    if a > &max_val {
                        max_val = a.clone();
                    }
                }
                Ok(max_val)
            }),
        ),
    );

    exports.insert(
        "pow".to_string(),
        Value::NativeFunction(
            "pow".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let base = match args[0] {
                        Value::Int(i) => i as f64,
                        Value::Float(f) => f,
                        _ => return Err("Expected number base".to_string()),
                    };
                    let exp = match args[1] {
                        Value::Int(i) => i as f64,
                        Value::Float(f) => f,
                        _ => return Err("Expected number exponent".to_string()),
                    };
                    Ok(Value::Float(base.powf(exp)))
                } else {
                    Err("Expected 2 arguments to pow".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "math".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
