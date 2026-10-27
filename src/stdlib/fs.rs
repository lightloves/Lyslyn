use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::rc::Rc;

pub fn create_fs_module() -> Value {
    let mut exports = IndexMap::new();

    let read_fn = Value::NativeFunction(
        "read_text".to_string(),
        Rc::new(|args| {
            if let Some(arg) = args.first() {
                let path = arg.to_string();
                fs::read_to_string(&path)
                    .map(Value::Str)
                    .map_err(|e| format!("Failed to read file '{}': {}", path, e))
            } else {
                Err("Expected path to files.read_text".to_string())
            }
        }),
    );
    exports.insert("read".to_string(), read_fn.clone());
    exports.insert("read_text".to_string(), read_fn);

    let write_fn = Value::NativeFunction(
        "write_text".to_string(),
        Rc::new(|args| {
            if args.len() >= 2 {
                let path = args[0].to_string();
                let content = args[1].to_string();
                if let Some(parent) = Path::new(&path).parent() {
                    if !parent.as_os_str().is_empty() {
                        let _ = fs::create_dir_all(parent);
                    }
                }
                fs::write(&path, content)
                    .map(|_| Value::Bool(true))
                    .map_err(|e| format!("Failed to write file '{}': {}", path, e))
            } else {
                Err("Expected 2 arguments to files.write_text".to_string())
            }
        }),
    );
    exports.insert("write".to_string(), write_fn.clone());
    exports.insert("write_text".to_string(), write_fn);

    let append_fn = Value::NativeFunction(
        "append_text".to_string(),
        Rc::new(|args| {
            if args.len() >= 2 {
                let path = args[0].to_string();
                let content = args[1].to_string();
                if let Some(parent) = Path::new(&path).parent() {
                    if !parent.as_os_str().is_empty() {
                        let _ = fs::create_dir_all(parent);
                    }
                }
                let mut file = fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(&path)
                    .map_err(|e| format!("Failed to open file '{}': {}", path, e))?;
                file.write_all(content.as_bytes())
                    .map(|_| Value::Bool(true))
                    .map_err(|e| format!("Failed to append to file '{}': {}", path, e))
            } else {
                Err("Expected 2 arguments to files.append_text".to_string())
            }
        }),
    );
    exports.insert("append".to_string(), append_fn.clone());
    exports.insert("append_text".to_string(), append_fn);

    exports.insert(
        "exists".to_string(),
        Value::NativeFunction(
            "exists".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let path = arg.to_string();
                    Ok(Value::Bool(Path::new(&path).exists()))
                } else {
                    Err("Expected path to files.exists".to_string())
                }
            }),
        ),
    );

    let delete_fn = Value::NativeFunction(
        "delete".to_string(),
        Rc::new(|args| {
            if let Some(arg) = args.first() {
                let path = arg.to_string();
                let p = Path::new(&path);
                if !p.exists() {
                    return Ok(Value::Bool(true));
                }
                if p.is_dir() {
                    fs::remove_dir_all(p)
                        .map(|_| Value::Bool(true))
                        .map_err(|e| format!("Failed to remove directory '{}': {}", path, e))
                } else {
                    fs::remove_file(p)
                        .map(|_| Value::Bool(true))
                        .map_err(|e| format!("Failed to remove file '{}': {}", path, e))
                }
            } else {
                Err("Expected path to files.delete".to_string())
            }
        }),
    );
    exports.insert("delete".to_string(), delete_fn.clone());
    exports.insert("remove".to_string(), delete_fn);

    let list_fn = Value::NativeFunction(
        "list_dir".to_string(),
        Rc::new(|args| {
            let path = if let Some(arg) = args.first() {
                arg.to_string()
            } else {
                ".".to_string()
            };
            let entries = fs::read_dir(&path)
                .map_err(|e| format!("Failed to list directory '{}': {}", path, e))?;
            let mut list = Vec::new();
            for entry in entries.flatten() {
                if let Some(name) = entry.file_name().to_str() {
                    list.push(Value::Str(name.to_string()));
                }
            }
            Ok(Value::List(Rc::new(RefCell::new(list))))
        }),
    );
    exports.insert("list_dir".to_string(), list_fn.clone());
    exports.insert("list_directory".to_string(), list_fn);

    exports.insert(
        "make_directory".to_string(),
        Value::NativeFunction(
            "make_directory".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let path = arg.to_string();
                    fs::create_dir_all(&path)
                        .map(|_| Value::Bool(true))
                        .map_err(|e| format!("Failed to create directory '{}': {}", path, e))
                } else {
                    Err("Expected path to files.make_directory".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "files".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
