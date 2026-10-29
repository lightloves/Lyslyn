# Lyslyn

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](SPEC.md)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Lyslyn is a dynamically-typed, general-purpose scripting language implemented in Rust. It compiles to bytecode and runs on an independent stack-based virtual machine with no external runtime dependencies.

The core motivation behind Lyslyn is accessibility: to make programming logic readable and approachable by replacing dense symbolic punctuation with clear, English-inspired phrases. Phrases such as `If score is at least 90:`, `Repeat 5 times:`, `x is even`, and `Add item to list` compile into deterministic bytecode instructions.

Lyslyn is designed for students, educators, domain experts who want executable logic that reads like prose, and language enthusiasts exploring alternative syntax design.

---

## Language Comparison: Lyslyn vs. Python vs. Lua

The following tables compare the same discount-calculation task implemented across Lyslyn, Python, and Lua: defining a function to apply a 10% discount on items of 100 or more, iterating through a shopping cart, and printing the resulting prices.

### Code Comparison

| Program Step | Lyslyn | Python | Lua |
|---|---|---|---|
| **Function Definition** | `Create a function called calculate_discount with price and rate:` | `def calculate_discount(price, rate):` | `local function calculate_discount(price, rate)` |
| **Conditional Check** | `    If price is at least 100:` | `    if price >= 100:` | `    if price >= 100 then` |
| **Discount Calculation** | `        Return price - (price * rate)` | `        return price - (price * rate)` | `        return price - (price * rate)` |
| **Default Return** | `    Return price` | `    return price` | `    end`<br>`    return price`<br>`end` |
| **Collection Setup** | `Set cart to [45, 120, 80, 250]` | `cart = [45, 120, 80, 250]` | `local cart = {45, 120, 80, 250}` |
| **Collection Iteration** | `For price in cart:` | `for price in cart:` | `for _, price in ipairs(cart) do` |
| **Threshold Branch** | `    If price is at least 100:` | `    if price >= 100:` | `    if price >= 100 then` |
| **Calculate & Output** | `        Set final_price to calculate_discount(price, 0.1)`<br>`        Say "Discounted price:", final_price` | `        final_price = calculate_discount(price, 0.1)`<br>`        print("Discounted price:", final_price)` | `        local final_price = calculate_discount(price, 0.1)`<br>`        print("Discounted price:", final_price)` |
| **Else Branch** | `    Otherwise:`<br>`        Say "Standard price:", price` | `    else:`<br>`        print("Standard price:", price)` | `    else`<br>`        print("Standard price:", price)`<br>`    end`<br>`end` |

<details>
<summary>Click to expand complete standalone source files</summary>

#### Lyslyn (`discount.lys`)
```lys
Create a function called calculate_discount with price and rate:
    If price is at least 100:
        Return price - (price * rate)
    Return price

Set cart to [45, 120, 80, 250]
For price in cart:
    If price is at least 100:
        Set final_price to calculate_discount(price, 0.1)
        Say "Discounted price:", final_price
    Otherwise:
        Say "Standard price:", price
```

#### Python (`discount.py`)
```python
def calculate_discount(price, rate):
    if price >= 100:
        return price - (price * rate)
    return price

cart = [45, 120, 80, 250]
for price in cart:
    if price >= 100:
        final_price = calculate_discount(price, 0.1)
        print("Discounted price:", final_price)
    else:
        print("Standard price:", price)
```

#### Lua (`discount.lua`)
```lua
local function calculate_discount(price, rate)
    if price >= 100 then
        return price - (price * rate)
    end
    return price
end

local cart = {45, 120, 80, 250}
for _, price in ipairs(cart) do
    if price >= 100 then
        local final_price = calculate_discount(price, 0.1)
        print("Discounted price:", final_price)
    else
        print("Standard price:", price)
    end
end
```

</details>

### Language Characteristics & Trade-offs

