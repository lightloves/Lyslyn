use crate::values::{LyslynModule, Value};
use hmac::{Hmac, Mac};
use indexmap::IndexMap;
use sha2::Sha256;
use std::cell::RefCell;
use std::rc::Rc;
use std::time::{SystemTime, UNIX_EPOCH};

type HmacSha256 = Hmac<Sha256>;

fn b64url_encode(data: &[u8]) -> String {
    let b64 = base64_encode(data);
    b64.replace('+', "-")
        .replace('/', "_")
        .trim_end_matches('=')
        .to_string()
}

fn b64url_decode(s: &str) -> Result<Vec<u8>, String> {
    let mut base = s.replace('-', "+").replace('_', "/");
    let pad = 4 - (base.len() % 4);
    if pad < 4 {
        base.push_str(&"=".repeat(pad));
    }
    base64_decode(&base)
}

fn base64_encode(data: &[u8]) -> String {
    const TABLE: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::new();
    let mut i = 0;
    while i < data.len() {
        let b0 = data[i] as u32;
        let b1 = if i + 1 < data.len() { data[i + 1] as u32 } else { 0 };
        let b2 = if i + 2 < data.len() { data[i + 2] as u32 } else { 0 };

        let triple = (b0 << 16) | (b1 << 8) | b2;

        out.push(TABLE[((triple >> 18) & 0x3F) as usize] as char);
        out.push(TABLE[((triple >> 12) & 0x3F) as usize] as char);

        if i + 1 < data.len() {
            out.push(TABLE[((triple >> 6) & 0x3F) as usize] as char);
        } else {
            out.push('=');
        }

        if i + 2 < data.len() {
            out.push(TABLE[(triple & 0x3F) as usize] as char);
        } else {
            out.push('=');
        }

        i += 3;
    }
    out
}

fn base64_decode(s: &str) -> Result<Vec<u8>, String> {
    let s_clean = s.trim_end_matches('=');
    let mut out = Vec::new();
    let mut buf = 0u32;
    let mut bits = 0;

    for c in s_clean.chars() {
        let val = match c {
            'A'..='Z' => (c as u8 - b'A') as u32,
            'a'..='z' => (c as u8 - b'a' + 26) as u32,
            '0'..='9' => (c as u8 - b'0' + 52) as u32,
            '+' => 62,
            '/' => 63,
            _ => return Err(format!("Invalid base64 character '{}'", c)),
        };
        buf = (buf << 6) | val;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((buf >> bits) as u8);
            buf &= (1 << bits) - 1;
        }
    }
    Ok(out)
}

fn value_to_serde_json(v: &Value) -> serde_json::Value {
    match v {
        Value::Nil => serde_json::Value::Null,
        Value::Bool(b) => serde_json::Value::Bool(*b),
        Value::Int(i) => serde_json::Value::Number((*i).into()),
        Value::Float(f) => serde_json::Number::from_f64(*f)
            .map(serde_json::Value::Number)
            .unwrap_or(serde_json::Value::Null),
        Value::Str(s) => serde_json::Value::String(s.clone()),
        Value::List(l) => {
            let arr = l.borrow().iter().map(value_to_serde_json).collect();
            serde_json::Value::Array(arr)
        }
        Value::Map(m) => {
            let mut obj = serde_json::Map::new();
            for (k, val) in m.borrow().iter() {
                obj.insert(k.clone(), value_to_serde_json(val));
            }
            serde_json::Value::Object(obj)
        }
        _ => serde_json::Value::String(v.to_string()),
    }
}

