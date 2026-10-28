use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use sha2::{Digest, Sha256};
use std::cell::RefCell;
use std::rc::Rc;
use std::time::{SystemTime, UNIX_EPOCH};

pub fn create_crypto_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "sha256".to_string(),
        Value::NativeFunction(
            "sha256".to_string(),
            Rc::new(|args| {
                if let Some(Value::Str(s)) = args.first() {
                    let mut hasher = Sha256::new();
                    hasher.update(s.as_bytes());
                    let result = hasher.finalize();
                    Ok(Value::Str(hex::encode(result)))
                } else {
                    Err("Expected string argument to crypto.sha256".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "token_hex".to_string(),
        Value::NativeFunction(
            "token_hex".to_string(),
            Rc::new(|args| {
                let n = if let Some(Value::Int(i)) = args.first() {
                    *i as usize
                } else {
                    16
                };

                let now = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_nanos();
                let seed = format!("{}-lyslyn-random", now);
                let mut hasher = Sha256::new();
                hasher.update(seed.as_bytes());
                let result = hex::encode(hasher.finalize());
                let token = if n * 2 <= result.len() {
                    result[..n * 2].to_string()
                } else {
                    result
                };
                Ok(Value::Str(token))
            }),
        ),
    );

    exports.insert(
        "token".to_string(),
        exports.get("token_hex").unwrap().clone(),
    );

    exports.insert(
        "uuid".to_string(),
        Value::NativeFunction(
            "uuid".to_string(),
            Rc::new(|_| {
                let now = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_nanos();
                let seed = format!("{}-uuid-seed", now);
                let mut hasher = Sha256::new();
                hasher.update(seed.as_bytes());
                let h = hex::encode(hasher.finalize());
                let uuid = format!(
                    "{}-{}-4{}-a{}-{}",
                    &h[0..8],
                    &h[8..12],
                    &h[13..16],
                    &h[17..20],
                    &h[20..32]
                );
                Ok(Value::Str(uuid))
            }),
        ),
    );

    exports.insert(
        "hash_password".to_string(),
        Value::NativeFunction(
            "hash_password".to_string(),
            Rc::new(|args| {
                if let Some(Value::Str(pwd)) = args.first() {
                    let salt = "lyslyn_salt_v1";
                    let mut hasher = Sha256::new();
                    hasher.update(format!("{}:{}", salt, pwd).as_bytes());
                    let hash = hex::encode(hasher.finalize());
                    Ok(Value::Str(format!("{}:{}", salt, hash)))
                } else {
                    Err("Expected string password to crypto.hash_password".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "verify_password".to_string(),
        Value::NativeFunction(
            "verify_password".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    if let (Value::Str(pwd), Value::Str(stored_hash)) = (&args[0], &args[1]) {
                        let parts: Vec<&str> = stored_hash.split(':').collect();
                        if parts.len() == 2 {
                            let salt = parts[0];
                            let expected_hash = parts[1];
                            let mut hasher = Sha256::new();
                            hasher.update(format!("{}:{}", salt, pwd).as_bytes());
                            let computed = hex::encode(hasher.finalize());
                            Ok(Value::Bool(computed == expected_hash))
                        } else {
                            Ok(Value::Bool(false))
                        }
                    } else {
                        Err(
                            "Expected string password and hash to crypto.verify_password"
                                .to_string(),
                        )
                    }
                } else {
                    Err("Expected 2 arguments to crypto.verify_password".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "crypto".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
