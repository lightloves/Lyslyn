use crate::compiler::Compiler;
use crate::lexer::Scanner;
use crate::package_manager::{init_project, install_package, remove_package};
use crate::parser::Parser;
use crate::vm::VM;
use colored::Colorize;
use std::fs;
use std::io::{self, Write};
use std::path::Path;
use std::time::Instant;

pub fn run_cli(args: Vec<String>) -> Result<(), i32> {
    if let Some(source) = check_embedded_executable() {
        let script_args = if args.len() > 1 {
            args[1..].to_vec()
        } else {
            Vec::new()
        };
        let exe_name = args.get(0).cloned().unwrap_or_else(|| "<standalone>".to_string());
        return execute_source(&source, &exe_name, script_args);
    }

    if args.len() <= 1 {
        print_help();
        return Ok(());
    }

    let command = args[1].as_str();

    match command {
        "-v" | "--version" | "version" => {
            println!("Lyslyn v2.0.0 (Rust Native VM)");
            Ok(())
        }
        "-h" | "--help" | "help" => {
            print_help();
            Ok(())
        }
        "-c" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing code string after -c".red());
                eprintln!("Usage: lyslyn -c '<code>'");
                return Err(1);
            }
            execute_source(&args[2], "<command_line>", args[3..].to_vec())
        }
        "run" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing filename to run".red());
                eprintln!("Usage: lyslyn run <file.lys>");
                return Err(1);
            }
            let filename = &args[2];
            let script_args: Vec<String> = args[3..].to_vec();
            execute_file(filename, script_args)
        }
        "compile" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing filename to compile".red());
                eprintln!("Usage: lyslyn compile <file.lys> [-o binary_name]");
                return Err(1);
            }
            let filename = &args[2];
            let default_out = filename.trim_end_matches(".lys").to_string();
            let out_path = args
                .iter()
                .position(|a| a == "-o")
                .and_then(|idx| args.get(idx + 1))
                .map(|s| s.as_str())
                .unwrap_or(&default_out);
            compile_standalone(filename, out_path)
        }
        "check" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing filename to check".red());
                eprintln!("Usage: lyslyn check <file.lys>");
                return Err(1);
            }
            check_file(&args[2])
        }
        "build" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing filename to build".red());
                eprintln!("Usage: lyslyn build <file.lys> [-o output.lysc] [--standalone]");
                return Err(1);
            }
            if args.contains(&"--standalone".to_string()) {
                let default_out = args[2].trim_end_matches(".lys").to_string();
                let out_path = args
                    .iter()
                    .position(|a| a == "-o")
                    .and_then(|idx| args.get(idx + 1))
                    .map(|s| s.as_str())
                    .unwrap_or(&default_out);
                compile_standalone(&args[2], out_path)
            } else {
                build_file(&args[2], args.get(4).map(|s| s.as_str()))
            }
        }
        "disasm" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing filename to disassemble".red());
                eprintln!("Usage: lyslyn disasm <file.lys>");
                return Err(1);
            }
            disassemble_file(&args[2])
        }
        "bench" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing filename to benchmark".red());
                eprintln!("Usage: lyslyn bench <file.lys> [-n iterations]");
                return Err(1);
            }
            let iterations = args
                .iter()
                .position(|a| a == "-n")
                .and_then(|idx| args.get(idx + 1))
                .and_then(|val| val.parse::<usize>().ok())
                .unwrap_or(10);
            benchmark_file(&args[2], iterations)
        }
        "repl" => run_repl(),
        "test" => run_test_suite(),
        "init" => {
            let name = args.get(2).map(|s| s.as_str()).unwrap_or("my_lyslyn_app");
            init_project(name).map_err(|e| {
                eprintln!("{}", e.red());
                1
            })
        }
        "install" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing package name".red());
                eprintln!("Usage: lyslyn install <package_name>");
                return Err(1);
            }
            install_package(&args[2]).map_err(|e| {
                eprintln!("{}", e.red());
                1
            })
        }
        "remove" => {
            if args.len() < 3 {
                eprintln!("{}", "Error: Missing package name".red());
                eprintln!("Usage: lyslyn remove <package_name>");
                return Err(1);
            }
            remove_package(&args[2]).map_err(|e| {
                eprintln!("{}", e.red());
                1
            })
        }
        path if path.ends_with(".lys") || Path::new(path).exists() => {
            let script_args: Vec<String> = args[2..].to_vec();
            execute_file(path, script_args)
        }
        _ => {
            eprintln!("{}: Unknown command or file '{}'", "Error".red(), command);
            print_help();
            Err(1)
        }
    }
}

pub fn execute_file(filename: &str, script_args: Vec<String>) -> Result<(), i32> {
    let source = fs::read_to_string(filename).map_err(|e| {
        eprintln!(
            "{}: Failed to read file '{}': {}",
            "File Error".red().bold(),
            filename,
            e
        );
        1
    })?;

    execute_source(&source, filename, script_args)
}

