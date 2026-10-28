use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::env;
use std::rc::Rc;

pub fn create_env_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "get".to_string(),
        Value::NativeFunction(
            "get".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let key = arg.to_string();
                    match env::var(&key) {
                        Ok(val) => Ok(Value::Str(val)),
                        Err(_) => {
                            if args.len() > 1 {
                                Ok(args[1].clone())
                            } else {
                                Ok(Value::Nil)
                            }
                        }
                    }
                } else {
                    Err("Expected string key to env.get".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "get_int".to_string(),
        Value::NativeFunction(
            "get_int".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let key = arg.to_string();
                    let default = if args.len() > 1 {
                        match &args[1] {
                            Value::Int(i) => *i,
                            Value::Float(f) => *f as i64,
                            _ => 0,
                        }
                    } else {
                        0
                    };
                    match env::var(&key) {
                        Ok(val) => {
                            let parsed = val.parse::<i64>().unwrap_or(default);
                            Ok(Value::Int(parsed))
                        }
                        Err(_) => Ok(Value::Int(default)),
                    }
                } else {
                    Err("Expected string key to env.get_int".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "get_bool".to_string(),
        Value::NativeFunction(
            "get_bool".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let key = arg.to_string();
                    let default = if args.len() > 1 {
                        args[1].is_truthy()
                    } else {
                        false
                    };
                    match env::var(&key) {
                        Ok(val) => {
                            let v_lower = val.to_lowercase();
                            let is_true =
                                matches!(v_lower.as_str(), "true" | "1" | "yes" | "on" | "t");
                            Ok(Value::Bool(is_true))
                        }
                        Err(_) => Ok(Value::Bool(default)),
                    }
                } else {
                    Err("Expected string key to env.get_bool".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "require".to_string(),
        Value::NativeFunction(
            "require".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let key = arg.to_string();
                    match env::var(&key) {
                        Ok(val) if !val.is_empty() => Ok(Value::Str(val)),
                        _ => Err(format!("Missing required environment variable '{}'", key)),
                    }
                } else {
                    Err("Expected string key to env.require".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "has".to_string(),
        Value::NativeFunction(
            "has".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let key = arg.to_string();
                    Ok(Value::Bool(env::var(&key).is_ok()))
                } else {
                    Err("Expected string key to env.has".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "set".to_string(),
        Value::NativeFunction(
            "set".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let k = args[0].to_string();
                    let v = args[1].to_string();
                    env::set_var(&k, &v);
                    Ok(Value::Nil)
                } else {
                    Err("Expected 2 arguments to env.set(key, value)".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "all".to_string(),
        Value::NativeFunction(
            "all".to_string(),
            Rc::new(|_| {
                let mut map = IndexMap::new();
                for (k, v) in env::vars() {
                    map.insert(k, Value::Str(v));
                }
                Ok(Value::Map(Rc::new(RefCell::new(map))))
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "env".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
