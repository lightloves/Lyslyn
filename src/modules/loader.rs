use crate::compiler::Compiler;
use crate::errors::{ErrorKind, LyslynError, Span};
use crate::lexer::Scanner;
use crate::parser::Parser;
use crate::stdlib::get_standard_modules;
use crate::values::{LyslynModule, Value};
use crate::vm::VM;
use indexmap::IndexMap;
use std::cell::RefCell;
use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;
use std::rc::Rc;

pub struct ModuleLoader {
    cached_modules: IndexMap<String, Value>,
    loading_stack: HashSet<String>,
    search_paths: Vec<PathBuf>,
}

impl ModuleLoader {
    pub fn new() -> Self {
        let std_mods = get_standard_modules();
        ModuleLoader {
            cached_modules: std_mods,
            loading_stack: HashSet::new(),
            search_paths: vec![PathBuf::from("."), PathBuf::from("examples")],
        }
    }

    pub fn add_search_path(&mut self, path: PathBuf) {
        if !self.search_paths.contains(&path) {
            self.search_paths.push(path);
        }
    }

    pub fn load(&mut self, name: &str) -> Result<Value, LyslynError> {
        if let Some(cached) = self.cached_modules.get(name) {
            return Ok(cached.clone());
        }

        if self.loading_stack.contains(name) {
            return Err(LyslynError::new(
                ErrorKind::Runtime,
                format!("Circular import detected when loading module '{}'", name),
                Span::new(1, 1, 1),
                name,
            ));
        }

        let mut target_path: Option<PathBuf> = None;
        let direct = PathBuf::from(name);
        if direct.exists() && direct.is_file() {
            target_path = Some(direct);
        } else {
            let clean_name = name.strip_suffix(".lys").unwrap_or(name);
            for base in &self.search_paths {
                let candidate = base.join(format!("{}.lys", clean_name));
                if candidate.exists() && candidate.is_file() {
                    target_path = Some(candidate);
                    break;
                }
                let cand_raw = base.join(name);
                if cand_raw.exists() && cand_raw.is_file() {
                    target_path = Some(cand_raw);
                    break;
                }
            }
        }

        let file_path = match target_path {
            Some(p) => p,
            None => {
                return Err(LyslynError::new(
                    ErrorKind::Runtime,
                    format!("Module '{}' not found in search paths", name),
                    Span::new(1, 1, 1),
                    name,
                )
                .with_suggestion("Ensure the module file exists with extension '.lys'"));
            }
        };

        let source = fs::read_to_string(&file_path).map_err(|e| {
            LyslynError::new(
                ErrorKind::Runtime,
                format!("Failed to read module file '{:?}': {}", file_path, e),
                Span::new(1, 1, 1),
                name,
            )
        })?;

        self.loading_stack.insert(name.to_string());

        let filename_str = file_path.to_string_lossy().to_string();
        let mut scanner = Scanner::new(&source, &filename_str);
        let tokens = scanner.scan_tokens()?;

        let mut parser = Parser::new(tokens, &filename_str, &source);
        let program = parser.parse()?;

        let mut compiler = Compiler::new(&filename_str, &source);
        let chunk = compiler.compile(&program)?;

        let mut vm = VM::new(None);
        let _ = vm.run(chunk)?;

        let mut exports = IndexMap::new();
        for (k, v) in vm.globals {
            if !k.starts_with('$') {
                exports.insert(k, v);
            }
        }

        self.loading_stack.remove(name);

        let module_val = Value::Module(Rc::new(LyslynModule {
            name: name.to_string(),
            exports: Rc::new(RefCell::new(exports)),
        }));

        self.cached_modules
            .insert(name.to_string(), module_val.clone());
        Ok(module_val)
    }
}
