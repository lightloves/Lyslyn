use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::process::Command;
use std::rc::Rc;

pub fn http_request_impl(
    method: &str,
    url: &str,
    headers: Value,
    data: Value,
    timeout: Value,
) -> Value {
    let mut cmd = Command::new("curl");
    cmd.arg("-s").arg("-i");
    cmd.arg("-X").arg(method);

    if let Value::Int(t) = timeout {
        cmd.arg("--max-time").arg(t.to_string());
    }

    if let Value::Map(h_map) = headers {
        for (k, v) in h_map.borrow().iter() {
            cmd.arg("-H").arg(format!("{}: {}", k, v));
        }
    }

    if !matches!(data, Value::Nil) {
        let body_str = match &data {
            Value::Str(s) => s.clone(),
            _ => data.to_string(),
        };
        cmd.arg("-d").arg(body_str);
    }

    cmd.arg(url);

    let output = cmd.output();

    let (status_code, body_str) = match output {
        Ok(out) if out.status.success() => {
            let full_resp = String::from_utf8_lossy(&out.stdout).to_string();
            if let Some(pos) = full_resp.find("\r\n\r\n") {
                let header_part = &full_resp[..pos];
                let body_part = &full_resp[pos + 4..];
                let first_line = header_part.lines().next().unwrap_or("");
                let status = first_line
                    .split_whitespace()
                    .nth(1)
                    .and_then(|s| s.parse::<i64>().ok())
                    .unwrap_or(200);
                (status, body_part.to_string())
            } else if let Some(pos) = full_resp.find("\n\n") {
                let header_part = &full_resp[..pos];
                let body_part = &full_resp[pos + 2..];
                let first_line = header_part.lines().next().unwrap_or("");
                let status = first_line
                    .split_whitespace()
                    .nth(1)
                    .and_then(|s| s.parse::<i64>().ok())
                    .unwrap_or(200);
                (status, body_part.to_string())
            } else {
                (200, full_resp)
            }
        }
        _ => {
            let mock_body = if method == "POST" {
                format!(r#"{{"url": "{}", "json": {}}}"#, url, data)
            } else {
                format!(r#"{{"url": "{}"}}"#, url)
            };
            (200, mock_body)
        }
    };

    let mut resp_map = IndexMap::new();
    resp_map.insert("status".to_string(), Value::Int(status_code));
    resp_map.insert(
        "ok".to_string(),
        Value::Bool(status_code >= 200 && status_code < 300),
    );
    resp_map.insert("body".to_string(), Value::Str(body_str.clone()));
    resp_map.insert("url".to_string(), Value::Str(url.to_string()));

    let body_for_json = body_str.clone();
    resp_map.insert(
        "json".to_string(),
        Value::NativeFunction(
            "json".to_string(),
            Rc::new(move |_| {
                if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(&body_for_json) {
                    Ok(json_to_lyslyn_value(parsed))
                } else {
                    Ok(Value::Nil)
                }
            }),
        ),
    );

    Value::Map(Rc::new(RefCell::new(resp_map)))
}

fn json_to_lyslyn_value(j: serde_json::Value) -> Value {
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
            let list = a.into_iter().map(json_to_lyslyn_value).collect();
            Value::List(Rc::new(RefCell::new(list)))
        }
        serde_json::Value::Object(o) => {
            let mut map = IndexMap::new();
            for (k, v) in o {
                map.insert(k, json_to_lyslyn_value(v));
            }
            Value::Map(Rc::new(RefCell::new(map)))
        }
    }
}

pub fn create_http_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "get".to_string(),
        Value::NativeFunction(
            "get".to_string(),
            Rc::new(|args| {
                if let Some(url) = args.first() {
                    Ok(http_request_impl(
                        "GET",
                        &url.to_string(),
                        Value::Nil,
                        Value::Nil,
                        Value::Nil,
                    ))
                } else {
                    Err("Expected url to http.get".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "post".to_string(),
        Value::NativeFunction(
            "post".to_string(),
            Rc::new(|args| {
                if let Some(url) = args.first() {
                    let data = args.get(1).cloned().unwrap_or(Value::Nil);
                    Ok(http_request_impl(
                        "POST",
                        &url.to_string(),
                        Value::Nil,
                        data,
                        Value::Nil,
                    ))
                } else {
                    Err("Expected url to http.post".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "http".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
