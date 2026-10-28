# Lyslyn Language Documentation & Reference Manual
**Version 1.1.0 — Production Backend Edition**

Welcome to the comprehensive documentation for **Lyslyn**, the production-grade, general-purpose programming language designed specifically for backend web services, APIs, microservices, and distributed applications.

---

## Table of Contents
1. [Backend Design Philosophy](#1-backend-design-philosophy)
2. [Quickstart: A 30-Second REST API](#2-quickstart-a-30-second-rest-api)
3. [Language Basics](#3-language-basics)
4. [Control Flow](#4-control-flow)
5. [Functions & Closures](#5-functions--closures)
6. [Native HTTP Server & Routing](#6-native-http-server--routing)
   - [Serve HTTP Blocks](#61-serve-http-blocks)
   - [Route Handlers & Path Parameters](#62-route-handlers--path-parameters)
   - [Middleware Pipeline](#63-middleware-pipeline)
   - [Request Object](#64-request-object)
   - [Respond Statements](#65-respond-statements)
   - [Request Validation](#66-request-validation)
7. [Built-in Database Engine (`db`)](#7-built-in-database-engine-db)
8. [Backend Security & Cryptography (`crypto`)](#8-backend-security--cryptography-crypto)
9. [Standard Library Reference](#9-standard-library-reference)
10. [Developer Toolchain & CLI](#10-developer-toolchain--cli)

---

## 1. Backend Design Philosophy

Backend development in traditional languages (Node.js, Go, Python, Java) suffers from:
- Massive boilerplate to configure servers, routes, JSON parsing, and middleware.
- Cryptic frameworks and thousands of transient npm/pip dependencies.
- Fragmented database query APIs and error-prone validations.

**Lyslyn** solves this by elevating backend primitives into the language itself:
- **`Serve HTTP on port ...`** is a native language statement.
- **`Route GET "/api/users/:id"`** handles path routing and URL decoding natively.
- **`Validate body with { ... }`** intercepts invalid inputs and returns structured 400 errors automatically.
- **`Respond with status 200 and json ...`** delivers responses with proper headers and serialization.
- **`db.query(...)` and `db.insert(...)`** provide built-in SQLite database operations with zero external drivers.

---

## 2. Quickstart: A 30-Second REST API

Save the following code as `api.lys`:

```lys
Import db
Import server

db.connect("./app.db")
db.create_table("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "email": "TEXT UNIQUE NOT NULL"
})

Serve HTTP on port 8080:
    Use middleware server.cors("*")
    Use middleware server.logger()

    Route GET "/health":
        Respond with status 200 and json {"status": "ok"}

    Route GET "/api/users":
        Set users to db.query("SELECT * FROM users")
        Respond with status 200 and json users

    Route GET "/api/users/:id":
        Set user to db.find_one("users", {"id": request.params.id})
        If user is nil:
            Respond with status 404 and json {"error": "User not found"}
        Otherwise:
            Respond with status 200 and json user

    Route POST "/api/users":
        Validate body with {
            "name": "required string min:2",
            "email": "required email"
        }
        Set new_user to db.insert("users", request.body)
        Respond with status 201 and json new_user
```

Run the server:
```bash
lys api.lys
```

---

## 3. Pure Simple English Syntax Guide

Lyslyn replaces traditional punctuation and cryptic syntax symbols with structured English:

| Traditional Language | Lyslyn Simple English |
|---|---|
| `const languages = ["Python", "Rust"];` | `Set languages to a list of "Python" and "Rust"` |
| `languages.push("Go");` | `Add "Go" to languages` |
| `if (users.length === 0)` | `If users is empty:` |
| `if (age >= 18)` | `If age is at least 18:` |
| `if (n % 2 === 0)` | `If n is even:` |
| `if (n % 2 !== 0)` | `If n is odd:` |
| `if (user !== null)` | `If user is something:` (or `is not nil:`) |
| `console.log("Hello", name);` | `Display "Hello", name` (or `Print`) |
| `return result;` | `Give back result` (or `Return result`) |
| `break;` | `Stop the loop` (or `Break`) |
| `continue;` | `Skip to next` (or `Continue`) |
| `for (let i = 0; i < 5; i++)` | `Do 5 times:` (or `Repeat 5 times:`) |
| `for (const x of items)` | `For every x in items:` |
| `fn(arg1, arg2)` | `Call fn with arg1 and arg2` |

---

## 4. Simple English Collections & Objects

```lys
Set fruits to a list of "apple", "banana" and "cherry"
Add "mango" to fruits

Set inbox to an empty list
If inbox is empty:
    Display "Zero messages pending."

Set user to an object with:
    username: "Raj"
    role: "Architect"
    age: 21

Set server_cfg to an object with host = "127.0.0.1", port = 8080
```

---

## 5. Control Flow, Functions, and Error Handling in English

```lys
If balance is positive:
    Display "In good credit."
Otherwise if balance is zero:
    Display "Zero balance."
Otherwise:
    Display "In debt."

For every fruit in fruits:
    If fruit is equal to "banana":
        Skip to next
    Display "Fruit:", fruit

Do 3 times:
    Display "Lyslyn is simple English!"

Create a function called greet with name and title:
    Give back "Hello " + title + " " + name

Call greet with "Raj" and "Architect"
```

---

## 6. Native HTTP Server & Routing

### 6.1 `Serve HTTP` Blocks
The `Serve` statement initializes a multi-threaded, non-blocking socket server:

```lys
Serve HTTP on port 8080:
    Use middleware server.cors("*")
    Use middleware server.logger()
```

Custom host binding:
```lys
Serve HTTP on port 3000 host "127.0.0.1":
    ...
```

### 6.2 Route Handlers & Path Parameters
Define endpoints with `Route <METHOD> <path>:`:

```lys
Route GET "/api/users/:id":
    Set user_id to request.params.id
    ...

Route POST "/api/auth/login":
    ...
```

Supported methods: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`, `HEAD`, and `*` (wildcard).

### 6.3 Middleware Pipeline
Middlewares are registered with `Use middleware <callable>` and execute in declaration order:

```lys
Use middleware server.cors("*")
Use middleware server.logger()
Use middleware server.auth_bearer("my_secret_token")
```

Custom middleware:
```lys
Create a function called check_api_key with req:
    If req.headers["x-api-key"] != "valid_key":
        Return {"status": 401, "body": {"error": "Invalid API Key"}}
    Return nil

Use middleware check_api_key
```

### 6.4 The `request` Context
Inside any route block, the `request` variable is automatically available:
- `request.method`: string (e.g. `"POST"`)
- `request.path`: string (e.g. `"/api/users/12"`)
- `request.params`: dictionary of path variables (e.g. `request.params.id`)
- `request.query`: dictionary of URL query parameters (e.g. `request.query.page`)
- `request.headers`: dictionary of lowercase request headers
- `request.body`: parsed JSON object or string
- `request.ip`: client IP address

### 6.5 Respond Statements
Send responses and terminate route execution:

```lys
Respond with status 200 and json {"result": "success"}
Respond with status 201 and json created_item
Respond with status 404 and json {"error": "Item not found"}
Respond with status 200 and text "Hello plain text"
Respond with redirect "/login"
```

### 6.6 Request Validation
Validate incoming payloads declaratively:

```lys
Validate body with {
    "username": "required string min:3 max:20",
    "email": "required email",
    "age": "optional number min:18",
    "isAdmin": "optional boolean"
}
```

If validation fails, Lyslyn immediately interrupts execution and returns an HTTP 400 Bad Request:
```json
{
  "error": "Validation Failed",
  "details": [
    { "field": "username", "issue": "Field 'username' length must be at least 3" },
    { "field": "email", "issue": "Field 'email' must be a valid email address" }
  ]
}
```

---

## 7. Built-in Database Engine (`db`)

Lyslyn includes a zero-dependency, production-ready SQLite database and ORM layer.

### Connection
```lys
Import db

db.connect("./production.db")
db.connect(":memory:")
```

### Table Creation
```lys
db.create_table("customers", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "email": "TEXT UNIQUE NOT NULL",
    "balance": "REAL DEFAULT 0.0",
    "created_at": "TEXT NOT NULL"
})
```

### High-Level CRUD
```lys
Set user to db.insert("customers", {
    "name": "Raj",
    "email": "raj@example.com",
    "balance": 250.0,
    "created_at": time.now()
})
Print "Inserted user ID:", user.id

Set all_users to db.find("customers")
Set active to db.find("customers", {"balance": 250.0}, "name ASC", 10)
Set customer to db.find_one("customers", {"email": "raj@example.com"})

db.update("customers", {"id": user.id}, {"balance": 300.0})
db.delete("customers", {"id": user.id})
Set total to db.count("customers")
```

### Raw Parameterized SQL
```lys
Set high_rollers to db.query("SELECT * FROM customers WHERE balance > ? ORDER BY balance DESC", [100.0])
Set result to db.execute("UPDATE customers SET balance = balance + 10 WHERE balance < ?", [50.0])
Print "Rows updated:", result.rows_affected
```

---

## 8. Backend Security & Cryptography (`crypto`)

```lys
Import crypto

Set password to "MySecureP@ssword123!"
Set hashed to crypto.hash_password(password)

If crypto.verify_password("MySecureP@ssword123!", hashed):
    Print "Password is valid!"

Set session_token to crypto.token(32)
Set request_id to crypto.uuid()
Set hash_val to crypto.sha256("payload string")
```

---

## 9. Standard Library Reference

| Module | Description | Key Functions |
|---|---|---|
| **`jwt`** | RFC 7519 JSON Web Tokens | `sign(payload, secret, expires_in)`, `verify(token, secret)`, `decode(token)` |
| **`cache`** | In-Memory TTL Key-Value Store | `set(k, v, ttl)`, `get(k, default)`, `has(k)`, `delete(k)`, `clear()`, `size()`, `get_or_set(k, fn, ttl)` |
| **`collections`** | Functional Data Processing | `map(lst, fn)`, `filter(lst, fn)`, `reduce(lst, fn, init)`, `sort(lst, key, rev)`, `unique(lst)`, `chunk(lst, sz)`, `zip(a, b)` |
| **`server`** | HTTP Server & Middleware | `create`, `cors`, `logger`, `auth_bearer`, `jwt_auth(secret, exclude)`, `rate_limit(max, window)` |
| **`db`** / **`database`** | SQLite & Document ORM | `connect`, `query`, `execute`, `create_table`, `insert`, `find`, `find_one`, `update`, `delete`, `count` |
| **`crypto`** | Cryptography & Security | `hash_password`, `verify_password`, `sha256`, `hmac`, `token`, `uuid` |
| **`validation`** | Schema Validator | `validate(data, schema)` |
| **`env`** | Environment & Config | `get`, `get_int`, `get_bool`, `require(key)`, `set`, `has`, `all`, auto `.env` loading |
| **`log`** | Structured Production Logging | `info`, `warn`, `error`, `debug`, `set_level("info")`, `set_format("text" \| "json")` |
| **`metrics`** | Prometheus Telemetry | `counter`, `gauge`, `histogram`, `export_prometheus()` |
| **`tasks`** | Background Worker Queues | `dispatch(fn, args)` |
| **`http`** | HTTP Client | `get`, `post`, `put`, `delete`, `request` |
| **`json`** | JSON Serialization | `parse`, `stringify` |
| **`files`** | Filesystem I/O | `read_text`, `write_text`, `exists`, `delete`, `list_directory` |
| **`text`** | String Manipulation | `trim`, `uppercase`, `lowercase`, `split`, `join`, `replace` |
| **`math`** | Mathematical Functions | `sqrt`, `round`, `floor`, `ceil`, `min`, `max`, `pow`, `pi` |
| **`time`** | Time & Dates | `now`, `sleep`, `timestamp`, `format` |
| **`random`** | Random Numbers | `random`, `integer`, `choice`, `shuffle` |

---

## 10. Developer Toolchain & CLI

The toolchain is available through both `lyslyn` and its short alias `lys`:

```bash
lys server.lys
lyslyn server.lys
lys server.lys --port 8080 prod
lys -c 'Say "Hello world!"'
lys check server.lys
lys build server.lys -o server.lysc
lys disasm server.lys
lys bench server.lys -n 100
lys repl
lys test
lys init my-backend
lys install package_name
lys remove package_name
```
