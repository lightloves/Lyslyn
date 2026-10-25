"""Command Line Interface for the Lyslyn toolchain."""
import os
import sys
import json
import argparse
from typing import List, Optional
from .lexer import Lexer
from .parser import Parser
from .semantics import SemanticAnalyzer
from .interpreter import Interpreter
from .diagnostics import LyslynError
from .formatter import format_source
from .repl import start_repl

VERSION = "1.0.0"


def cmd_run(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91mError\033[0m: File '{filepath}' does not exist.")
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
        # Expose CLI arguments in Lyslyn environment as 'args'
        interp.globals.define("args", args.script_args, is_constant=True)

        interp.interpret(program)
        return 0

    except LyslynError as e:
        print(e.format_diagnostic(color=True), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\033[91mRuntime Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_check(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91mError\033[0m: File '{filepath}' does not exist.")
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

        print(f"\033[92m✓\033[0m Syntax and semantic check passed for '{filepath}' ({len(program.statements)} statements).")
        return 0

    except LyslynError as e:
        print(e.format_diagnostic(color=True), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\033[91mCheck Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_format(args: argparse.Namespace) -> int:
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"\033[91mError\033[0m: File '{filepath}' does not exist.")
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        formatted = format_source(source)

        if args.write:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"\033[92m✓\033[0m Formatted '{filepath}'.")
        else:
            sys.stdout.write(formatted)
        return 0

    except Exception as e:
        print(f"\033[91mFormat Error\033[0m: {e}", file=sys.stderr)
        return 1


def cmd_test(args: argparse.Namespace) -> int:
    target_path = args.path or "."
    test_files: List[str] = []

    if os.path.isfile(target_path):
        test_files = [target_path]
    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for file in sorted(files):
                if file.endswith(".lys") and (file.startswith("test_") or file.endswith("_test.lys")):
                    test_files.append(os.path.join(root, file))

    if not test_files:
        print(f"No Lyslyn test files found in '{target_path}' (looking for test_*.lys or *_test.lys).")
        return 0

    print(f"\033[1mRunning {len(test_files)} test suite(s)...\033[0m\n")

    passed = 0
    failed = 0

    for test_file in test_files:
        sys.stdout.write(f"  • {test_file} ... ")
        sys.stdout.flush()

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

            print("\033[92mPASSED\033[0m")
            passed += 1

        except LyslynError as e:
            print("\033[91mFAILED\033[0m")
            print(e.format_diagnostic(color=True), file=sys.stderr)
            failed += 1
        except Exception as e:
            print("\033[91mFAILED\033[0m")
            print(f"    \033[91mError\033[0m: {e}\n", file=sys.stderr)
            failed += 1

    print(f"\n\033[1mTest Results:\033[0m \033[92m{passed} passed\033[0m, \033[91m{failed} failed\033[0m, {len(test_files)} total.")
    return 0 if failed == 0 else 1


def cmd_init(args: argparse.Namespace) -> int:
    project_dir = args.name
    if os.path.exists(project_dir):
        print(f"\033[91mError\033[0m: Directory '{project_dir}' already exists.")
        return 1

    os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)

    # 1. lyslyn.json
    manifest = {
        "name": project_dir,
        "version": "1.0.0",
        "description": f"A Lyslyn project: {project_dir}",
        "main": "main.lys",
        "scripts": {
            "start": "lyslyn run main.lys",
            "test": "lyslyn test"
        }
    }
    with open(os.path.join(project_dir, "lyslyn.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 2. main.lys
    main_code = """# Welcome to your new Lyslyn project!

Set project_name to "{project_name}"
Print "Hello from {project_name}!"
Print "Programming in clear, structured English with Lyslyn."

Create a function called greet with user:
    Return "Greetings, {user}!"

Print greet("Developer")
""".replace("{project_name}", project_dir)

    with open(os.path.join(project_dir, "main.lys"), "w", encoding="utf-8") as f:
        f.write(main_code)

    # 3. tests/test_main.lys
    test_code = """# Test suite for project
Create a function called add with a, b:
    Return a + b

Assert(add(2, 3) is equal to 5, "Addition test")
Assert(add(-1, 1) is equal to 0, "Zero sum test")
Print "✓ Math assertions passed"
"""
    with open(os.path.join(project_dir, "tests", "test_main.lys"), "w", encoding="utf-8") as f:
        f.write(test_code)

    # 4. README.md
    readme_content = f"""# {project_dir}

A project written in [Lyslyn](https://lyslyn.org) — The English-structured programming language.

## Getting Started

Run the program:
```bash
lyslyn run main.lys
```

Run tests:
```bash
lyslyn test
```

Check syntax and semantics:
```bash
lyslyn check main.lys
```
"""
    with open(os.path.join(project_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"\033[92m✓\033[0m Initialized new Lyslyn project in \033[1m{project_dir}\033[0m/")
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

    # format
    fmt_parser = subparsers.add_parser("format", help="Format a Lyslyn source file")
    fmt_parser.add_argument("file", help="Path to .lys source file")
    fmt_parser.add_argument("-w", "--write", action="store_true", help="Write formatted code back to file in-place")

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
