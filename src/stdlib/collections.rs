use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;

pub fn create_collections_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "unique".to_string(),
        Value::NativeFunction(
            "unique".to_string(),
            Rc::new(|args| {
                if let Some(Value::List(l)) = args.first() {
                    let mut unique_list = Vec::new();
                    for item in l.borrow().iter() {
                        if !unique_list.contains(item) {
                            unique_list.push(item.clone());
                        }
                    }
                    Ok(Value::List(Rc::new(RefCell::new(unique_list))))
                } else {
                    Err("Expected list argument to collections.unique".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "chunk".to_string(),
        Value::NativeFunction(
            "chunk".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    if let (Value::List(l), Value::Int(size)) = (&args[0], &args[1]) {
                        if *size <= 0 {
                            return Err("Chunk size must be positive".to_string());
                        }
                        let borrowed = l.borrow();
                        let mut chunks = Vec::new();
                        for slice in borrowed.chunks(*size as usize) {
                            chunks.push(Value::List(Rc::new(RefCell::new(slice.to_vec()))));
                        }
                        Ok(Value::List(Rc::new(RefCell::new(chunks))))
                    } else {
                        Err("Expected list and integer size to collections.chunk".to_string())
                    }
                } else {
                    Err("Expected 2 arguments to collections.chunk".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "flatten".to_string(),
        Value::NativeFunction(
            "flatten".to_string(),
            Rc::new(|args| {
                if let Some(Value::List(l)) = args.first() {
                    let mut flat = Vec::new();
                    for item in l.borrow().iter() {
                        if let Value::List(inner) = item {
                            flat.extend(inner.borrow().clone());
                        } else {
                            flat.push(item.clone());
                        }
                    }
                    Ok(Value::List(Rc::new(RefCell::new(flat))))
                } else {
                    Err("Expected list argument to collections.flatten".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "zip".to_string(),
        Value::NativeFunction(
            "zip".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    if let (Value::List(l1), Value::List(l2)) = (&args[0], &args[1]) {
                        let b1 = l1.borrow();
                        let b2 = l2.borrow();
                        let mut zipped = Vec::new();
                        for (a, b) in b1.iter().zip(b2.iter()) {
                            zipped.push(Value::List(Rc::new(RefCell::new(vec![
                                a.clone(),
                                b.clone(),
                            ]))));
                        }
                        Ok(Value::List(Rc::new(RefCell::new(zipped))))
                    } else {
                        Err("Expected 2 lists to collections.zip".to_string())
                    }
                } else {
                    Err("Expected 2 arguments to collections.zip".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "collections".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
