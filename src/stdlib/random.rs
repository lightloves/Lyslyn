use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;
use std::time::{SystemTime, UNIX_EPOCH};

fn next_random_u64() -> u64 {
    thread_local! {
        static STATE: RefCell<u64> = RefCell::new({
            let nanos = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_nanos() as u64;
            nanos ^ 0xdeadbeefcafe
        });
    }
    STATE.with(|s| {
        let mut x = *s.borrow();
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        *s.borrow_mut() = x;
        x
    })
}

pub fn create_random_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "random".to_string(),
        Value::NativeFunction(
            "random".to_string(),
            Rc::new(|_| {
                let r = (next_random_u64() % 1_000_000) as f64 / 1_000_000.0;
                Ok(Value::Float(r))
            }),
        ),
    );

    exports.insert(
        "integer".to_string(),
        Value::NativeFunction(
            "integer".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let min = match &args[0] {
                        Value::Int(i) => *i,
                        Value::Float(f) => *f as i64,
                        _ => 0,
                    };
                    let max = match &args[1] {
                        Value::Int(i) => *i,
                        Value::Float(f) => *f as i64,
                        _ => 100,
                    };
                    if min >= max {
                        Ok(Value::Int(min))
                    } else {
                        let range = (max - min + 1) as u64;
                        let offset = (next_random_u64() % range) as i64;
                        Ok(Value::Int(min + offset))
                    }
                } else {
                    Err("Expected 2 arguments to random.integer(min, max)".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "choice".to_string(),
        Value::NativeFunction(
            "choice".to_string(),
            Rc::new(|args| {
                if let Some(Value::List(items)) = args.first() {
                    let borrowed = items.borrow();
                    if borrowed.is_empty() {
                        Ok(Value::Nil)
                    } else {
                        let idx = (next_random_u64() as usize) % borrowed.len();
                        Ok(borrowed[idx].clone())
                    }
                } else {
                    Err("Expected list argument to random.choice".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "shuffle".to_string(),
        Value::NativeFunction(
            "shuffle".to_string(),
            Rc::new(|args| {
                if let Some(Value::List(items)) = args.first() {
                    let mut list = items.borrow().clone();
                    for i in (1..list.len()).rev() {
                        let j = (next_random_u64() as usize) % (i + 1);
                        list.swap(i, j);
                    }
                    Ok(Value::List(Rc::new(RefCell::new(list))))
                } else {
                    Err("Expected list argument to random.shuffle".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "random".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
