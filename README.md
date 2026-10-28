# Lyslyn — The Industrial-Grade Backend Language

[![Version](https://img.shields.io/badge/version-2.0.0--industrial-blue.svg)](SPEC.md)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Lyslyn** makes backend programming feel like writing clear, structured English while providing the deterministic precision, performance, and reliability required of production web runtimes.

---

## ⚡ Industrial Capabilities

- 🏛️ **Java & Python Level OOP**: Full classes, constructors (`To initialize with ...:`), instance methods, inheritance (`inheriting from ...`), superclass delegation (`Call parent with ...`), and bound methods.
- 🔍 **Dynamic Type Inspection & Reflection**: `type(x)` reflection, `is an instance of <Class>`, and English type predicates (`is a string`, `is an integer`, `is a number`, `is a list`, `is a map`, `is a function`).
- 🎯 **Enterprise Regular Expressions**: Native `regex` engine (`regex.is_match`, `regex.find`, `regex.find_all`, `regex.replace`, `regex.split`).
- 💻 **Operating System & Process System APIs**: Native `os` module (`os.platform`, `os.arch`, `os.cwd`, `os.args`, `os.exit`, `os.exec`).
- 🚀 **Bytecode Compiler & Stack Virtual Machine**: Fast AST-to-bytecode compilation, binary serialization (`.lysc`), and independent Rust execution engine.
- 🌐 **Native HTTP Server & Routing**: First-class `Serve HTTP on port ...` syntax with pattern-matching path parameters (`/api/users/:id`).
- 🛡️ **JWT Authentication & Security**: RFC 7519 JSON Web Tokens (`jwt.sign`, `jwt.verify`) and native `server.jwt_auth()` middleware.
- ⏱️ **In-Memory TTL Cache Engine**: Fast in-process key-value store with millisecond-precision TTL eviction (`cache.set`, `cache.get_or_set`).
- 🛑 **Sliding-Window Rate Limiting**: Built-in IP-based rate limiting middleware (`server.rate_limit`) with HTTP 429 backoff.
- 🗄️ **Zero-Dependency Database Engine**: Built-in SQLite and ORM layer (`db.insert`, `db.find`, `db.query`) with WAL concurrency.
- 🔍 **Declarative Request Validation**: `Validate body with { ... }` automatically inspects payloads and responds with formatted HTTP 400 errors.
- 🔒 **Enterprise-Grade Cryptography**: Native PBKDF2 password hashing, constant-time verification, UUIDs, HMAC, and tokens.
- 🧩 **Functional Collections Pipeline**: High-order algorithms (`Map`, `Filter`, `Reduce`, `Sort`, `Unique`, `Chunk`, `Zip`).
- ⚙️ **Config & Structured Logging**: Automatic `.env` file loader (`env.require`, `env.get_int`) and colorized/JSON logger.
- 📦 **Deterministic Package Manager**: Project initialization and dependency management (`lys init`, `lys install`, `lys remove`).
- 🛠️ **Full Developer Toolchain**: CLI with `run`, `check`, `build`, `test`, `init`, `install`, `remove`, and interactive `repl`.

---

## 📖 Coding in Pure Simple English

Lyslyn is engineered so that **every program reads like clear, structured English prose**, eliminating cryptic symbols and bracket fatigue:

```lys
Set languages to a list of "Lyslyn", "Python" and "Rust"
Add "SQL" to languages

Set profile to an object with:
    username: "Raj"
    role: "Architect"
    age: 21

If profile.age is at least 18:
    Display "Welcome, adult user!"

If languages is not empty:
    Display "Active languages:", languages

If profile.age is odd:
    Display "Age is an odd number."

For every lang in languages:
    If lang is equal to "Lyslyn":
        Display "Found primary language!"
        Stop the loop

Do 3 times:
    Display "Lyslyn makes coding simple English!"

Create a function called greet with name and role:
    Give back "Hello " + name + " (" + role + ")"

Call greet with "Raj" and "Architect"
```

---

## 🚀 30-Second Example: A Complete REST API

```lys
Import db
Import server

db.connect("./store.db")
db.create_table("items", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "price": "REAL NOT NULL"
})

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
lys examples/01_hello.lys
lys examples/01_hello.lys foo bar
lys -c 'Say "Hello from Lyslyn!"'
lys check examples/01_hello.lys
lys build examples/01_hello.lys -o hello.lysc
lys disasm examples/01_hello.lys
lys bench examples/01_hello.lys -n 100
lys repl
lys test
lys init my_service
lys install package_name
lys remove package_name
```

---

## 📁 Repository Structure

```
lyslyn/
├── Cargo.toml
├── bin/
│   ├── lys
│   └── lyslyn
├── src/
│   ├── main.rs
│   ├── lib.rs
│   ├── errors/
│   │   └── mod.rs
│   ├── lexer/
│   │   ├── token.rs
│   │   ├── scanner.rs
│   │   └── mod.rs
│   ├── ast/
│   │   └── mod.rs
│   ├── parser/
│   │   ├── parser.rs
│   │   └── mod.rs
│   ├── bytecode/
│   │   ├── opcodes.rs
│   │   ├── chunk.rs
│   │   └── mod.rs
│   ├── compiler/
│   │   ├── compiler.rs
│   │   └── mod.rs
│   ├── vm/
│   │   ├── vm.rs
│   │   └── mod.rs
│   ├── values/
│   │   ├── value.rs
│   │   └── mod.rs
│   ├── modules/
│   │   ├── loader.rs
│   │   └── mod.rs
│   ├── stdlib/
│   │   ├── math.rs
│   │   ├── json.rs
│   │   ├── fs.rs
│   │   ├── time.rs
│   │   ├── env.rs
│   │   ├── random.rs
│   │   ├── text.rs
│   │   ├── crypto.rs
│   │   ├── jwt.rs
│   │   ├── cache.rs
│   │   ├── collections.rs
│   │   ├── validation.rs
│   │   ├── db.rs
│   │   ├── server.rs
│   │   ├── http.rs
│   │   ├── log.rs
│   │   ├── regex.rs
│   │   ├── os.rs
│   │   └── mod.rs
│   ├── package_manager/
│   │   └── mod.rs
│   └── cli/
│       └── mod.rs
├── examples/
│   ├── 01_hello.lys
│   ├── 02_control_flow.lys
│   ├── 03_functions_and_closures.lys
│   ├── 04_collections.lys
│   ├── 05_error_handling.lys
│   ├── 06_filesystem.lys
│   ├── 07_http_requests.lys
│   ├── 08_modules_and_stdlib.lys
│   ├── 09_task_manager.lys
│   ├── 10_backend_api_server.lys
│   ├── 11_production_jwt_cache_api.lys
│   ├── 12_simple_english_programming.lys
│   └── 13_oop_and_industrial.lys
├── tests/
│   ├── native_rust_tests.rs
│   ├── test_basics.lys
│   ├── test_control_flow.lys
│   ├── test_functions.lys
│   ├── test_collections.lys
│   ├── test_errors.lys
│   ├── test_stdlib.lys
│   ├── test_db.lys
│   ├── test_backend_security.lys
│   ├── test_jwt_cache_collections.lys
│   ├── test_simple_english.lys
│   └── test_oop_and_industrial.lys
├── SPEC.md
├── DOCS.md
└── README.md
```

---

## 📚 Documentation Links

- [Language Specification (`SPEC.md`)](SPEC.md): Formal EBNF grammar, backend syntax, and operational semantics.
- [Reference Manual (`DOCS.md`)](DOCS.md): Complete guide to routing, database operations, security, and standard library.