pub fn execute_source(source: &str, filename: &str, script_args: Vec<String>) -> Result<(), i32> {
    let mut scanner = Scanner::new(source, filename);
    let tokens = scanner.scan_tokens().map_err(|err| {
        eprintln!("{}", err.format_diagnostic().red());
        1
    })?;

    let mut parser = Parser::new(tokens, filename, source);
    let program = parser.parse().map_err(|err| {
        eprintln!("{}", err.format_diagnostic().red());
        1
    })?;

    let mut compiler = Compiler::new(filename, source);
    let chunk = compiler.compile(&program).map_err(|err| {
        eprintln!("{}", err.format_diagnostic().red());
        1
    })?;

    let mut vm = VM::new(Some(script_args));
    if let Some(parent) = Path::new(filename).parent() {
        vm.module_loader.add_search_path(parent.to_path_buf());
    }

    vm.run(chunk).map_err(|err| {
        eprintln!("{}", err.format_diagnostic().red());
        1
    })?;

    Ok(())
}

pub fn check_file(filename: &str) -> Result<(), i32> {
    let source = fs::read_to_string(filename).map_err(|e| {
        eprintln!("{}: Cannot read file '{}': {}", "Error".red(), filename, e);
        1
    })?;

    let mut scanner = Scanner::new(&source, filename);
    let tokens = scanner.scan_tokens().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut parser = Parser::new(tokens, filename, &source);
    let program = parser.parse().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut compiler = Compiler::new(filename, &source);
    let _ = compiler.compile(&program).map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    println!(
        "{} Check passed for '{}' ({} statements).",
        "✓".green().bold(),
        filename,
        program.statements.len()
    );
    Ok(())
}

pub fn build_file(filename: &str, out_path: Option<&str>) -> Result<(), i32> {
    let source = fs::read_to_string(filename).map_err(|e| {
        eprintln!("{}: Cannot read file '{}': {}", "Error".red(), filename, e);
        1
    })?;

    let mut scanner = Scanner::new(&source, filename);
    let tokens = scanner.scan_tokens().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut parser = Parser::new(tokens, filename, &source);
    let program = parser.parse().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut compiler = Compiler::new(filename, &source);
    let chunk = compiler.compile(&program).map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let default_out = format!("{}.lysc", filename.trim_end_matches(".lys"));
    let final_out = out_path.unwrap_or(&default_out);

    fs::write(final_out, &chunk.code).map_err(|e| {
        eprintln!("{}: Cannot write output '{}': {}", "Error".red(), final_out, e);
        1
    })?;

    println!(
        "{} Successfully compiled '{}' to bytecode '{}' ({} bytes, {} instructions)",
        "✓".green().bold(),
        filename,
        final_out,
        chunk.code.len(),
        chunk.lines.len()
    );
    Ok(())
}

pub fn disassemble_file(filename: &str) -> Result<(), i32> {
    let source = fs::read_to_string(filename).map_err(|e| {
        eprintln!("{}: Cannot read file '{}': {}", "Error".red(), filename, e);
        1
    })?;

    let mut scanner = Scanner::new(&source, filename);
    let tokens = scanner.scan_tokens().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut parser = Parser::new(tokens, filename, &source);
    let program = parser.parse().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut compiler = Compiler::new(filename, &source);
    let chunk = compiler.compile(&program).map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    println!("{}", chunk.disassemble(Some(filename)));
    Ok(())
}

pub fn benchmark_file(filename: &str, iterations: usize) -> Result<(), i32> {
    let source = fs::read_to_string(filename).map_err(|e| {
        eprintln!("{}: Cannot read file '{}': {}", "Error".red(), filename, e);
        1
    })?;

    let mut scanner = Scanner::new(&source, filename);
    let tokens = scanner.scan_tokens().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut parser = Parser::new(tokens, filename, &source);
    let program = parser.parse().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut compiler = Compiler::new(filename, &source);
    let chunk = compiler.compile(&program).map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    println!(
        "{} Benchmarking '{}' over {} iterations...",
        "⚡".yellow().bold(),
        filename,
        iterations
    );

    let mut durations: Vec<std::time::Duration> = Vec::with_capacity(iterations);
    for _ in 0..iterations {
        let mut vm = VM::new(None);
        if let Some(parent) = Path::new(filename).parent() {
            vm.module_loader.add_search_path(parent.to_path_buf());
        }
        let start = Instant::now();
        let _ = vm.run(chunk.clone()).map_err(|e| {
            eprintln!("{}", e.format_diagnostic().red());
            1
        })?;
        durations.push(start.elapsed());
    }

    let total: std::time::Duration = durations.iter().sum();
    let avg = total / iterations as u32;
    let min = durations.iter().min().cloned().unwrap_or_default();
    let max = durations.iter().max().cloned().unwrap_or_default();
    let ops_per_sec = 1_000_000.0 / avg.as_micros().max(1) as f64;

    println!("  • Iterations: {}", iterations);
    println!("  • Average:    {:.2?}", avg);
    println!("  • Min:        {:.2?}", min);
    println!("  • Max:        {:.2?}", max);
    println!("  • Throughput: {:.1} runs/sec", ops_per_sec);
    Ok(())
}