fn serde_json_to_value(j: serde_json::Value) -> Value {
    match j {
        serde_json::Value::Null => Value::Nil,
        serde_json::Value::Bool(b) => Value::Bool(b),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Int(i)
            } else if let Some(f) = n.as_f64() {
                Value::Float(f)
            } else {
                Value::Int(0)
            }
        }
        serde_json::Value::String(s) => Value::Str(s),
        serde_json::Value::Array(a) => {
            let list = a.into_iter().map(serde_json_to_value).collect();
            Value::List(Rc::new(RefCell::new(list)))
        }
        serde_json::Value::Object(o) => {
            let mut map = IndexMap::new();
            for (k, v) in o {
                map.insert(k, serde_json_to_value(v));
            }
            Value::Map(Rc::new(RefCell::new(map)))
        }
    }
}

pub fn create_jwt_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "sign".to_string(),
        Value::NativeFunction(
            "sign".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let payload = &args[0];
                    let secret = args[1].to_string();
                    let expires_in: Option<i64> = if args.len() > 2 {
                        match &args[2] {
                            Value::Int(i) => Some(*i),
                            Value::Float(f) => Some(*f as i64),
                            _ => None,
                        }
                    } else {
                        Some(3600)
                    };

                    let now = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap_or_default()
                        .as_secs() as i64;

                    let mut payload_json = match value_to_serde_json(payload) {
                        serde_json::Value::Object(o) => o,
                        _ => return Err("JWT payload must be an object/map".to_string()),
                    };

                    if !payload_json.contains_key("iat") {
                        payload_json.insert("iat".to_string(), serde_json::Value::Number(now.into()));
                    }
                    if let Some(exp_sec) = expires_in {
                        if exp_sec > 0 {
                            payload_json.insert(
                                "exp".to_string(),
                                serde_json::Value::Number((now + exp_sec).into()),
                            );
                        }
                    }

                    let header_json = serde_json::json!({"alg": "HS256", "typ": "JWT"});
                    let header_b64 = b64url_encode(serde_json::to_string(&header_json).unwrap().as_bytes());
                    let payload_b64 = b64url_encode(
                        serde_json::to_string(&serde_json::Value::Object(payload_json))
                            .unwrap()
                            .as_bytes(),
                    );

                    let signing_input = format!("{}.{}", header_b64, payload_b64);
                    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
                        .map_err(|e| format!("HMAC error: {}", e))?;
                    mac.update(signing_input.as_bytes());
                    let sig_bytes = mac.finalize().into_bytes();
                    let sig_b64 = b64url_encode(&sig_bytes);

                    Ok(Value::Str(format!("{}.{}", signing_input, sig_b64)))
                } else {
                    Err("Expected at least 2 arguments to jwt.sign(payload, secret)".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "verify".to_string(),
        Value::NativeFunction(
            "verify".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let token = args[0].to_string();
                    let secret = args[1].to_string();

                    let parts: Vec<&str> = token.split('.').collect();
                    if parts.len() != 3 {
                        return Err("Invalid JWT format: expected 3 parts".to_string());
                    }

                    let signing_input = format!("{}.{}", parts[0], parts[1]);
                    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
                        .map_err(|e| format!("HMAC error: {}", e))?;
                    mac.update(signing_input.as_bytes());
                    let expected_sig = mac.finalize().into_bytes();
                    let expected_sig_b64 = b64url_encode(&expected_sig);

                    if parts[2] != expected_sig_b64 {
                        return Err("JWT verification failed: Invalid signature".to_string());
                    }

                    let payload_bytes = b64url_decode(parts[1])
                        .map_err(|e| format!("Failed to decode JWT payload: {}", e))?;
                    let payload_json: serde_json::Value = serde_json::from_slice(&payload_bytes)
                        .map_err(|e| format!("Failed to parse JWT payload JSON: {}", e))?;

                    let now = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap_or_default()
                        .as_secs() as i64;

                    if let Some(exp) = payload_json.get("exp").and_then(|v| v.as_i64()) {
                        if now > exp {
                            return Err("JWT token has expired".to_string());
                        }
                    }

                    Ok(serde_json_to_value(payload_json))
                } else {
                    Err("Expected 2 arguments to jwt.verify(token, secret)".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "jwt".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
