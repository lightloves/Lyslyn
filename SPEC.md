# Lyslyn Programming Language Specification
**Version 1.1.0 — Production Backend Edition**

Lyslyn is a modern, general-purpose programming language designed specifically for production backend engineering, microservices, and distributed systems. It makes backend programming feel like writing clear, structured English while providing the deterministic precision, performance, and reliability required of production web runtimes.

---

## 1. Design Principles for Backend Engineering

1. **Declarative Backend Architecture**: First-class language constructs for HTTP servers, routing, middleware pipelines, database queries, and request validation.
2. **Deterministic Formal Grammar**: An unambiguous context-free grammar with mathematically exact operational semantics.
3. **Built-in Production Stack**: Native SQLite/ORM database engine, multi-threaded HTTP server, path-parameter routing (`:id`), input validation, and password cryptography with zero third-party dependencies.
4. **Resilient Error Boundaries**: Clean, structured exception handling with automatic HTTP 400/500 responses and developer diagnostics.

---

## 2. Formal Grammar (EBNF) — Backend Additions

```ebnf
program         = { statement | newline } , EOF ;

statement       = set_stmt
                | const_stmt
                | change_stmt
                | if_stmt
                | while_stmt
                | for_stmt
                | repeat_stmt
                | func_def
                | return_stmt
                | break_stmt
                | continue_stmt
                | try_stmt
                | raise_stmt
                | import_stmt
                | http_stmt
                | serve_stmt
                | route_stmt
                | use_stmt
                | respond_stmt
                | validate_stmt
                | print_stmt
                | expr_stmt ;

(* Backend Server Statements *)
serve_stmt      = "Serve" [ "HTTP" ] "on" "port" expr [ "host" expr ] ":" serve_block ;
serve_block     = INDENT { use_stmt | route_stmt } DEDENT ;

route_stmt      = "Route" HTTP_METHOD ( STRING | IDENTIFIER ) ":" block ;
use_stmt        = "Use" [ "middleware" ] expr ;

respond_stmt    = "Respond" [ "with" ]
                  [ "status" expr [ "and" ] ]
                  ( "json" expr | "text" expr | "redirect" expr | expr ) ;

validate_stmt   = "Validate" ( "body" | "query" | "params" ) "with" expr ;

HTTP_METHOD     = "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "OPTIONS" | "HEAD" | "*" ;
```

---

## 3. Native Backend Architecture

### 3.1 HTTP Server & Routing Lifecycle
When `Serve HTTP on port <port>:` executes:
1. A multi-threaded socket server binds to `<host>:<port>`.
2. Middleware pipelines execute sequentially for every inbound request.
3. URL routing matches path patterns with path variables (`/api/users/:id`), extracting `request.params.id`.
4. Handlers execute in isolated request environments containing `request`:
   - `request.method`: HTTP method (`"GET"`, `"POST"`, etc.)
   - `request.path`: URL path (`"/api/users/42"`)
   - `request.params`: Extracted path variables (`{"id": "42"}`)
   - `request.query`: Query parameters (`{"page": "1"}`)
   - `request.headers`: HTTP request headers
   - `request.body`: Automatically parsed JSON payload or string
   - `request.ip`: Remote client IP address
5. `Respond with status <status> and json <payload>` sends headers and serialized body to the client.

### 3.2 Built-in Database Layer (`db` / `database`)
Embedded SQLite engine supporting WAL concurrency, transactions, and high-level CRUD:
- `db.connect(path)`: Connects to file or `":memory:"`.
- `db.create_table(name, schema_dict)`: Creates table with typed schema.
- `db.insert(table, data_dict)`: Inserts record and returns inserted object with `id`.
- `db.find(table, where_dict, order_by, limit)`: Queries records.
- `db.find_one(table, where_dict)`: Fetches single record or `nil`.
- `db.update(table, where_dict, updates_dict)`: Updates records.
- `db.delete(table, where_dict)`: Deletes records.
- `db.query(sql, params)`: Parameterized SQL query returning list of dicts.
- `db.execute(sql, params)`: Parameterized DDL/DML.

### 3.3 Request Validation (`Validate body with ...`)
Declarative schema validation that automatically interrupts execution and responds with HTTP 400 Bad Request if invalid:
- `required string min:3 max:50`
- `required email`
- `required number min:0`
- `optional boolean`

### 3.4 Security & Cryptography (`crypto`)
- `crypto.hash_password(pwd)`: PBKDF2 HMAC-SHA256 password hashing.
- `crypto.verify_password(pwd, hash)`: Constant-time password verification.
- `crypto.sha256(text)`: SHA-256 hex digest.
- `crypto.token(bytes)`: Secure cryptographic random hex token.
- `crypto.uuid()`: RFC 4122 UUID v4 generator.
