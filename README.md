# Lyslyn — The Industrial-Grade Backend Language

[![Version](https://img.shields.io/badge/version-2.0.0--industrial-blue.svg)](SPEC.md)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Lyslyn** makes backend programming feel like writing clear, structured English while providing the deterministic precision, performance, and reliability required of production web runtimes.

---

## ⚡ Industrial Capabilities

- 🚀 **Bytecode Compiler & Stack Virtual Machine**: Fast AST-to-bytecode compilation, binary serialization (`.lysc`), and disassembler (`lys disasm`).
- 🌐 **Native HTTP Server & Routing**: First-class `Serve HTTP on port ...` syntax with pattern-matching path parameters (`/api/users/:id`).
- 🗄️ **Zero-Dependency Database Engine**: Built-in SQLite and ORM layer (`db.insert`, `db.find`, `db.query`) with WAL concurrency.
- 🛡️ **Declarative Request Validation**: `Validate body with { ... }` automatically inspects payloads and responds with formatted HTTP 400 errors.
- 🔒 **Enterprise-Grade Cryptography**: Native PBKDF2 password hashing, constant-time verification, UUIDs, and random tokens.
- 📦 **Deterministic Package Manager & Lockfile**: `lyslyn.lock` with SHA-256 integrity checksums (`lys add`, `lys install`, `lys pack`).
- 🔍 **Static Analysis Linter**: `lys lint` detects dead branches, unreachable code, and unused bindings.
- ⏱️ **Microbenchmark Harness**: `lys bench` reports operations/sec, mean latencies, and percentiles.
- 📖 **Documentation Generator**: `lys doc` automatically extracts doc-comments into Markdown.
- 🛠️ **Full Developer Toolchain**: CLI with `run`, `compile`, `disasm`, `lint`, `bench`, `doc`, `check`, `format`, `test`, `init`, and `repl`.

---

## 🚀 30-Second Example: A Complete REST API

```lys
Import db
Import server

# Connect to database and ensure table exists
db.connect("./store.db")
db.create_table("items", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "price": "REAL NOT NULL"
})

# Launch production server
Serve HTTP on port 8080:
    Use middleware server.cors("*")
    Use middleware server.logger()

    Route GET "/health":
        Respond with status 200 and json {"status": "ok"}

    Route GET "/api/items":
        Set items to db.find("items")
        Respond with status 200 and json items

    Route GET "/api/items/:id":
        Set item to db.find_one("items", {"id": request.params.id})
        If item is nil:
            Respond with status 404 and json {"error": "Item not found"}
        Otherwise:
            Respond with status 200 and json item

    Route POST "/api/items":
        Validate body with {
            "name": "required string min:2",
            "price": "required number min:0"
        }
        Set new_item to db.insert("items", request.body)
        Respond with status 201 and json new_item
```

---

## 📦 Getting Started

Both `lyslyn` and its short alias `lys` are installed and available in `$PATH`:

```bash
# 1. Run any script directly (just like python)
lys examples/01_hello.lys

# 2. Run with arguments passed through
lys examples/01_hello.lys foo bar

# 3. Run inline code snippets
lys -c "Print 'Hello from Lyslyn!'"

# 4. Start interactive REPL (just type `lys`)
lys

# 5. Run compiled bytecode (.lysc) directly with instant VM startup
lys hello.lysc

# --- Developer Toolchain Commands ---

# Compile to binary bytecode (.lysc)
lys compile examples/01_hello.lys -o hello.lysc

# Disassemble bytecode instructions
lys disasm examples/01_hello.lys

# Run static analysis linter
lys lint examples/

# Benchmark execution throughput
lys bench examples/01_hello.lys -n 100

# Generate API documentation
lys doc examples/math_utils.lys

# Run all test suites
lys test

# Beautify code in-place
lys format -w

# Scaffold a new project
lys init my-service
```

---

## 📁 Repository Structure

```
lyslyn/
├── bin/
│   └── lyslyn                 # Executable CLI launcher
├── lyslyn/
│   ├── tokens.py              # Token definitions with backend keywords
│   ├── lexer.py               # Indentation-aware lexical scanner
│   ├── ast_nodes.py           # AST definitions (ServeStmt, RouteStmt, RespondStmt, ValidateStmt)
│   ├── parser.py              # Recursive-descent parser with contextual keywords
│   ├── semantics.py           # Scope and backend syntax validator
│   ├── interpreter.py         # AST execution engine and HTTP server runtime
│   ├── diagnostics.py         # Formatted compiler error reporting
│   ├── formatter.py           # Code formatter & canonicalizer
│   ├── repl.py                # Interactive REPL shell
│   ├── cli.py                 # Toolchain commands
│   └── stdlib/                # Standard library modules
│       ├── db.py              # Built-in SQLite database & ORM layer
│       ├── server_mod.py      # Multi-threaded HTTP server & routing engine
│       ├── validation.py      # Request schema validator
│       ├── crypto_mod.py      # Passwords, HMAC, tokens, UUIDs
│       ├── tasks_mod.py       # Asynchronous background workers
│       ├── http.py            # HTTP client (GET, POST, PUT, DELETE)
│       ├── json_mod.py        # JSON parse & stringify
│       ├── files.py           # Filesystem I/O
│       ├── text.py            # String manipulation helpers
│       └── math_mod.py        # Mathematical operations
├── examples/
│   ├── 01_hello.lys           # Basics & arithmetic
│   ├── 02_control_flow.lys    # Conditionals & loops
│   ├── 03_functions_and_closures.lys # First-class functions & stateful closures
│   ├── 04_collections.lys     # Lists & dictionaries
│   ├── 05_error_handling.lys  # Try, catch, finally, raise
│   ├── 06_filesystem.lys      # File read/write/delete
│   ├── 07_http_requests.lys   # Client HTTP requests
│   ├── 08_modules_and_stdlib.lys # Standard library modules
│   ├── 09_task_manager.lys    # Task persistence application
│   └── 10_backend_api_server.lys # Complete Production REST API Server
├── tests/
│   ├── test_backend_security.lys # Crypto & validation tests
│   ├── test_db.lys            # Database CRUD & query tests
│   ├── test_basics.lys        # Core language tests
│   ├── test_control_flow.lys  # Control flow tests
│   ├── test_functions.lys     # Closures & recursion tests
│   ├── test_collections.lys   # Lists & objects tests
│   ├── test_errors.lys        # Exception handling tests
│   ├── test_stdlib.lys        # Standard library tests
│   └── test_compiler_units.py # Python unit test suite
├── SPEC.md                    # Formal EBNF Grammar & Backend Specification
├── DOCS.md                    # Complete Reference Manual
└── README.md                  # This file
```

---

## 📚 Documentation Links

- [Language Specification (`SPEC.md`)](SPEC.md): Formal EBNF grammar, backend syntax, and operational semantics.
- [Reference Manual (`DOCS.md`)](DOCS.md): Complete guide to routing, database operations, security, and standard library.
