use crate::values::Value;
use indexmap::IndexMap;
use std::cell::RefCell;
use std::process::Command;
use std::rc::Rc;

pub fn load_os_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "platform".to_string(),
        Value::NativeFunction(
            "platform".to_string(),
            Rc::new(|_| Ok(Value::Str(std::env::consts::OS.to_string()))),
        ),
    );

    exports.insert(
        "arch".to_string(),
        Value::NativeFunction(
            "arch".to_string(),
            Rc::new(|_| Ok(Value::Str(std::env::consts::ARCH.to_string()))),
        ),
    );

    exports.insert(
        "cwd".to_string(),
        Value::NativeFunction(
            "cwd".to_string(),
            Rc::new(|_| {
                let p = std::env::current_dir()
                    .map(|d| d.to_string_lossy().to_string())
                    .unwrap_or_else(|_| ".".to_string());
                Ok(Value::Str(p))
            }),
        ),
    );

    exports.insert(
        "args".to_string(),
        Value::NativeFunction(
            "args".to_string(),
            Rc::new(|_| {
                let args_list: Vec<Value> = std::env::args().map(Value::Str).collect();
                Ok(Value::List(Rc::new(RefCell::new(args_list))))
            }),
        ),
    );

    exports.insert(
        "exit".to_string(),
        Value::NativeFunction(
            "exit".to_string(),
            Rc::new(|args| {
                let code = if let Some(Value::Int(i)) = args.first() {
                    *i as i32
                } else {
                    0
                };
                std::process::exit(code);
            }),
        ),
    );

    exports.insert(
        "exec".to_string(),
        Value::NativeFunction(
            "exec".to_string(),
            Rc::new(|args| {
                if let Some(cmd_val) = args.first() {
                    let cmd_str = cmd_val.to_string();
                    let output = Command::new("sh")
                        .arg("-c")
                        .arg(&cmd_str)
                        .output()
                        .map_err(|e| format!("Failed to execute command: {}", e))?;
                    let out = String::from_utf8_lossy(&output.stdout).to_string();
                    Ok(Value::Str(out))
                } else {
                    Err("Expected command string in os.exec".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(crate::values::LyslynModule {
        name: "os".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
