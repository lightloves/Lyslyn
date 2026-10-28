use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;
use std::time::{SystemTime, UNIX_EPOCH};

struct CacheEntry {
    value: Value,
    expire_at: Option<f64>,
}

thread_local! {
    static GLOBAL_CACHE: RefCell<IndexMap<String, CacheEntry>> = RefCell::new(IndexMap::new());
}

fn with_cache<R>(f: impl FnOnce(&mut IndexMap<String, CacheEntry>) -> R) -> R {
    GLOBAL_CACHE.with(|cell| {
        let mut map = cell.borrow_mut();
        f(&mut map)
    })
}

fn current_time() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
}

fn evict_expired(map: &mut IndexMap<String, CacheEntry>) {
    let now = current_time();
    map.retain(|_, entry| match entry.expire_at {
        Some(exp) => now <= exp,
        None => true,
    });
}

pub fn create_cache_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "set".to_string(),
        Value::NativeFunction(
            "set".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let key = args[0].to_string();
                    let val = args[1].clone();
                    let ttl_sec = if args.len() > 2 {
                        match &args[2] {
                            Value::Int(i) => Some(*i as f64),
                            Value::Float(f) => Some(*f),
                            _ => None,
                        }
                    } else {
                        None
                    };

                    let expire_at = ttl_sec.map(|t| current_time() + t);
                    with_cache(|map| {
                        map.insert(
                            key,
                            CacheEntry {
                                value: val.clone(),
                                expire_at,
                            },
                        );
                    });
                    Ok(val)
                } else {
                    Err("Expected at least 2 arguments to cache.set(key, value)".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "get".to_string(),
        Value::NativeFunction(
            "get".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let key = arg.to_string();
                    let default = if args.len() > 1 {
                        args[1].clone()
                    } else {
                        Value::Nil
                    };

                    let now = current_time();
                    with_cache(|map| {
                        if let Some(entry) = map.get(&key) {
                            if let Some(exp) = entry.expire_at {
                                if now > exp {
                                    map.shift_remove(&key);
                                    return Ok(default);
                                }
                            }
                            Ok(entry.value.clone())
                        } else {
                            Ok(default)
                        }
                    })
                } else {
                    Err("Expected key argument to cache.get".to_string())
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
                    let now = current_time();
                    with_cache(|map| {
                        if let Some(entry) = map.get(&key) {
                            if let Some(exp) = entry.expire_at {
                                if now > exp {
                                    map.shift_remove(&key);
                                    return Ok(Value::Bool(false));
                                }
                            }
                            Ok(Value::Bool(true))
                        } else {
                            Ok(Value::Bool(false))
                        }
                    })
                } else {
                    Err("Expected key argument to cache.has".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "delete".to_string(),
        Value::NativeFunction(
            "delete".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let key = arg.to_string();
                    let removed = with_cache(|map| map.shift_remove(&key).is_some());
                    Ok(Value::Bool(removed))
                } else {
                    Err("Expected key argument to cache.delete".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "clear".to_string(),
        Value::NativeFunction(
            "clear".to_string(),
            Rc::new(|_| {
                with_cache(|map| map.clear());
                Ok(Value::Nil)
            }),
        ),
    );

    exports.insert(
        "size".to_string(),
        Value::NativeFunction(
            "size".to_string(),
            Rc::new(|_| {
                let s = with_cache(|map| {
                    evict_expired(map);
                    map.len()
                });
                Ok(Value::Int(s as i64))
            }),
        ),
    );

    exports.insert(
        "keys".to_string(),
        Value::NativeFunction(
            "keys".to_string(),
            Rc::new(|_| {
                let keys_list = with_cache(|map| {
                    evict_expired(map);
                    map.keys().map(|k| Value::Str(k.clone())).collect()
                });
                Ok(Value::List(Rc::new(RefCell::new(keys_list))))
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "cache".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
