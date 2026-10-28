use crate::values::Value;
use indexmap::IndexMap;
use regex::Regex;
use std::cell::RefCell;
use std::rc::Rc;

pub fn load_regex_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "is_match".to_string(),
        Value::NativeFunction(
            "is_match".to_string(),
            Rc::new(|args| {
                if args.len() < 2 {
                    return Err("Expected 2 arguments to regex.is_match(pattern, text)".to_string());
                }
                let pat_str = args[0].to_string();
                let text = args[1].to_string();
                let re = Regex::new(&pat_str)
                    .map_err(|e| format!("Invalid regex '{}': {}", pat_str, e))?;
                Ok(Value::Bool(re.is_match(&text)))
            }),
        ),
    );

    exports.insert(
        "find".to_string(),
        Value::NativeFunction(
            "find".to_string(),
            Rc::new(|args| {
                if args.len() < 2 {
                    return Err("Expected 2 arguments to regex.find(pattern, text)".to_string());
                }
                let pat_str = args[0].to_string();
                let text = args[1].to_string();
                let re = Regex::new(&pat_str)
                    .map_err(|e| format!("Invalid regex '{}': {}", pat_str, e))?;
                if let Some(m) = re.find(&text) {
                    Ok(Value::Str(m.as_str().to_string()))
                } else {
                    Ok(Value::Nil)
                }
            }),
        ),
    );

    exports.insert(
        "find_all".to_string(),
        Value::NativeFunction(
            "find_all".to_string(),
            Rc::new(|args| {
                if args.len() < 2 {
                    return Err("Expected 2 arguments to regex.find_all(pattern, text)".to_string());
                }
                let pat_str = args[0].to_string();
                let text = args[1].to_string();
                let re = Regex::new(&pat_str)
                    .map_err(|e| format!("Invalid regex '{}': {}", pat_str, e))?;
                let matches: Vec<Value> = re
                    .find_iter(&text)
                    .map(|m| Value::Str(m.as_str().to_string()))
                    .collect();
                Ok(Value::List(Rc::new(RefCell::new(matches))))
            }),
        ),
    );

    exports.insert(
        "replace".to_string(),
        Value::NativeFunction(
            "replace".to_string(),
            Rc::new(|args| {
                if args.len() < 3 {
                    return Err(
                        "Expected 3 arguments to regex.replace(pattern, replacement, text)"
                            .to_string(),
                    );
                }
                let pat_str = args[0].to_string();
                let rep = args[1].to_string();
                let text = args[2].to_string();
                let re = Regex::new(&pat_str)
                    .map_err(|e| format!("Invalid regex '{}': {}", pat_str, e))?;
                let result = re.replace_all(&text, rep.as_str()).to_string();
                Ok(Value::Str(result))
            }),
        ),
    );

    exports.insert(
        "split".to_string(),
        Value::NativeFunction(
            "split".to_string(),
            Rc::new(|args| {
                if args.len() < 2 {
                    return Err("Expected 2 arguments to regex.split(pattern, text)".to_string());
                }
                let pat_str = args[0].to_string();
                let text = args[1].to_string();
                let re = Regex::new(&pat_str)
                    .map_err(|e| format!("Invalid regex '{}': {}", pat_str, e))?;
                let parts: Vec<Value> =
                    re.split(&text).map(|s| Value::Str(s.to_string())).collect();
                Ok(Value::List(Rc::new(RefCell::new(parts))))
            }),
        ),
    );

    Value::Module(Rc::new(crate::values::LyslynModule {
        name: "regex".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
