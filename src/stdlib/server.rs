use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;

pub fn create_server_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "cors".to_string(),
        Value::NativeFunction(
            "cors".to_string(),
            Rc::new(|args| {
                let origin = args
                    .first()
                    .map(|a| a.to_string())
                    .unwrap_or_else(|| "*".to_string());
                let mut mid = IndexMap::new();
                mid.insert("type".to_string(), Value::Str("cors".to_string()));
                mid.insert("origin".to_string(), Value::Str(origin));
                Ok(Value::Map(Rc::new(RefCell::new(mid))))
            }),
        ),
    );

    exports.insert(
        "logger".to_string(),
        Value::NativeFunction(
            "logger".to_string(),
            Rc::new(|_| {
                let mut mid = IndexMap::new();
                mid.insert("type".to_string(), Value::Str("logger".to_string()));
                Ok(Value::Map(Rc::new(RefCell::new(mid))))
            }),
        ),
    );

    exports.insert(
        "rate_limit".to_string(),
        Value::NativeFunction(
            "rate_limit".to_string(),
            Rc::new(|args| {
                let limit = args.first().cloned().unwrap_or(Value::Int(100));
                let window = args.get(1).cloned().unwrap_or(Value::Int(60));
                let mut mid = IndexMap::new();
                mid.insert("type".to_string(), Value::Str("rate_limit".to_string()));
                mid.insert("limit".to_string(), limit);
                mid.insert("window".to_string(), window);
                Ok(Value::Map(Rc::new(RefCell::new(mid))))
            }),
        ),
    );

    exports.insert(
        "jwt_auth".to_string(),
        Value::NativeFunction(
            "jwt_auth".to_string(),
            Rc::new(|args| {
                let secret = args.first().map(|a| a.to_string()).unwrap_or_default();
                let whitelist = args
                    .get(1)
                    .cloned()
                    .unwrap_or(Value::List(Rc::new(RefCell::new(Vec::new()))));
                let mut mid = IndexMap::new();
                mid.insert("type".to_string(), Value::Str("jwt_auth".to_string()));
                mid.insert("secret".to_string(), Value::Str(secret));
                mid.insert("whitelist".to_string(), whitelist);
                Ok(Value::Map(Rc::new(RefCell::new(mid))))
            }),
        ),
    );

    exports.insert(
        "create".to_string(),
        Value::NativeFunction(
            "create".to_string(),
            Rc::new(|_| {
                let mut server_obj = IndexMap::new();
                server_obj.insert("status".to_string(), Value::Str("ready".to_string()));
                Ok(Value::Map(Rc::new(RefCell::new(server_obj))))
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "server".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
