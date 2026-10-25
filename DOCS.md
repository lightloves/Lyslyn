# Lyslyn Language Documentation & Reference Manual
**Version 1.0.0**

Welcome to the official documentation for **Lyslyn**, the programming language that makes software development feel like writing clear, structured English without sacrificing precision, performance, or flexibility.

---

## Table of Contents
1. [Language Philosophy](#1-language-philosophy)
2. [Getting Started & Installation](#2-getting-started--installation)
3. [Language Basics](#3-language-basics)
   - [Variables & Constants](#31-variables--constants)
   - [Data Types](#32-data-types)
   - [Operators & Expressions](#33-operators--expressions)
4. [Control Flow](#4-control-flow)
   - [If-Otherwise Statements](#41-if-otherwise-statements)
   - [While Loops](#42-while-loops)
   - [For-Each Loops](#43-for-each-loops)
   - [Repeat Loops](#44-repeat-loops)
   - [Break & Continue](#45-break--continue)
5. [Functions & Closures](#5-functions--closures)
   - [Defining Functions](#51-defining-functions)
   - [Return Values](#52-return-values)
   - [Recursion](#53-recursion)
   - [Lexical Closures](#54-lexical-closures)
6. [Error Handling](#6-error-handling)
7. [First-Class HTTP Syntax](#7-first-class-http-syntax)
8. [Standard Library Reference](#8-standard-library-reference)
   - [`http`](#81-http)
   - [`json`](#82-json)
   - [`files`](#83-files)
   - [`text`](#84-text)
   - [`math`](#85-math)
   - [`time`](#86-time)
   - [`random`](#87-random)
   - [`env`](#88-env)
   - [`log`](#89-log)
9. [Developer Toolchain & CLI](#9-developer-toolchain--cli)

---

## 1. Language Philosophy

Traditional programming languages require developers to juggle cryptic punctuation, verbose braces, and boilerplate syntax. Lyslyn was built on a different principle:

> **Programming should read like clear, intentional English, backed by an unambiguous, deterministic compiler.**

Lyslyn is not an unpredictable AI chatbot. It is a fully specified programming language with an exact formal grammar, deterministic execution semantics, and zero ambiguity.

---

## 2. Getting Started & Installation

Lyslyn comes with a self-contained developer toolchain:

```bash
# Verify installation
lyslyn --version

# Launch the interactive REPL
lyslyn repl

# Run a script
lyslyn run script.lys

# Check syntax and semantics without running
lyslyn check script.lys

# Format code
lyslyn format script.lys -w

# Run all test suites
lyslyn test

# Scaffold a new project
lyslyn init my-project
```

---

## 3. Language Basics

### 3.1 Variables & Constants

Variables are declared and updated using `Set`:
```lys
Set username to "Raj"
Set score to 100
```

Variables can also be modified using `Increase`, `Decrease`, and `Change`:
```lys
Increase score by 10    # score is now 110
Decrease score by 5     # score is now 105
Change username to "Alex"
```

Constants are immutable values declared with `Constant`:
```lys
Constant MAX_CONNECTIONS is 100
Constant PI is 3.14159
```

### 3.2 Data Types

Lyslyn features dynamic typing with rich standard primitives:

| Type | Examples | Description |
|---|---|---|
| **Number** | `42`, `-17`, `3.14159`, `1e-3` | 64-bit integers and IEEE-754 floats |
| **String** | `"Hello"`, `'world'`, `"Score: {score}"` | UTF-8 strings with string interpolation |
| **Boolean** | `true` (`yes`), `false` (`no`) | Truth values |
| **Nil** | `nil`, `null`, `nothing` | Absence of value |
| **List** | `[1, 2, "three", true]` | Ordered dynamic arrays |
| **Object** | `{"name": "Raj", "role": "Architect"}` | Key-value dictionaries |
| **Function** | `create a function called ...` | First-class callable objects |

#### String Interpolation
Embed expressions directly into strings using `{expression}`:
```lys
Set user to "Raj"
Set items to 3
Print "Hello, {user}! You have {items * 2} pending items."
```

### 3.3 Operators & Expressions

#### Arithmetic Operators
- Addition & String Concatenation: `+`
- Subtraction: `-`
- Multiplication: `*`
- Division: `/`
- Modulo: `%`

#### Comparison Operators (Symbolic & English)
Lyslyn allows natural English comparison phrases:
- `is equal to` or `==` or `equals`
- `is not equal to` or `!=` or `does not equal`
- `is at least` or `>=` or `is greater than or equal to`
- `is at most` or `<=` or `is less than or equal to`
- `is greater than` or `>`
- `is less than` or `<`
- `in` or `is in`
- `not in` or `is not in`

```lys
If age is at least 18 and score > 80:
    Print "Eligible for advanced placement!"
```

#### Logical Operators
- `and`
- `or`
- `not` (or `!`)

---

## 4. Control Flow

### 4.1 If-Otherwise Statements
```lys
If score is at least 90:
    Print "Grade: A"
Otherwise if score is at least 80:
    Print "Grade: B"
Otherwise:
    Print "Grade: C"
```

### 4.2 While Loops
```lys
Set counter to 1
While counter is at most 5:
    Print "Current:", counter
    Increase counter by 1
```

### 4.3 For-Each Loops
```lys
Set fruits to ["Apple", "Banana", "Cherry"]
For each fruit in fruits:
    Print "Fruit:", fruit
```

### 4.4 Repeat Loops
Lyslyn provides a clean loop for repeating actions a specific number of times:
```lys
Repeat 3 times:
    Print "Lyslyn is productive!"
```

### 4.5 Break & Continue
```lys
Set i to 0
While i < 10:
    Increase i by 1
    If i is equal to 3:
        Continue to next iteration
    If i is equal to 7:
        Break out of loop
    Print i
```

---

## 5. Functions & Closures

### 5.1 Defining Functions
Functions can be defined with natural English syntax:
```lys
Create a function called greet with name:
    Print "Hello, " + name

# Invocation
greet("Raj")
# or:
Run greet with "Raj"
```

Multiple parameters:
```lys
Create a function called calculate_tax with amount, rate:
    Return amount * rate
```

### 5.2 Return Values
```lys
Create a function called square with x:
    Return x * x
```

### 5.3 Lexical Closures
Functions capture their enclosing environment, allowing stateful function generators:
```lys
Create a function called make_counter with initial:
    Set count to initial
    Create a function called next_count:
        Increase count by 1
        Return count
    Return next_count

Set counter to make_counter(10)
Print counter()    # 11
Print counter()    # 12
```

---

## 6. Error Handling

Lyslyn features robust structured exception handling:

```lys
Try:
    If denominator is equal to 0:
        Raise error "Cannot divide by zero"
    Set result to numerator / denominator
Catch error as err:
    Print "Handled error:", err
Finally:
    Print "Operation finished."
```

---

## 7. First-Class HTTP Syntax

Lyslyn features native syntactic support for HTTP requests:

```lys
Send a POST request to "https://api.example.com/users":
    headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    }
    data: {
        "username": "Raj",
        "role": "Engineer"
    }
    timeout: 10
    save response as resp

If resp.ok:
    Print "Success! Status:", resp.status
    Set user_info to resp.json()
    Print "Created user ID:", user_info.id
Otherwise:
    Print "Request failed:", resp.status
```

---

## 8. Standard Library Reference

### 8.1 `http`
- `http.get(url, options)`
- `http.post(url, options)`
- `http.put(url, options)`
- `http.delete(url, options)`
- `http.request(method, url, options)`

### 8.2 `json`
- `json.parse(string)`: Deserializes JSON string into Lyslyn object/list.
- `json.stringify(value, indent)`: Serializes Lyslyn value to JSON string.

### 8.3 `files`
- `files.read_text(path)`: Reads entire text file.
- `files.write_text(path, content)`: Writes text to file.
- `files.append_text(path, content)`: Appends text to file.
- `files.exists(path)`: Returns true if file or directory exists.
- `files.delete(path)`: Deletes file or directory.
- `files.list_directory(path)`: Returns list of file names.
- `files.create_directory(path)`: Creates directory recursively.

### 8.4 `text`
- `text.trim(s)`: Strips whitespace from both ends.
- `text.uppercase(s)`: Converts string to uppercase.
- `text.lowercase(s)`: Converts string to lowercase.
- `text.split(s, sep)`: Splits string by delimiter.
- `text.join(list, sep)`: Joins list of strings by delimiter.
- `text.replace(s, old, new)`: Replaces occurrences.
- `text.starts_with(s, prefix)`: Returns true if string starts with prefix.
- `text.ends_with(s, suffix)`: Returns true if string ends with suffix.

### 8.5 `math`
- `math.pi`: Mathematical constant $\pi$.
- `math.e`: Euler's constant $e$.
- `math.sqrt(x)`: Square root.
- `math.floor(x)`, `math.ceil(x)`, `math.round(x, n)`: Rounding helpers.
- `math.min(*args)`, `math.max(*args)`: Extremes.
- `math.sin(x)`, `math.cos(x)`, `math.tan(x)`: Trigonometry.

### 8.6 `time`
- `time.now()`: Returns current ISO 8601 timestamp.
- `time.sleep(seconds)`: Pauses execution.
- `time.timestamp()`: Unix epoch seconds.
- `time.format(fmt)`: Formatted date string.

### 8.7 `random`
- `random.random()`: Random float in $[0.0, 1.0)$.
- `random.integer(min, max)`: Random integer in range $[min, max]$.
- `random.choice(list)`: Randomly selected element.
- `random.shuffle(list)`: Returns a shuffled copy of the list.

### 8.8 `env`
- `env.get(key, default)`: Retrieves environment variable.
- `env.set(key, value)`: Sets environment variable.
- `env.has(key)`: Checks if environment variable exists.

### 8.9 `log`
- `log.info(*args)`: Logs message with `[INFO]` header in blue.
- `log.warn(*args)`: Logs message with `[WARN]` header in yellow.
- `log.error(*args)`: Logs message with `[ERROR]` header in red.
- `log.debug(*args)`: Logs message with `[DEBUG]` header in gray.

---

## 9. Developer Toolchain & CLI

```bash
# Check syntax & semantic analysis without execution
lyslyn check main.lys

# Run the program
lyslyn run main.lys

# Format code automatically
lyslyn format main.lys -w

# Discover and run all test suites
lyslyn test

# Scaffold a project
lyslyn init my-service
```
