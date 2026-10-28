use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;

pub fn create_validation_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "validate".to_string(),
        Value::NativeFunction(
            "validate".to_string(),
            Rc::new(|args| {
                if args.len() < 2 {
                    return Err(
                        "Expected 2 arguments to validation.validate(data, schema)".to_string()
                    );
                }

                let data_map = match &args[0] {
                    Value::Map(m) => m.borrow().clone(),
                    _ => {
                        let mut res = IndexMap::new();
                        res.insert("valid".to_string(), Value::Bool(false));
                        let mut err_entry = IndexMap::new();
                        err_entry.insert("field".to_string(), Value::Str("_root".to_string()));
                        err_entry.insert(
                            "issue".to_string(),
                            Value::Str("Expected object for validation".to_string()),
                        );
                        let errs = vec![Value::Map(Rc::new(RefCell::new(err_entry)))];
                        res.insert(
                            "errors".to_string(),
                            Value::List(Rc::new(RefCell::new(errs))),
                        );
                        return Ok(Value::Map(Rc::new(RefCell::new(res))));
                    }
                };

                let schema_map = match &args[1] {
                    Value::Map(m) => m.borrow().clone(),
                    _ => {
                        return Err("Expected schema map as second argument to validate".to_string())
                    }
                };

                let mut errors = Vec::new();

                for (field, rule_val) in schema_map {
                    let rule_str = rule_val.to_string();
                    let rules: Vec<&str> = if rule_str.contains('|') {
                        rule_str.split('|').map(|s| s.trim()).collect()
                    } else {
                        rule_str.split_whitespace().collect()
                    };

                    let val_opt = data_map.get(&field);
                    let is_required = rules.iter().any(|r| r.eq_ignore_ascii_case("required"));

                    if val_opt.is_none() || matches!(val_opt, Some(Value::Nil)) {
                        if is_required {
                            let mut err = IndexMap::new();
                            err.insert("field".to_string(), Value::Str(field.clone()));
                            err.insert(
                                "issue".to_string(),
                                Value::Str(format!("Field '{}' is required", field)),
                            );
                            errors.push(Value::Map(Rc::new(RefCell::new(err))));
                        }
                        continue;
                    }

                    let val = val_opt.unwrap();

                    if rules.iter().any(|r| r.eq_ignore_ascii_case("string"))
                        && !matches!(val, Value::Str(_))
                    {
                        let mut err = IndexMap::new();
                        err.insert("field".to_string(), Value::Str(field.clone()));
                        err.insert(
                            "issue".to_string(),
                            Value::Str(format!("Field '{}' must be a string", field)),
                        );
                        errors.push(Value::Map(Rc::new(RefCell::new(err))));
                        continue;
                    }

                    if rules.iter().any(|r| r.eq_ignore_ascii_case("number"))
                        && !matches!(val, Value::Int(_) | Value::Float(_))
                    {
                        let mut err = IndexMap::new();
                        err.insert("field".to_string(), Value::Str(field.clone()));
                        err.insert(
                            "issue".to_string(),
                            Value::Str(format!("Field '{}' must be a number", field)),
                        );
                        errors.push(Value::Map(Rc::new(RefCell::new(err))));
                        continue;
                    }

                    if rules.iter().any(|r| r.eq_ignore_ascii_case("email")) {
                        let is_email = match val {
                            Value::Str(s) => s.contains('@') && s.contains('.'),
                            _ => false,
                        };
                        if !is_email {
                            let mut err = IndexMap::new();
                            err.insert("field".to_string(), Value::Str(field.clone()));
                            err.insert(
                                "issue".to_string(),
                                Value::Str(format!(
                                    "Field '{}' must be a valid email address",
                                    field
                                )),
                            );
                            errors.push(Value::Map(Rc::new(RefCell::new(err))));
                            continue;
                        }
                    }

                    for r in &rules {
                        if r.starts_with("min:") {
                            if let Ok(min_num) = r[4..].parse::<f64>() {
                                match val {
                                    Value::Int(i) if (*i as f64) < min_num => {
                                        let mut err = IndexMap::new();
                                        err.insert("field".to_string(), Value::Str(field.clone()));
                                        err.insert(
                                            "issue".to_string(),
                                            Value::Str(format!(
                                                "Field '{}' must be at least {}",
                                                field, min_num
                                            )),
                                        );
                                        errors.push(Value::Map(Rc::new(RefCell::new(err))));
                                    }
                                    Value::Float(f) if *f < min_num => {
                                        let mut err = IndexMap::new();
                                        err.insert("field".to_string(), Value::Str(field.clone()));
                                        err.insert(
                                            "issue".to_string(),
                                            Value::Str(format!(
                                                "Field '{}' must be at least {}",
                                                field, min_num
                                            )),
                                        );
                                        errors.push(Value::Map(Rc::new(RefCell::new(err))));
                                    }
                                    Value::Str(s) if (s.chars().count() as f64) < min_num => {
                                        let mut err = IndexMap::new();
                                        err.insert("field".to_string(), Value::Str(field.clone()));
                                        err.insert(
                                            "issue".to_string(),
                                            Value::Str(format!(
                                                "Field '{}' length must be at least {}",
                                                field, min_num as i64
                                            )),
                                        );
                                        errors.push(Value::Map(Rc::new(RefCell::new(err))));
                                    }
                                    Value::List(l) if (l.borrow().len() as f64) < min_num => {
                                        let mut err = IndexMap::new();
                                        err.insert("field".to_string(), Value::Str(field.clone()));
                                        err.insert(
                                            "issue".to_string(),
                                            Value::Str(format!(
                                                "Field '{}' items must be at least {}",
                                                field, min_num as i64
                                            )),
                                        );
                                        errors.push(Value::Map(Rc::new(RefCell::new(err))));
                                    }
                                    _ => {}
                                }
                            }
                        }
                    }
                }

                let is_valid = errors.is_empty();
                let mut result = IndexMap::new();
                result.insert("valid".to_string(), Value::Bool(is_valid));
                result.insert(
                    "errors".to_string(),
                    Value::List(Rc::new(RefCell::new(errors))),
                );

                Ok(Value::Map(Rc::new(RefCell::new(result))))
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "validation".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
