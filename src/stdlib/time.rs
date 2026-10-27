use crate::values::{LyslynModule, Value};
use chrono::Utc;
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub fn create_time_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "now".to_string(),
        Value::NativeFunction(
            "now".to_string(),
            Rc::new(|_| {
                let start = SystemTime::now();
                let since = start
                    .duration_since(UNIX_EPOCH)
                    .unwrap_or(Duration::ZERO)
                    .as_secs_f64();
                Ok(Value::Float(since))
            }),
        ),
    );

    exports.insert(
        "timestamp".to_string(),
        Value::NativeFunction(
            "timestamp".to_string(),
            Rc::new(|_| {
                let start = SystemTime::now();
                let since = start
                    .duration_since(UNIX_EPOCH)
                    .unwrap_or(Duration::ZERO)
                    .as_millis() as i64;
                Ok(Value::Int(since))
            }),
        ),
    );

    exports.insert(
        "iso".to_string(),
        Value::NativeFunction(
            "iso".to_string(),
            Rc::new(|_| Ok(Value::Str(Utc::now().to_rfc3339()))),
        ),
    );

    exports.insert(
        "sleep".to_string(),
        Value::NativeFunction(
            "sleep".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let secs = match arg {
                        Value::Int(i) => *i as f64,
                        Value::Float(f) => *f,
                        _ => return Err("Expected number of seconds to sleep".to_string()),
                    };
                    if secs > 0.0 {
                        thread::sleep(Duration::from_secs_f64(secs));
                    }
                    Ok(Value::Nil)
                } else {
                    Err("Expected 1 argument to time.sleep".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "time".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
