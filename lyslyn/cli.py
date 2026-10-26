"""Command Line Interface for the Lyslyn toolchain with rich terminal UI."""
import os
import sys
import json
import time
import argparse
from typing import List, Optional
from .lexer import Lexer
from .parser import Parser
from .semantics import SemanticAnalyzer
from .interpreter import Interpreter
from .diagnostics import LyslynError
from .formatter import format_source, generate_diff
from .repl import start_repl

VERSION = "1.1.0"


def cmd_run(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91m✖ Error\033[0m: File '{filepath}' does not exist.")
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()

        parser = Parser(tokens, filename=filepath, source=source)
        program = parser.parse()

        analyzer = SemanticAnalyzer(filename=filepath, source=source)
        analyzer.analyze(program)

        interp = Interpreter(filename=filepath, source=source)
        interp.globals.define("args", args.script_args, is_constant=True)

        interp.interpret(program)
        return 0

    except LyslynError as e:
        print(e.format_diagnostic(color=True), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\033[91m✖ Runtime Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_check(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91m✖ Error\033[0m: File '{filepath}' does not exist.")
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        lexer = Lexer(source, filename=filepath)
        tokens = lexer.tokenize()

        parser = Parser(tokens, filename=filepath, source=source)
        program = parser.parse()

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
            # Skip hidden directories (except current dir '.') and pycache
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
                # Single file to stdout if not writing
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
            print(f"\n\033[93m✖ {changed_count} file(s) need formatting.\033[0m Run 'lyslyn format -w' to format.")
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
            if any(part.startswith(".") or part == "__pycache__" for part in root.split(os.sep)):
                continue
            for file in sorted(files):
                if file.endswith(".lys") and (file.startswith("test_") or file.endswith("_test.lys")):
                    test_files.append(os.path.join(root, file))

    if not test_files:
        print(f"No Lyslyn test files found in '{target_path}'.")
        return 0

    # Header Box
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

            lexer = Lexer(source, filename=test_file)
            tokens = lexer.tokenize()

            parser = Parser(tokens, filename=test_file, source=source)
            program = parser.parse()

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

    # Summary Box
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
        "description": f"A production Lyslyn backend service: {project_dir}",
        "main": "main.lys",
        "scripts": {
            "start": "lyslyn run main.lys",
            "test": "lyslyn test",
            "format": "lyslyn format -w"
        }
    }
    with open(os.path.join(project_dir, "lyslyn.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    main_code = """# Welcome to your new Lyslyn project!

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
            "runtime": "Lyslyn 1.1 Backend Edition"
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

    print(f"\033[92m✓\033[0m Initialized new Lyslyn backend project in \033[1m\033[96m{project_dir}/\033[0m")
    print(f"  cd {project_dir}")
    print("  lyslyn run main.lys")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lyslyn",
        description="Lyslyn: The English-Structured Programming Language Toolchain",
    )
    parser.add_argument("--version", action="version", version=f"Lyslyn {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run
    run_parser = subparsers.add_parser("run", help="Run a Lyslyn program")
    run_parser.add_argument("file", help="Path to .lys source file")
    run_parser.add_argument("script_args", nargs="*", help="Arguments passed to the script")

    # check
    check_parser = subparsers.add_parser("check", help="Type-check and validate a Lyslyn file")
    check_parser.add_argument("file", help="Path to .lys source file")

    # format / beautify
    fmt_parser = subparsers.add_parser("format", help="Beautify and format Lyslyn source files")
    fmt_parser.add_argument("path", nargs="?", default=".", help="Path to .lys file or directory (default: current directory)")
    fmt_parser.add_argument("-w", "--write", action="store_true", help="Write formatted code back to file in-place")
    fmt_parser.add_argument("--check", action="store_true", help="Check if files are formatted without writing")
    fmt_parser.add_argument("--diff", action="store_true", help="Show colorized diff of formatting changes")

    # test
    test_parser = subparsers.add_parser("test", help="Run Lyslyn test suites")
    test_parser.add_argument("path", nargs="?", default="tests", help="Directory or file containing tests")

    # init
    init_parser = subparsers.add_parser("init", help="Scaffold a new Lyslyn project")
    init_parser.add_argument("name", help="Name of the new project directory")

    # repl
    subparsers.add_parser("repl", help="Start the interactive Lyslyn REPL")

    args = parser.parse_args()

    if args.command is None:
        start_repl()
        return

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "check":
        sys.exit(cmd_check(args))
    elif args.command == "format":
        sys.exit(cmd_format(args))
    elif args.command == "test":
        sys.exit(cmd_test(args))
    elif args.command == "init":
        sys.exit(cmd_init(args))
    elif args.command == "repl":
        start_repl()


if __name__ == "__main__":
    main()
