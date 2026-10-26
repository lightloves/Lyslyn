# Lyslyn — The Production-Grade Backend Language

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](SPEC.md)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Lyslyn** makes backend programming feel like writing clear, structured English while providing the deterministic precision, performance, and reliability required of production web runtimes.

---

## ⚡ Highlights for Backend Developers

- 🌐 **Native HTTP Server & Routing**: First-class `Serve HTTP on port ...` syntax with pattern-matching path parameters (`/api/users/:id`).
- 🗄️ **Zero-Dependency Database Engine**: Built-in SQLite and ORM layer (`db.insert`, `db.find`, `db.query`) with WAL concurrency.
- 🛡️ **Declarative Request Validation**: `Validate body with { ... }` automatically inspects payloads and responds with formatted HTTP 400 errors.
- 🔒 **Enterprise-Grade Cryptography**: Native PBKDF2 password hashing, constant-time verification, UUIDs, and random tokens.
- 🗣️ **Structured English Readability**: Unambiguous grammar without cryptic punctuation, braces, or boilerplate.
- 🛠️ **Full Developer Toolchain**: CLI with `run`, `check`, `format`, `test`, `init`, and an interactive `repl`.

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

```bash
# Verify installation
lyslyn --version

# Run the complete production REST API example
lyslyn run examples/10_backend_api_server.lys

# Check syntax and semantics without execution
lyslyn check examples/10_backend_api_server.lys

# Run all 8 test suites
lyslyn test

# Scaffold a new project
lyslyn init my-service
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