pub fn run_repl() -> Result<(), i32> {
    println!("{}", "Lyslyn 2.0.0 Interactive REPL".cyan().bold());
    println!("Type 'exit' to quit. Multiline blocks use 4-space indentation.\n");

    let mut vm = VM::new(None);
    let stdin = io::stdin();
    let mut buffer = String::new();

    loop {
        if buffer.is_empty() {
            print!("lyslyn> ");
        } else {
            print!("    ... ");
        }
        let _ = io::stdout().flush();

        let mut line = String::new();
        if stdin.read_line(&mut line).unwrap_or(0) == 0 {
            break;
        }

        let trimmed = line.trim();
        if trimmed == "exit" || trimmed == "quit" {
            break;
        }

        buffer.push_str(&line);

        if trimmed.ends_with(':') {
            continue;
        }

        let source = buffer.clone();
        buffer.clear();

        let mut scanner = Scanner::new(&source, "<repl>");
        let tokens = match scanner.scan_tokens() {
            Ok(t) => t,
            Err(e) => {
                eprintln!("{}", e.format_diagnostic().red());
                continue;
            }
        };

        let mut parser = Parser::new(tokens, "<repl>", &source);
        let program = match parser.parse() {
            Ok(p) => p,
            Err(e) => {
                eprintln!("{}", e.format_diagnostic().red());
                continue;
            }
        };

        let mut compiler = Compiler::new("<repl>", &source);
        let chunk = match compiler.compile(&program) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("{}", e.format_diagnostic().red());
                continue;
            }
        };

        match vm.run(chunk) {
            Ok(val) => {
                if val != crate::values::Value::Nil {
                    println!("{}", format!("{}", val).green());
                }
            }
            Err(e) => {
                eprintln!("{}", e.format_diagnostic().red());
            }
        }
    }

    println!("\nExiting Lyslyn REPL.");
    Ok(())
}

pub fn run_test_suite() -> Result<(), i32> {
    println!(
        "\n┌──────────────────────────────────────────────────────────────┐\n│            LYSLYN NATIVE RUST TEST SUITE RUNNER              │\n└──────────────────────────────────────────────────────────────┘\n"
    );

    let mut total = 0;
    let mut passed = 0;
    let mut failed = 0;

    let test_files = vec![
        "tests/test_basics.lys",
        "tests/test_control_flow.lys",
        "tests/test_functions.lys",
        "tests/test_collections.lys",
        "tests/test_simple_english.lys",
        "tests/test_jwt_cache_collections.lys",
        "tests/test_stdlib.lys",
        "tests/test_errors.lys",
        "tests/test_db.lys",
        "tests/test_backend_security.lys",
        "tests/test_oop_and_industrial.lys",
    ];

    let overall_start = Instant::now();

    for test_file in test_files {
        if !Path::new(test_file).exists() {
            continue;
        }

        total += 1;
        let start = Instant::now();
        let res = execute_file(test_file, Vec::new());
        let duration = start.elapsed();

        if res.is_ok() {
            passed += 1;
            println!(
                "  • {:<40} {} ({:.1}ms)",
                test_file,
                "✓ PASSED".green().bold(),
                duration.as_secs_f64() * 1000.0
            );
        } else {
            failed += 1;
            println!(
                "  • {:<40} {} ({:.1}ms)",
                test_file,
                "✗ FAILED".red().bold(),
                duration.as_secs_f64() * 1000.0
            );
        }
    }

    let elapsed = overall_start.elapsed();
    println!(
        "\n┌──────────────────────────────────────────────────────────────┐\n│  Results: {} passed, {} failed out of {} total ({:.1}ms)     │\n└──────────────────────────────────────────────────────────────┘\n",
        passed,
        failed,
        total,
        elapsed.as_secs_f64() * 1000.0
    );

    if failed > 0 {
        Err(1)
    } else {
        Ok(())
    }
}

pub fn check_embedded_executable() -> Option<String> {
    let exe_path = std::env::current_exe().ok()?;
    let data = fs::read(&exe_path).ok()?;
    let magic = b"LYSLYN_EMBEDDED_V1\n";
    if data.len() < magic.len() + 8 {
        return None;
    }
    let footer_start = data.len() - magic.len() - 8;
    if &data[data.len() - magic.len()..] == magic {
        let len_bytes: [u8; 8] = data[footer_start..footer_start + 8].try_into().ok()?;
        let source_len = u64::from_be_bytes(len_bytes) as usize;
        if footer_start >= source_len {
            let source_start = footer_start - source_len;
            let source_bytes = &data[source_start..footer_start];
            return String::from_utf8(source_bytes.to_vec()).ok();
        }
    }
    None
}