| Criterion | Lyslyn | Python | Lua |
|---|---|---|---|
| **Syntax Philosophy** | English prose style; eliminates cryptic symbols for beginners | Clean, indentation-delimited with standard mathematical operators | Minimalist and compact; explicit block terminators (`end`) |
| **Comparison Operators** | Natural phrases (`is at least`, `is at most`, `does not equal`) | Standard mathematical symbols (`>=`, `<=`, `!=`) | Standard mathematical symbols (`>=`, `<=`, `~=`) |
| **Conciseness** | Verbose function headers; longer lines for clarity | Highly concise function and loop syntax | Concise keywords; explicit `then` and `end` delimiters |
| **Beginner Friction** | Low: avoids `=` vs `==` or `>=` vs `=>` syntax confusion | Low: clean indentation and readable keyword structure | Moderate: 1-based indexing and table syntax require adjustment |
| **Variable Scoping** | Parameters are local; `Set` currently writes to globals | Local by default in functions; explicit `global` / `nonlocal` | Global by default; requires explicit `local` keyword |
| **Data Structures** | First-class `List` and `Map` (dot and bracket notation) | Built-in `list`, `dict`, `set`, and `tuple` | Single unified `table` for arrays, dictionaries, and objects |
| **Runtime Footprint** | Self-contained single native Rust binary (~2-3 MB) | Requires full Python interpreter and standard library | Ultra-compact C library (~300 KB), embeddable in host engines |

---

## Quick Start

### Using Lyslyn Without Rust

Rust is only required if you are modifying or compiling the Lyslyn interpreter from source. For everyday development, learning, and running scripts, you can install the standalone prebuilt release binary directly.

#### Option 1: Install a Prebuilt Release (Recommended)

