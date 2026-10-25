# Lyslyn — The English-Structured Programming Language

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](SPEC.md)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Lyslyn** makes programming feel like writing clear, structured English while retaining the precision, composability, and power of a real programming language.

---

## Highlights

- 🗣️ **Structured English Syntax**: `Set username to "Raj"`, `If age is at least 18:`, `Repeat 5 times:`
- 🌐 **First-Class HTTP Syntax**: Declarative `Send a POST request to "..."` blocks with JSON, headers, and timeouts.
- 🔒 **Deterministic Formal Grammar**: Fully defined context-free grammar; not an unpredictable LLM or fuzzy parser.
- ⚡ **Lexical Closures & First-Class Functions**: Stateful closures, higher-order functions, and recursion.
- 🛠️ **Full Developer Toolchain**: CLI with `run`, `check`, `format`, `test`, `init`, and interactive `repl`.
- 🔋 **Batteries Included**: Standard library for `http`, `json`, `files`, `text`, `math`, `time`, `random`, `env`, and `log`.

---

## Quick Example

```lys
# Define variables
Set username to "Raj"
Set role to "Architect"

# English comparison & conditionals
If role is equal to "Architect":
    Print "Welcome, {username}! Access granted."
Otherwise:
    Print "Standard user access."

# First-class HTTP Request
Send a POST request to "https://httpbin.org/post":
    headers: { "Content-Type": "application/json" }
    data: { "username": username, "status": "active" }
    timeout: 5
    save response as resp

If resp.ok:
    Print "Server returned status:", resp.status
    Set body to resp.json()
    Print "Echoed payload:", body.json
```

---

## Getting Started

### Installation & CLI Usage

The `lyslyn` executable is located in `bin/` and installed in your path:

```bash
# Verify installation
lyslyn --version

# Start the interactive shell
lyslyn repl

# Run an example
lyslyn run examples/01_hello.lys

# Check a file for syntax and semantic errors
lyslyn check examples/09_task_manager.lys

# Run all test suites
lyslyn test

# Format a file
lyslyn format examples/01_hello.lys -w

# Scaffold a new project
lyslyn init my-project
```

---

## Project Structure

```
lyslyn/
├── bin/
│   └── lyslyn                 # Standalone CLI executable
├── lyslyn/
│   ├── __init__.py
│   ├── tokens.py              # Token definitions and keyword tables
│   ├── lexer.py               # Indentation-aware lexical scanner
│   ├── ast_nodes.py           # AST node representations
│   ├── parser.py              # Deterministic recursive-descent parser
│   ├── semantics.py           # Scope, constants, and loop validator
│   ├── environment.py         # Lexical environments & closures
│   ├── values.py              # Runtime value types (Functions, Modules, HTTP Responses)
│   ├── interpreter.py         # AST execution engine
│   ├── builtins.py            # Global built-in functions
│   ├── formatter.py           # Code formatter & canonicalizer
│   ├── diagnostics.py         # Formatted compiler error reporting
│   ├── repl.py                # Interactive REPL shell
│   ├── cli.py                 # Toolchain command implementations
│   └── stdlib/                # Standard library modules
│       ├── __init__.py
│       ├── http.py            # HTTP client (GET, POST, PUT, DELETE)
│       ├── json_mod.py        # JSON serialization & parsing
│       ├── files.py           # File & directory operations
│       ├── text.py            # String manipulation helpers
│       ├── math_mod.py        # Mathematical functions
│       ├── misc_mods.py       # time, random, env, log modules
├── examples/
│   ├── 01_hello.lys           # Basics & arithmetic
│   ├── 02_control_flow.lys    # Conditionals, while, for-each, repeat
│   ├── 03_functions_and_closures.lys # Functions & stateful closures
│   ├── 04_collections.lys     # Lists & Dictionaries
│   ├── 05_error_handling.lys  # Try-catch-finally & raise
│   ├── 06_filesystem.lys      # File read/write/delete operations
│   ├── 07_http_requests.lys   # Real HTTP requests & response parsing
│   ├── 08_modules_and_stdlib.lys # Standard library & custom imports
│   └── 09_task_manager.lys    # Real-world task manager application
├── tests/
│   ├── test_basics.lys        # Core language tests
│   ├── test_control_flow.lys  # Loop and branch tests
│   ├── test_functions.lys     # Recursion and closure tests
│   ├── test_collections.lys   # Lists and maps tests
│   ├── test_errors.lys        # Error handling tests
│   ├── test_stdlib.lys        # Standard library tests
│   └── test_compiler_units.py # Python unit test suite
├── SPEC.md                    # Formal Language Specification
├── DOCS.md                    # Language Reference Manual
└── README.md                  # This file
```

---

## Architectural Decisions

1. **Host Implementation Language (Python 3)**:
   Python was chosen as the implementation language for the v1 interpreter because it delivers clean AST representations, robust standard library support (zero external C dependencies or fragile native toolchain requirements in mobile/Termux/Linux environments), and rapid iteration.
2. **Contextual Keywords**:
   To make code read like natural English without colliding with variable names (`Set data to ...`, `save response as resp`), Lyslyn distinguishes between statement starters and contextual identifiers.
3. **Bytecode VM Ready**:
   The AST and lexical scoping architecture have been strictly separated from the evaluator, making it straightforward to add a Bytecode Compiler or native transpiler backend in future releases.

---

## Documentation

- [Language Specification (SPEC.md)](SPEC.md): Formal EBNF grammar, type semantics, and design principles.
- [Reference Manual (DOCS.md)](DOCS.md): Full syntax guide, stdlib reference, and tutorial.