fn get_base_executable() -> Result<Vec<u8>, String> {
    if let Ok(exe_path) = std::env::current_exe() {
        if let Ok(bytes) = fs::read(&exe_path) {
            let magic = b"LYSLYN_EMBEDDED_V1\n";
            if bytes.len() >= magic.len() + 8 && &bytes[bytes.len() - magic.len()..] == magic {
                let footer_start = bytes.len() - magic.len() - 8;
                let len_bytes: [u8; 8] = bytes[footer_start..footer_start + 8]
                    .try_into()
                    .unwrap_or([0; 8]);
                let source_len = u64::from_be_bytes(len_bytes) as usize;
                if footer_start >= source_len {
                    return Ok(bytes[..footer_start - source_len].to_vec());
                }
            }
            return Ok(bytes);
        }
    }
    if let Ok(home) = std::env::var("HOME") {
        let candidate = Path::new(&home).join(".local/bin/lyslyn");
        if let Ok(bytes) = fs::read(&candidate) {
            return Ok(bytes);
        }
        let candidate2 = Path::new(&home).join(".cargo_target/lyslyn/release/lyslyn");
        if let Ok(bytes) = fs::read(&candidate2) {
            return Ok(bytes);
        }
    }
    Err("Could not locate lyslyn base executable".to_string())
}

pub fn compile_standalone(filename: &str, out_path: &str) -> Result<(), i32> {
    let source = fs::read_to_string(filename).map_err(|e| {
        eprintln!("{}: Cannot read file '{}': {}", "Error".red(), filename, e);
        1
    })?;

    let mut scanner = Scanner::new(&source, filename);
    let tokens = scanner.scan_tokens().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut parser = Parser::new(tokens, filename, &source);
    let program = parser.parse().map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut compiler = Compiler::new(filename, &source);
    let _ = compiler.compile(&program).map_err(|e| {
        eprintln!("{}", e.format_diagnostic().red());
        1
    })?;

    let mut binary_bytes = get_base_executable().map_err(|e| {
        eprintln!("{}: {}", "Error".red(), e);
        1
    })?;

    let source_bytes = source.as_bytes();
    let source_len = source_bytes.len() as u64;
    let len_bytes = source_len.to_be_bytes();
    let magic = b"LYSLYN_EMBEDDED_V1\n";

    binary_bytes.extend_from_slice(source_bytes);
    binary_bytes.extend_from_slice(&len_bytes);
    binary_bytes.extend_from_slice(magic);

    fs::write(out_path, &binary_bytes).map_err(|e| {
        eprintln!("{}: Cannot write output binary '{}': {}", "Error".red(), out_path, e);
        1
    })?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        if let Ok(metadata) = fs::metadata(out_path) {
            let mut perms = metadata.permissions();
            perms.set_mode(0o755);
            let _ = fs::set_permissions(out_path, perms);
        }
    }

    println!(
        "{} Successfully compiled standalone native executable '{}' ({} bytes)",
        "✓".green().bold(),
        out_path,
        binary_bytes.len()
    );
    Ok(())
}

fn print_help() {
    println!(
        "{} - The Simple-English Systems Programming Language\n",
        "Lyslyn 2.0 (Native Rust Engine)".cyan().bold()
    );
    println!("Usage:");
    println!("  lyslyn <file.lys> [args...]       Execute a Lyslyn script directly");
    println!("  lyslyn run <file.lys> [args...]   Execute a Lyslyn script");
    println!("  lyslyn compile <file.lys> [-o out] Compile to standalone native executable");
    println!("  lyslyn -c '<code>'                Execute inline code string");
    println!("  lyslyn check <file.lys>           Parse and statically check a script");
    println!("  lyslyn build <file.lys>           Compile to binary bytecode (.lysc)");
    println!("  lyslyn disasm <file.lys>          Disassemble to human-readable bytecode");
    println!("  lyslyn bench <file.lys> [-n N]    Benchmark execution latency & throughput");
    println!("  lyslyn repl                       Start the interactive REPL");
    println!("  lyslyn test                       Run all tests in tests/ directory");
    println!("  lyslyn init [name]                Initialize a new Lyslyn project");
    println!("  lyslyn install <package>          Install a dependency in lyslyn.toml");
    println!("  lyslyn remove <package>           Remove a dependency from lyslyn.toml");
    println!("  lyslyn --version                  Show version information");
    println!("  lyslyn --help                     Show this help message\n");
}