Precompiled binaries are published on the [GitHub Releases](https://github.com/lightloves/lyslyn/releases) page for Linux (x64), macOS (Apple Silicon / Intel), Windows (x64), and Android (ARM64).

**Linux & macOS:**
```bash
# Download the latest release archive for your platform
curl -LO https://github.com/lightloves/lyslyn/releases/latest/download/lyslyn-linux-x64.tar.gz

# Extract the archive
tar -xzf lyslyn-linux-x64.tar.gz

# Move to a directory in your PATH
sudo mv lyslyn-linux-x64 /usr/local/bin/lyslyn
chmod +x /usr/local/bin/lyslyn

# Verify installation
lyslyn --version
```

*(On macOS, replace `lyslyn-linux-x64.tar.gz` with `lyslyn-macos.tar.gz`.)*

**Windows:**
1. Download `lyslyn-windows-x64.zip` from [GitHub Releases](https://github.com/lightloves/lyslyn/releases).
2. Extract `lyslyn.exe` to a folder of your choice (for example, `C:\Program Files\Lyslyn` or `C:\tools`).
3. Add that folder to your `Path` environment variable.
4. Verify in PowerShell or Command Prompt: `lyslyn --version`.

**Android (Termux):**
```bash
curl -LO https://github.com/lightloves/lyslyn/releases/latest/download/lyslyn-android-arm64.tar.gz
tar -xzf lyslyn-android-arm64.tar.gz
mv lyslyn-android-arm64 $PREFIX/bin/lyslyn
chmod +x $PREFIX/bin/lyslyn
lyslyn --version
```

Once installed, you can execute scripts, run one-liners, or launch the interactive REPL with zero external dependencies:

```bash
lyslyn examples/01_hello.lys
lyslyn -c 'Say "Hello directly from the release binary!"'
lyslyn repl
```

#### Option 2: Distribute Standalone Executables to Others

You can also use Lyslyn to package your own scripts into standalone executables that you can share with people who do not have Rust or Lyslyn:

```bash
lyslyn compile my_script.lys -o my_app
```

The resulting `my_app` binary embeds the complete runtime engine. Recipients can run `./my_app` directly on compatible systems as a native application without installing any tools.

---

### Building from Source (Requires Rust)

If you are contributing to Lyslyn or building from source:

- **Prerequisite**: [Rust](https://www.rust-lang.org/) (version 1.75 or later) and Cargo.

Clone the repository and build the release executable:

```bash
git clone https://github.com/lightloves/lyslyn.git
cd lyslyn
cargo build --release
```

The compiled binary will be placed at `target/release/lyslyn`. You can install it into your Cargo bin directory:

```bash
cargo install --path .
```

A helper wrapper script is also provided at `bin/lys` for convenient local repository execution.

### Running Code

Run a script file:

```bash
lyslyn examples/01_hello.lys
# or using cargo directly
cargo run --release -- examples/01_hello.lys
```

Run an inline code string:

```bash
lyslyn -c 'Say "Hello from Lyslyn!"'
```

Start the interactive REPL:

```bash
lyslyn repl
```

Parse and statically validate a file without running it:

```bash
lyslyn check examples/01_hello.lys
```

Run the built-in test suite:

```bash
lyslyn test
# or via cargo test
cargo test
```

---

## Language Overview

Every feature documented below is implemented and verified in the current codebase and test suite.

### Variables and Data Types

Variables are dynamically typed and assigned using `Set <name> to <value>`:

```lys
Set user_name to "Alice"
Set age to 28
Set is_active to true
Set rating to 4.95
Set metadata to nil
```

Supported primitive types are `int`, `float`, `string`, `bool`, and `nil`.

### Natural Comparisons and Type Checks

Lyslyn supports English comparison phrases alongside standard operators:

```lys
Set score to 85

If score is at least 90:
    Say "Grade: A"
Else if score is at least 80:
    Say "Grade: B"
Otherwise:
    Say "Grade: Needs improvement"

# Parity and range checks
If score is positive and score is odd:
    Say "Score is a positive odd number."

# Type reflection
If score is an integer:
    Say "Score is an integer value."
```

Supported predicates include:
- Comparisons: `is at least`, `is at most`, `is greater than`, `is less than`, `is equal to`, `does not equal`
- State tests: `is positive`, `is negative`, `is zero`, `is even`, `is odd`, `is empty`, `is something`
- Type tests: `is a string`, `is a number`, `is an integer`, `is a float`, `is a boolean`, `is a list`, `is a map`, `is a function`, `is an instance of <Class>`

### Control Flow

```lys
# Counted loop
Repeat 3 times:
    Say "Repeating an action..."

# While loop
Set counter to 1
While counter is at most 3:
    Say "Count:", counter
    Increase counter by 1

# Collection iteration
Set items to ["book", "pen", "notebook"]
For item in items:
    If item is equal to "pen":
        Continue
    Say "Item:", item
```

`Break` and `Continue` statements are fully supported in all loop types.

### Functions and Closures

Functions support multiple parameters and return values:

```lys
Create a function called add with a and b:
    Return a + b

Say add(15, 25)  # 40
```

Functions are first-class values and can capture variables from enclosing scopes:

```lys
Create a function called make_counter with start:
    Set total to start
    Create a function called increment with step:
        Increase total by step
        Return total
    Return increment

Set counter to make_counter(10)
Say counter(5)  # 15
Say counter(5)  # 20
```

### Collections and OOP

#### Lists and Maps

```lys
# Lists
Set numbers to [1, 2, 3]
Add 4 to numbers
Say numbers[0]         # 1
Say numbers[-1]        # 4
Say numbers.length     # 4

# Maps (Objects)
Set user to {
    "name": "Bob",
    "role": "Engineer"
}
Say user.name          # Dot notation
Say user["role"]       # Subscript notation
```

#### Classes and Single Inheritance

```lys
Define a class called Animal:
    To initialize with name:
        Set this.name to name

    Method speak:
        Return this.name + " makes a sound."

Define a class called Dog inheriting from Animal:
    To initialize with name, breed:
        Call parent with name
        Set this.breed to breed

    Method speak:
        Return this.name + " barks."

Set pet to a new Dog with "Rex", "Collie"
Say pet.speak()                        # "Rex barks."
Say pet is an instance of Animal      # true
```

### Standard Library Modules

Modules are imported using `Import <name>` or `Get <name> as <alias>`:

- `math`: Trigonometry, logarithms, rounding, square roots (`math.sqrt`, `math.sin`, `math.pi`).
- `json`: JSON parsing and serialization (`json.parse`, `json.stringify`).
- `fs`: File reading, writing, appending, and directory listing (`fs.read`, `fs.write`, `fs.exists`).
- `time`: Timestamps, UTC formatting, and sleeping (`time.now`, `time.sleep`).
- `env`: Environment variable reading and directory inspection (`env.get`, `env.current_dir`).
- `crypto`: SHA-256, HMAC, and random bytes (`crypto.sha256`, `crypto.hmac_sha256`).
- `regex`: Regular expression matching and string replacement (`regex.is_match`, `regex.find`, `regex.replace`).
- `jwt`: JSON Web Token signing and verification with HS256 (`jwt.sign`, `jwt.verify`).
- `cache`: In-memory key-value store with millisecond TTL expiration (`cache.set`, `cache.get`).
- `text`: String casing, trimming, padding, and splitting (`text.trim`, `text.pad_start`).
- Higher-order functions: Built-in `filter(list, fn)`, `map(list, fn)`, and `reduce(list, fn, init)`.

---

## Advantages

- **Readability**: Code reads closer to natural language, making intended logic easier to follow for readers unfamiliar with programming idioms.
- **Zero Runtime Dependencies**: The entire language, including compiler, VM, and standard modules, is written in pure Rust. It runs as a self-contained binary without needing Python, Node.js, or external runtimes.
- **Clear Error Diagnostics**: Syntax and parse errors include line numbers, column numbers, the source line, and ASCII caret pointers showing the exact failure location.
- **Embedded Batteries**: Built-in cryptographic hashing, JWT verification, in-memory TTL caching, and regular expressions are available out of the box without external package setup.

---

## Limitations and Known Issues

To remain transparent with developers, the following limitations reflect the actual current state of the codebase:

- **Variable Scoping Leak**: Lyslyn currently lacks an explicit local variable declaration keyword (like `let` or `local`). When a variable is initialized with `Set x to ...` inside a function, if `x` was not a parameter, it is written to the global environment. This can unintentionally overwrite global variables of the same name.
- **Try / Finally on Early Return**: If a function returns early from inside a `Try:` block, the `Finally:` block is currently skipped. Furthermore, unhandled try frames can remain on the internal handler stack across call boundaries.
- **No Anonymous Functions (Lambdas)**: Closures must be defined as named functions with `Create a function called ...`. Inline expression-level lambdas (such as `(x) => x + 1`) are not yet implemented.
- **Prototype Server and Database Modules**:
  - The `Serve HTTP on port ...` statement parses and compiles, but currently outputs a status line and terminates. A multi-threaded TCP socket listener is not yet wired up.
  - The `db` module is an in-memory dictionary-backed store with basic SQL string-splitting; it is not currently connected to an embedded SQLite engine.
- **HTTP Client External Dependency**: While the language core is self-contained, the `http.get` and `http.post` library functions currently invoke the host system's `curl` executable via process spawning.
- **Bytecode File Serialization**: The `lyslyn build` command writes raw opcode bytes to `.lysc` files, but does not yet serialize the constant table or line mappings. `.lysc` files cannot currently be reloaded by `lyslyn run`.
- **Selective Imports**: Syntax such as `From math Import sqrt` is unsupported; modules must be imported in their entirety.
- **Ecosystem Size**: Lyslyn is an experimental, emerging language. There are currently no prebuilt package registries or IDE language servers (LSP).

---

## Future Goals and Roadmap

The following improvements are planned or proposed for future releases:

### Planned for v1.1.0
- **Lexical Scoping**: Add an explicit `local` / `let` declaration to properly scope variables to their enclosing block and prevent global leakage.
- **Error Unwinding**: Update VM frame return handling so `Finally` blocks always execute upon early return and unpopped try handlers are cleaned up.
- **Anonymous Functions**: Introduce concise inline lambda syntax for use with `map`, `filter`, and callbacks.
- **Selective Module Imports**: Support importing individual functions from modules (e.g., `From math Import sqrt`).

### Proposed for v1.2.0
- **Embedded SQLite Integration**: Replace the in-memory mock database with an embedded SQLite engine via `rusqlite`.
- **Native HTTP Socket Server**: Implement an actual multi-threaded TCP listener for `Serve HTTP` using Rust standard networking.
- **Complete Bytecode Serialization**: Serialize chunk constants and line numbers to enable loading and executing `.lysc` binary files.

### Tooling and Distribution
- **Package Manager Integration**: Package recipes for Homebrew, Winget, and APT (direct standalone binaries are currently distributed via GitHub Releases).
- **Editor Support**: Basic syntax highlighters and Language Server Protocol (LSP) integration for VS Code and Neovim.

---

## Who Should Try Lyslyn?

- **Beginners and Students**: Anyone looking to understand core programming concepts (variables, loops, conditions, functions, and objects) without struggling with syntax errors caused by semicolons, braces, or symbolic operators.
- **Educators**: Teachers who want a language that looks like structured pseudocode but can be executed and tested immediately.
- **Language and Compiler Enthusiasts**: Developers interested in exploring simple-English domain-specific languages (DSLs), stack-based bytecode virtual machines, and Rust-based language implementations.

---

## Contributing

Contributions, bug reports, and suggestions are welcome.

- **Report Bugs**: If you encounter an unexpected error, incorrect output, or parser issue, please open an issue describing the code and expected behavior.
- **Submit Pull Requests**: Check existing issues or propose an improvement before opening a PR. Please ensure all tests pass before submitting (`cargo test` and `cargo run -- test`).
- **Guidelines**: Read [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, coding standards, and testing procedures.

---

## Documentation and Resources

- [Language Specification (`SPEC.md`)](SPEC.md): Formal grammar and core language specifications.
- [Reference Manual (`DOCS.md`)](DOCS.md): Detailed reference guide for language constructs and standard library modules.
- [Changelog (`CHANGELOG.md`)](CHANGELOG.md): History of updates and version changes.
- [License (`LICENSE`)](LICENSE): MIT License.
