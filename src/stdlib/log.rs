use crate::values::{LyslynModule, Value};
use chrono::Utc;
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;
use std::sync::atomic::{AtomicI32, Ordering};

static LOG_LEVEL: AtomicI32 = AtomicI32::new(20);

fn emit_log(level_name: &str, color_code: &str, level_num: i32, args: &[Value]) {
    if level_num < LOG_LEVEL.load(Ordering::Relaxed) {
        return;
    }
    let now = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();

    let mut context_str = String::new();
    let mut messages: Vec<String> = Vec::new();

    for (i, arg) in args.iter().enumerate() {
        if i == args.len() - 1 && matches!(arg, Value::Map(_)) && args.len() > 1 {
            context_str = format!(" {}", arg);
        } else {
            messages.push(arg.to_string());
        }
    }

    let msg = messages.join(" ");
    println!(
        "\x1b[90m{}\x1b[0m {}[{}]\x1b[0m {}{}",
        now,
        color_code,
        level_name.to_uppercase(),
        msg,
        context_str
    );
}

pub fn create_log_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "info".to_string(),
        Value::NativeFunction(
            "info".to_string(),
            Rc::new(|args| {
                emit_log("info", "\x1b[94m", 20, &args);
                Ok(Value::Nil)
            }),
        ),
    );

    exports.insert(
        "warn".to_string(),
        Value::NativeFunction(
            "warn".to_string(),
            Rc::new(|args| {
                emit_log("warn", "\x1b[93m", 30, &args);
                Ok(Value::Nil)
            }),
        ),
    );

    exports.insert(
        "error".to_string(),
        Value::NativeFunction(
            "error".to_string(),
            Rc::new(|args| {
                emit_log("error", "\x1b[91m", 40, &args);
                Ok(Value::Nil)
            }),
        ),
    );

    exports.insert(
        "debug".to_string(),
        Value::NativeFunction(
            "debug".to_string(),
            Rc::new(|args| {
                emit_log("debug", "\x1b[90m", 10, &args);
                Ok(Value::Nil)
            }),
        ),
    );

    exports.insert(
        "set_level".to_string(),
        Value::NativeFunction(
            "set_level".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let lvl = arg.to_string().to_lowercase();
                    let num = match lvl.as_str() {
                        "debug" => 10,
                        "info" => 20,
                        "warn" | "warning" => 30,
                        "error" => 40,
                        _ => 20,
                    };
                    LOG_LEVEL.store(num, Ordering::Relaxed);
                }
                Ok(Value::Nil)
            }),
        ),
    );

    exports.insert(
        "set_format".to_string(),
        Value::NativeFunction(
            "set_format".to_string(),
            Rc::new(|_| Ok(Value::Nil)),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "log".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
