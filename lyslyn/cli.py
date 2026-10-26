"""Command Line Interface for the Lyslyn Industrial Toolchain."""
import os
import sys
import json
import time
import difflib
import argparse
from typing import List, Optional
from .lexer import Lexer
from .parser import Parser
from .semantics import SemanticAnalyzer
from .interpreter import Interpreter
from .compiler import Compiler
from .chunk import Chunk
from .vm import VM
from .linter import Linter
from .bench import run_benchmark, print_benchmark_table
from .docgen import extract_docs, generate_markdown_doc
from .pm import PackageManager
from .diagnostics import LyslynError
from .formatter import format_source, generate_diff
from .repl import start_repl

VERSION = "2.0.0 — Industrial Edition"


def cmd_run(args: argparse.Namespace) -> int:
    filepath = args.file
    if os.path.isdir(filepath):
        print(f"\033[91m✖ Error\033[0m: '{filepath}' is a directory, not a Lyslyn file.", file=sys.stderr)
        return 1

    if not os.path.isfile(filepath):
        print(f"\033[91m✖ Error\033[0m: File '{filepath}' does not exist.")
        return 1

    script_args = getattr(args, "script_args", []) or []

    try:
        # Check if pre-compiled bytecode .lysc
        if filepath.endswith(".lysc"):
            with open(filepath, "rb") as f:
                bytecode_data = f.read()
            chunk = Chunk.deserialize(bytecode_data)
            vm = VM(script_args=script_args)
            vm.run(chunk)
            return 0

        # Standard source execution
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()

        parser = Parser(tokens, filename=filepath, source=source)
        program = parser.parse()

        analyzer = SemanticAnalyzer(filename=filepath, source=source)
        analyzer.analyze(program)

        interp = Interpreter(filename=filepath, source=source)
        interp.globals.define("args", script_args, is_constant=True)

        interp.interpret(program)
        return 0

    except LyslynError as e:
        print(e.format_diagnostic(color=True), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\033[91m✖ Runtime Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_eval(code: str, script_args: Optional[List[str]] = None) -> int:
    script_args = script_args or []
    try:
        lexer = Lexer(code, filename="<string>")
        tokens = lexer.tokenize()

        parser = Parser(tokens, filename="<string>", source=code)
        program = parser.parse()

        analyzer = SemanticAnalyzer(filename="<string>", source=code)
        analyzer.analyze(program)

        interp = Interpreter(filename="<string>", source=code)
        interp.globals.define("args", script_args, is_constant=True)

        interp.interpret(program)
        return 0

    except LyslynError as e:
        print(e.format_diagnostic(color=True), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\033[91m✖ Runtime Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_compile(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91m✖ Error\033[0m: File '{filepath}' does not exist.")
        return 1

    output_path = args.output or os.path.splitext(filepath)[0] + ".lysc"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()

        parser = Parser(tokens, filename=filepath, source=source)
        program = parser.parse()

        analyzer = SemanticAnalyzer(filename=filepath, source=source)
        analyzer.analyze(program)

        compiler = Compiler(filename=filepath, source=source)
        chunk = compiler.compile(program)

        data = chunk.serialize()
        with open(output_path, "wb") as f:
            f.write(data)

        print(f"\033[92m✓\033[0m Compiled '\033[1m{filepath}\033[0m' -> '\033[96m{output_path}\033[0m' ({len(data)} bytes, {len(chunk.code)} opcodes).")
        return 0

    except LyslynError as e:
        print(e.format_diagnostic(color=True), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\033[91m✖ Compilation Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_disasm(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91m✖ Error\033[0m: File '{filepath}' does not exist.")
        return 1

    try:
        if filepath.endswith(".lysc"):
            with open(filepath, "rb") as f:
                chunk = Chunk.deserialize(f.read())
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tokens = Lexer(source, filename=filepath).tokenize()
            program = Parser(tokens, filename=filepath, source=source).parse()
            compiler = Compiler(filename=filepath, source=source)
            chunk = compiler.compile(program)

        print(chunk.disassemble(os.path.basename(filepath)))
        return 0

    except Exception as e:
        print(f"\033[91m✖ Disassembly Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_lint(args: argparse.Namespace) -> int:
    target = args.path or "."
    files_to_lint: List[str] = []

    if os.path.isfile(target):
        files_to_lint = [target]
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            if any(part.startswith(".") and part not in (".", "..") or part == "__pycache__" for part in root.split(os.sep)):
                continue
            for f in sorted(files):
                if f.endswith(".lys"):
                    files_to_lint.append(os.path.join(root, f))

    if not files_to_lint:
        print(f"No Lyslyn files found to lint in '{target}'.")
        return 0

    total_warnings = 0
    for f in files_to_lint:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                source = fp.read()
            tokens = Lexer(source, filename=f).tokenize()
            program = Parser(tokens, filename=f, source=source).parse()
            linter = Linter(filename=f, source=source)
            warnings = linter.lint(program)
            if warnings:
                print(linter.format_warnings())
                total_warnings += len(warnings)
        except Exception as e:
            print(f"\033[91m✖ Lint Error in {f}\033[0m: {e}")

    if total_warnings == 0:
        print(f"\033[92m✓\033[0m All {len(files_to_lint)} file(s) passed static analysis cleanly.")
        return 0
    return 1


def cmd_bench(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91m✖ Error\033[0m: Benchmark target '{filepath}' does not exist.")
        return 1

    try:
        results = run_benchmark(filepath, iterations=args.iterations)
        print_benchmark_table(results, filepath)
        return 0
    except Exception as e:
        print(f"\033[91m✖ Benchmark Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_doc(args: argparse.Namespace) -> int:
    target = args.path or "."
    files = [target] if os.path.isfile(target) else [
        os.path.join(root, f) for root, _, fs in os.walk(target) for f in fs if f.endswith(".lys")
    ]

    for f in files:
        try:
            items = extract_docs(f)
            md = generate_markdown_doc(f, items)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as out:
                    out.write(md)
                print(f"\033[92m✓\033[0m Wrote documentation to {args.output}")
            else:
                print(md)
        except Exception as e:
            print(f"\033[91m✖ Doc Generation Error\033[0m: {e}", file=sys.stderr)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91m✖ Error\033[0m: File '{filepath}' does not exist.")
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tokens = Lexer(source, filename=filepath).tokenize()
        program = Parser(tokens, filename=filepath, source=source).parse()

        analyzer = SemanticAnalyzer(filename=filepath, source=source)
        analyzer.analyze(program)

        print(f"\033[92m✓\033[0m \033[1mCheck passed\033[0m for '\033[96m{filepath}\033[0m' ({len(program.statements)} statements).")
        return 0

    except LyslynError as e:
        print(e.format_diagnostic(color=True), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\033[91m✖ Check Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_format(args: argparse.Namespace) -> int:
    target = args.path or "."
    files_to_format: List[str] = []

    if os.path.isfile(target):
        files_to_format = [target]
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            if any(part.startswith(".") and part not in (".", "..") or part == "__pycache__" for part in root.split(os.sep)):
                continue
            for f in sorted(files):
                if f.endswith(".lys"):
                    files_to_format.append(os.path.join(root, f))

    if not files_to_format:
        print(f"No Lyslyn (.lys) files found in '{target}'.")
        return 0

    changed_count = 0
    clean_count = 0

    for filepath in files_to_format:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                original = f.read()

            beautified = format_source(original)
            is_different = (original != beautified)

            if args.diff:
                diff = generate_diff(original, beautified, filepath)
                if diff:
                    sys.stdout.write(diff)
                    changed_count += 1
                else:
                    clean_count += 1

            elif args.check:
                if is_different:
                    print(f"  \033[93m⚠ Needs formatting:\033[0m {filepath}")
                    changed_count += 1
                else:
                    clean_count += 1

            elif args.write:
                if is_different:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(beautified)
                    print(f"  \033[92m✓ Beautified:\033[0m {filepath}")
                    changed_count += 1
                else:
                    print(f"  \033[90m• Unchanged:\033[0m {filepath}")
                    clean_count += 1
            else:
                if len(files_to_format) == 1:
                    sys.stdout.write(beautified)
                    return 0
                else:
                    if is_different:
                        print(f"  \033[93m⚠ Needs formatting:\033[0m {filepath} (run with -w to write)")
                        changed_count += 1
                    else:
                        print(f"  \033[90m• Formatted:\033[0m {filepath}")
                        clean_count += 1

        except Exception as e:
            print(f"\033[91m✖ Error formatting '{filepath}'\033[0m: {e}", file=sys.stderr)
            return 1

    if args.check:
        if changed_count > 0:
            print(f"\n\033[93m✖ {changed_count} file(s) need formatting.\033[0m Run 'lys format -w' to format.")
            return 1
        else:
            print(f"\n\033[92m✓ All {clean_count} file(s) are properly formatted.\033[0m")
            return 0

    if args.write:
        print(f"\n\033[1mFormatting Complete:\033[0m \033[92m{changed_count} beautified\033[0m, \033[90m{clean_count} unchanged\033[0m.")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    target_path = args.path or "."
    test_files: List[str] = []

    if os.path.isfile(target_path):
        test_files = [target_path]
    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            if any(part.startswith(".") and part not in (".", "..") or part == "__pycache__" for part in root.split(os.sep)):
                continue
            for file in sorted(files):
                if file.endswith(".lys") and (file.startswith("test_") or file.endswith("_test.lys")):
                    test_files.append(os.path.join(root, file))

    if not test_files:
        print(f"No Lyslyn test files found in '{target_path}'.")
        return 0

    print("\n\033[1m┌──────────────────────────────────────────────────────────────┐\033[0m")
    print("\033[1m│                   LYSLYN TEST SUITE RUNNER                   │\033[0m")
    print("\033[1m└──────────────────────────────────────────────────────────────┘\033[0m\n")

    passed = 0
    failed = 0
    total_start = time.perf_counter()

    for test_file in test_files:
        display_name = os.path.relpath(test_file)
        sys.stdout.write(f"  • {display_name:<40} ")
        sys.stdout.flush()

        start_time = time.perf_counter()
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                source = f.read()

            tokens = Lexer(source, filename=test_file).tokenize()
            program = Parser(tokens, filename=test_file, source=source).parse()

            analyzer = SemanticAnalyzer(filename=test_file, source=source)
            analyzer.analyze(program)

            interp = Interpreter(filename=test_file, source=source)
            interp.interpret(program)

            duration_ms = (time.perf_counter() - start_time) * 1000
            print(f"\033[92m✓ PASSED\033[0m \033[90m({duration_ms:.1f}ms)\033[0m")
            passed += 1

        except LyslynError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            print(f"\033[91m✖ FAILED\033[0m \033[90m({duration_ms:.1f}ms)\033[0m")
            print(e.format_diagnostic(color=True), file=sys.stderr)
            failed += 1
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            print(f"\033[91m✖ FAILED\033[0m \033[90m({duration_ms:.1f}ms)\033[0m")
            print(f"    \033[91mError\033[0m: {e}\n", file=sys.stderr)
            failed += 1

    total_duration_ms = (time.perf_counter() - total_start) * 1000
    status_color = "\033[92m" if failed == 0 else "\033[91m"
    print("\n\033[1m┌──────────────────────────────────────────────────────────────┐\033[0m")
    summary_text = f"Results: {passed} passed, {failed} failed out of {len(test_files)} total ({total_duration_ms:.1f}ms)"
    print(f"\033[1m│  {status_color}{summary_text:<58}\033[0m\033[1m│\033[0m")
    print("\033[1m└──────────────────────────────────────────────────────────────┘\033[0m\n")

    return 0 if failed == 0 else 1


def cmd_init(args: argparse.Namespace) -> int:
    project_dir = args.name
    if os.path.exists(project_dir):
        print(f"\033[91m✖ Error\033[0m: Directory '{project_dir}' already exists.")
        return 1

    os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)

    manifest = {
        "name": project_dir,
        "version": "1.0.0",
        "description": f"Industrial Lyslyn backend service: {project_dir}",
        "main": "main.lys",
        "scripts": {
            "start": "lys run main.lys",
            "test": "lys test",
            "lint": "lys lint",
            "format": "lys format -w",
            "build": "lys compile main.lys"
        },
        "dependencies": {},
        "devDependencies": {}
    }
    with open(os.path.join(project_dir, "lyslyn.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    main_code = """# Welcome to your industrial Lyslyn service!

Import server
Import db

db.connect("./app.db")

Serve HTTP on port 8080:
    Use middleware server.cors("*")
    Use middleware server.logger()

    Route GET "/health":
        Respond with status 200 and json {"status": "healthy"}

    Route GET "/":
        Respond with status 200 and json {
            "message": "Welcome to {project_name}!",
            "version": "1.0.0"
        }
""".replace("{project_name}", project_dir)

    with open(os.path.join(project_dir, "main.lys"), "w", encoding="utf-8") as f:
        f.write(main_code)

    test_code = """# Test suite for project
Create a function called add with a, b:
    Return a + b

Assert(add(2, 3) is equal to 5, "Addition test")
Assert(add(-1, 1) is equal to 0, "Zero sum test")
"""
    with open(os.path.join(project_dir, "tests", "test_main.lys"), "w", encoding="utf-8") as f:
        f.write(test_code)

    print(f"\033[92m✓\033[0m Initialized new industrial Lyslyn project in \033[1m\033[96m{project_dir}/\033[0m")
    print(f"  cd {project_dir}")
    print("  lys run main.lys")
    return 0


# ============================================================================
# Package Manager Commands
# ============================================================================

def cmd_pm_add(args: argparse.Namespace) -> int:
    pm = PackageManager()
    pm.add_package(args.package, args.pkg_version, is_dev=args.dev)
    return 0

def cmd_pm_remove(args: argparse.Namespace) -> int:
    pm = PackageManager()
    pm.remove_package(args.package)
    return 0

def cmd_pm_install(args: argparse.Namespace) -> int:
    pm = PackageManager()
    pm.install()
    return 0

def cmd_pm_pack(args: argparse.Namespace) -> int:
    pm = PackageManager()
    pm.pack(args.output)
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    from .watcher import watch_file
    watch_file(args.file, getattr(args, "script_args", []))
    return 0


def cmd_bundle(args: argparse.Namespace) -> int:
    from .bundler import bundle_project
    bundle_project(args.file, args.output)
    return 0


KNOWN_SUBCOMMANDS = {
    "run", "watch", "bundle", "compile", "disasm", "lint", "bench", "doc", "check",
    "format", "test", "init", "add", "remove", "install", "pack", "repl"
}

COMMON_ALIASES = {
    "fmt": "format",
    "b": "bench",
    "c": "compile",
    "d": "disasm",
    "t": "test",
    "r": "run",
    "chk": "check",
    "w": "watch",
    "bun": "bundle",
}


def main() -> None:
    invoked_name = os.path.basename(sys.argv[0]) if sys.argv else "lyslyn"
    prog_name = "lys" if invoked_name in ("lys", "lys.py") else "lyslyn"

    # 1. No arguments provided -> launch interactive REPL (just like `python`)
    if len(sys.argv) <= 1:
        start_repl()
        return

    first_arg = sys.argv[1]

    # 2. Version flag
    if first_arg in ("-v", "-V", "--version"):
        print(f"Lyslyn {VERSION}")
        sys.exit(0)

    # 3. Inline code snippet (-c "code") (just like `python -c`)
    if first_arg == "-c":
        if len(sys.argv) < 3:
            print(f"{prog_name}: error: option -c requires an argument", file=sys.stderr)
            sys.exit(2)
        code = sys.argv[2]
        script_args = sys.argv[3:]
        sys.exit(cmd_eval(code, script_args))

    # 4. Watch flag (--watch <file> or <file> --watch)
    if "--watch" in sys.argv:
        argv_clean = [a for a in sys.argv[1:] if a != "--watch"]
        if not argv_clean:
            print(f"{prog_name}: error: --watch requires a file to monitor", file=sys.stderr)
            sys.exit(2)
        target = argv_clean[0]
        script_args = argv_clean[1:]
        from .watcher import watch_file
        watch_file(target, script_args)
        return

    # 4. If first argument is NOT a subcommand and does NOT start with '-',
    # it is a script file to execute directly (just like `python script.py [args...]`)
    if first_arg not in KNOWN_SUBCOMMANDS and not first_arg.startswith("-"):
        target = first_arg
        if os.path.isdir(target):
            print(f"\033[91m✖ Error\033[0m: '{target}' is a directory, not a Lyslyn source file.", file=sys.stderr)
            sys.exit(1)

        if not os.path.isfile(target):
            print(f"\033[91m✖ Error\033[0m: File '{target}' does not exist.", file=sys.stderr)
            suggestion = COMMON_ALIASES.get(target)
            if not suggestion:
                matches = difflib.get_close_matches(target, list(KNOWN_SUBCOMMANDS), n=1, cutoff=0.6)
                if matches:
                    suggestion = matches[0]
            if suggestion:
                print(f"\033[93m💡 Did you mean:\033[0m {prog_name} {suggestion}?")
            sys.exit(1)

        # File exists: Execute immediately with all subsequent arguments passed through
        script_args = sys.argv[2:]
        run_args = argparse.Namespace(file=target, script_args=script_args)
        sys.exit(cmd_run(run_args))

    # 5. Standard argparse subcommands & help handling
    parser = argparse.ArgumentParser(
        prog=prog_name,
        usage=f"{prog_name} [file.lys | -c 'code' | command] [args...]",
        description=(
            "Lyslyn: The Industrial English-Structured Programming Language Toolchain\n\n"
            "Execution patterns (just like Python):\n"
            f"  {prog_name} script.lys [args...]          Run a Lyslyn source script directly\n"
            f"  {prog_name} script.lysc [args...]         Run compiled bytecode directly\n"
            f"  {prog_name} -c '<code>' [args...]         Execute inline Lyslyn code snippet\n"
            f"  {prog_name}                              Start interactive REPL session\n"
            f"  {prog_name} <command> [options]          Run developer toolchain commands"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", "-v", action="version", version=f"Lyslyn {VERSION}")
    parser.add_argument("-c", dest="command_code", metavar="CODE", help="Execute inline code string")

    subparsers = parser.add_subparsers(dest="command", help="Available industrial commands")

    # run
    run_parser = subparsers.add_parser("run", help="Run a Lyslyn source file or compiled .lysc bytecode")
    run_parser.add_argument("file", help="Path to .lys source file or .lysc bytecode")
    run_parser.add_argument("script_args", nargs="*", help="Arguments passed to the script")

    # watch
    watch_parser = subparsers.add_parser("watch", help="Run a Lyslyn file in live watch mode with hot reloading")
    watch_parser.add_argument("file", help="Path to .lys source file to monitor")
    watch_parser.add_argument("script_args", nargs="*", help="Arguments passed to the script")

    # bundle
    bundle_parser = subparsers.add_parser("bundle", help="Inline all local dependencies into a single distribution file")
    bundle_parser.add_argument("file", help="Entry .lys source file")
    bundle_parser.add_argument("-o", "--output", default="bundle.lys", help="Output bundled filename (default: bundle.lys)")

    # compile
    compile_parser = subparsers.add_parser("compile", help="Compile .lys source code into binary bytecode (.lysc)")
    compile_parser.add_argument("file", help="Path to .lys source file")
    compile_parser.add_argument("-o", "--output", help="Output .lysc file path")

    # disasm
    disasm_parser = subparsers.add_parser("disasm", help="Disassemble Lyslyn source code or compiled bytecode")
    disasm_parser.add_argument("file", help="Path to .lys source file or .lysc bytecode")

    # lint
    lint_parser = subparsers.add_parser("lint", help="Static analysis and lint checks for dead code, unused vars")
    lint_parser.add_argument("path", nargs="?", default=".", help="File or directory to lint")

    # bench
    bench_parser = subparsers.add_parser("bench", help="Run microbenchmarks with iteration and throughput reports")
    bench_parser.add_argument("file", help="Path to .lys benchmark file")
    bench_parser.add_argument("-n", "--iterations", type=int, default=100, help="Number of benchmark iterations")

    # doc
    doc_parser = subparsers.add_parser("doc", help="Generate API documentation from doc-comments")
    doc_parser.add_argument("path", nargs="?", default=".", help="File or directory to generate docs for")
    doc_parser.add_argument("-o", "--output", help="Write documentation to file")

    # check
    check_parser = subparsers.add_parser("check", help="Type-check and validate a Lyslyn file")
    check_parser.add_argument("file", help="Path to .lys source file")

    # format
    fmt_parser = subparsers.add_parser("format", help="Beautify and format Lyslyn source files")
    fmt_parser.add_argument("path", nargs="?", default=".", help="Path to .lys file or directory")
    fmt_parser.add_argument("-w", "--write", action="store_true", help="Write formatted code back in-place")
    fmt_parser.add_argument("--check", action="store_true", help="Check formatting without writing")
    fmt_parser.add_argument("--diff", action="store_true", help="Show colorized diff of formatting changes")

    # test
    test_parser = subparsers.add_parser("test", help="Run Lyslyn test suites")
    test_parser.add_argument("path", nargs="?", default="tests", help="Directory or file containing tests")

    # init
    init_parser = subparsers.add_parser("init", help="Scaffold a new Lyslyn project")
    init_parser.add_argument("name", help="Name of the new project directory")

    # Package Manager (add, remove, install, pack)
    add_parser = subparsers.add_parser("add", help="Add a dependency to lyslyn.json and update lockfile")
    add_parser.add_argument("package", help="Package name")
    add_parser.add_argument("pkg_version", nargs="?", default="1.0.0", help="Package version")
    add_parser.add_argument("--dev", action="store_true", help="Add to devDependencies")

    remove_parser = subparsers.add_parser("remove", help="Remove a dependency from lyslyn.json and lockfile")
    remove_parser.add_argument("package", help="Package name")

    subparsers.add_parser("install", help="Install all dependencies with integrity verification")

    pack_parser = subparsers.add_parser("pack", help="Bundle project into a distributable .lyspkg archive")
    pack_parser.add_argument("-o", "--output", help="Output package archive filename")

    # repl
    subparsers.add_parser("repl", help="Start the interactive Lyslyn REPL")

    args = parser.parse_args()

    if args.command is None:
        start_repl()
        return

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "watch":
        sys.exit(cmd_watch(args))
    elif args.command == "bundle":
        sys.exit(cmd_bundle(args))
    elif args.command == "compile":
        sys.exit(cmd_compile(args))
    elif args.command == "disasm":
        sys.exit(cmd_disasm(args))
    elif args.command == "lint":
        sys.exit(cmd_lint(args))
    elif args.command == "bench":
        sys.exit(cmd_bench(args))
    elif args.command == "doc":
        sys.exit(cmd_doc(args))
    elif args.command == "check":
        sys.exit(cmd_check(args))
    elif args.command == "format":
        sys.exit(cmd_format(args))
    elif args.command == "test":
        sys.exit(cmd_test(args))
    elif args.command == "init":
        sys.exit(cmd_init(args))
    elif args.command == "add":
        sys.exit(cmd_pm_add(args))
    elif args.command == "remove":
        sys.exit(cmd_pm_remove(args))
    elif args.command == "install":
        sys.exit(cmd_pm_install(args))
    elif args.command == "pack":
        sys.exit(cmd_pm_pack(args))
    elif args.command == "repl":
        start_repl()


if __name__ == "__main__":
    main()
