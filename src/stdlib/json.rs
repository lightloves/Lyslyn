use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use serde_json::Value as JsonValue;
use std::cell::RefCell;
use std::rc::Rc;

pub fn create_json_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "parse".to_string(),
        Value::NativeFunction(
            "parse".to_string(),
            Rc::new(|args| {
                if let Some(Value::Str(s)) = args.first() {
                    let parsed: JsonValue =
                        serde_json::from_str(s).map_err(|e| format!("JSON parse error: {}", e))?;
                    Ok(json_to_lyslyn(&parsed))
                } else {
                    Err("Expected string argument to json.parse".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "stringify".to_string(),
        Value::NativeFunction(
            "stringify".to_string(),
            Rc::new(|args| {
                if let Some(val) = args.first() {
                    let jval = lyslyn_to_json(val)?;
                    serde_json::to_string(&jval)
                        .map(Value::Str)
                        .map_err(|e| format!("JSON serialize error: {}", e))
                } else {
                    Err("Expected argument to json.stringify".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "json".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}

fn json_to_lyslyn(j: &JsonValue) -> Value {
    match j {
        JsonValue::Null => Value::Nil,
        JsonValue::Bool(b) => Value::Bool(*b),
        JsonValue::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Int(i)
            } else if let Some(f) = n.as_f64() {
                Value::Float(f)
            } else {
                Value::Nil
            }
        }
        JsonValue::String(s) => Value::Str(s.clone()),
        JsonValue::Array(arr) => {
            let list = arr.iter().map(json_to_lyslyn).collect();
            Value::List(Rc::new(RefCell::new(list)))
        }
        JsonValue::Object(obj) => {
            let mut map = IndexMap::new();
            for (k, v) in obj {
                map.insert(k.clone(), json_to_lyslyn(v));
            }
            Value::Map(Rc::new(RefCell::new(map)))
        }
    }
}

fn lyslyn_to_json(v: &Value) -> Result<JsonValue, String> {
    match v {
        Value::Nil => Ok(JsonValue::Null),
        Value::Bool(b) => Ok(JsonValue::Bool(*b)),
        Value::Int(i) => Ok(JsonValue::Number((*i).into())),
        Value::Float(f) => serde_json::Number::from_f64(*f)
            .map(JsonValue::Number)
            .ok_or_else(|| "Invalid float for JSON".to_string()),
        Value::Str(s) => Ok(JsonValue::String(s.clone())),
        Value::List(l) => {
            let mut arr = Vec::new();
            for item in l.borrow().iter() {
                arr.push(lyslyn_to_json(item)?);
            }
            Ok(JsonValue::Array(arr))
        }
        Value::Map(m) => {
            let mut obj = serde_json::Map::new();
            for (k, val) in m.borrow().iter() {
                obj.insert(k.clone(), lyslyn_to_json(val)?);
            }
            Ok(JsonValue::Object(obj))
        }
        _ => Err(format!("Cannot convert type '{}' to JSON", v.type_name())),
    }
}
