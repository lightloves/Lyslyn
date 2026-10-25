# Lyslyn Programming Language Specification
**Version 1.0.0**

Lyslyn is a modern programming language designed to make code feel like clear, structured English while retaining the precision, composability, and performance of a production-ready general-purpose language.

---

## 1. Design Principles

1. **Structured English Readability**: Code should read naturally without cryptic punctuation or excessive boilerplate.
2. **Unambiguous Determinism**: Lyslyn is a formal programming language with a context-free, deterministic grammar, not an unpredictable natural language model. Every construct has exact operational semantics.
3. **Batteries Included**: Rich first-class standard library for HTTP, JSON, Filesystem, Math, Strings, Async, and Collections.
4. **Developer Experience First**: Clear compiler diagnostics with line and column numbers, code frame snippets, formatted suggestions, a built-in test runner, project initializer, and code formatter.

---

## 2. Lexical Structure

### 2.1 Identifiers & Keywords
Identifiers start with an ASCII letter or underscore `[a-zA-Z_]`, followed by any number of letters, digits, or underscores.

Keywords are case-insensitive or standardized to Title/lowercase:
- Declarations: `Set`, `Let`, `Constant`, `Define`, `Create`
- Control Flow: `If`, `Otherwise if`, `Else if`, `Otherwise`, `Else`, `While`, `For`, `Each`, `In`, `Repeat`, `Times`, `Break`, `Continue`, `Return`
- Functions & Types: `Function`, `Type`, `Method`, `Async`, `Wait for`, `Await`
- Error Handling: `Try`, `Catch`, `Finally`, `Raise`, `Throw`
- Network & I/O: `Send`, `Request`, `To`, `Save`, `Response`, `As`, `Print`, `Ask`
- Logical & Comparisons: `and`, `or`, `not`, `is`, `equal`, `at`, `least`, `most`, `greater`, `than`, `less`
- Literals: `true` / `yes`, `false` / `no`, `nil` / `null` / `nothing`

### 2.2 Comments
- Single-line comments start with `#` or `//` and extend to the end of the line:
  ```lys
  # This is a comment in Lyslyn
  // This is also supported
  ```
- Multi-line comments use `/* ... */`:
  ```lys
  /* Multi-line
     documentation or comment */
  ```

### 2.3 Blocks and Indentation
Lyslyn uses indentation (spaces or tabs) to structure blocks of code, initiated with a colon `:` at the end of the header statement:
```lys
If age is at least 18:
    Print "Adult"
Otherwise:
    Print "Minor"
```

---

## 3. Formal Grammar (EBNF)

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
                | type_def
                | return_stmt
                | break_stmt
                | continue_stmt
                | try_stmt
                | raise_stmt
                | import_stmt
                | http_stmt
                | print_stmt
                | expr_stmt ;

set_stmt        = ( "Set" | "Let" ) target ( "to" | "=" ) expr ;
const_stmt      = ( "Constant" | "Define constant" ) IDENTIFIER ( "is" | "as" | "=" ) expr ;
change_stmt     = ( "Increase" target "by" expr )
                | ( "Decrease" target "by" expr )
                | ( "Change" target "to" expr ) ;

target          = IDENTIFIER { "." IDENTIFIER | "[" expr "]" } ;

if_stmt         = "If" expr ":" block
                  { ( "Otherwise if" | "Else if" ) expr ":" block }
                  [ ( "Otherwise" | "Else" ) ":" block ] ;

while_stmt      = "While" expr ":" block ;
for_stmt        = "For" [ "each" ] IDENTIFIER "in" expr ":" block ;
repeat_stmt     = "Repeat" expr "times" ":" block ;

func_def        = [ "Async" ] ( "Define function" | "Create a function called" | "Function" )
                  IDENTIFIER [ "with" param_list | "(" [ param_list ] ")" ] ":" block ;

param_list      = IDENTIFIER { "," IDENTIFIER } ;

return_stmt     = "Return" [ expr | "nothing" ] ;
break_stmt      = "Break" [ "out of loop" ] ;
continue_stmt   = "Continue" [ "to next iteration" ] ;

try_stmt        = "Try" ":" block
                  "Catch" [ "error" ] [ "as" IDENTIFIER ] ":" block
                  [ "Finally" ":" block ] ;

raise_stmt      = ( "Raise error" | "Throw" ) expr ;

import_stmt     = "Import" ( STRING | IDENTIFIER ) [ "as" IDENTIFIER ]
                | "From" ( STRING | IDENTIFIER ) "import" IDENTIFIER { "," IDENTIFIER } ;

http_stmt       = "Send a" HTTP_METHOD "request to" expr ":" block
                | "Send a" HTTP_METHOD "request to" expr "save" [ "the" ] "response as" IDENTIFIER ;

HTTP_METHOD     = "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "HEAD" ;

print_stmt      = "Print" expr { "," expr } ;

expr_stmt       = expr ;

block           = INDENT { statement } DEDENT ;

expr            = logic_or ;
logic_or        = logic_and { "or" logic_and } ;
logic_and       = logic_not { "and" logic_not } ;
logic_not       = ( "not" | "!" ) logic_not | comparison ;

comparison      = term { comp_op term } ;
comp_op         = "is equal to" | "==" | "equals"
                | "is not equal to" | "!=" | "does not equal"
                | "is greater than or equal to" | "is at least" | ">="
                | "is less than or equal to" | "is at most" | "<="
                | "is greater than" | ">"
                | "is less than" | "<"
                | "is in" | "in"
                | "is not in" | "not in" ;

term            = factor { ( "+" | "-" ) factor } ;
factor          = unary { ( "*" | "/" | "%" ) unary } ;
unary           = ( "-" | "+" | "Wait for" | "Await" ) unary | call_or_access ;

call_or_access  = primary { "(" [ arg_list ] ")" | "." IDENTIFIER | "[" expr "]" } ;
arg_list        = expr { "," expr } ;

primary         = NUMBER
                | STRING
                | "true" | "yes"
                | "false" | "no"
                | "nil" | "null" | "nothing"
                | IDENTIFIER
                | list_literal
                | map_literal
                | "(" expr ")" ;

list_literal    = "[" [ expr { "," expr } ] "]" ;
map_literal     = "{" [ map_entry { "," map_entry } ] "}" ;
map_entry       = ( STRING | IDENTIFIER ) ( ":" | "=" ) expr ;
```

---

## 4. Semantics & Data Types

### 4.1 Data Types
- **Numbers**: Unified numerical system representing 64-bit integers and IEEE-754 double precision floats. Arithmetic automatically promotes integer to float on division or when combined with floats.
- **Strings**: UTF-8 immutable sequences of characters. Supports string interpolation using `{expression}`:
  ```lys
  Set name to "Lyslyn"
  Print "Welcome to {name}!"
  ```
- **Booleans**: `true` (synonym: `yes`) and `false` (synonym: `no`).
- **Nil**: Represents the absence of a value (`nil`, `null`, `nothing`).
- **Lists**: Dynamic ordered arrays, indexed from 0:
  ```lys
  Set fruits to ["apple", "banana", "cherry"]
  Set first to fruits[0]
  ```
- **Dictionaries / Objects**: Key-value maps supporting string or identifier keys, accessed via dot notation `user.name` or index `user["name"]`.
- **Functions**: First-class citizens. Can be passed as arguments, returned from functions, and assigned to variables. Full lexical scoping and closures.
- **Modules**: Standalone namespaces imported with `Import`.

---

## 5. First-Class HTTP Syntax
Lyslyn provides native syntactic sugar for HTTP requests alongside the `http` module:

```lys
Send a POST request to "https://api.example.com/users":
    headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    }
    data: {
        "name": "Raj",
        "role": "Engineer"
    }
    timeout: 10
    save response as resp

If resp.ok:
    Print "User created with status:", resp.status
    Print "Response data:", resp.json()
Otherwise:
    Print "Request failed:", resp.status
```

---

## 6. Standard Library Modules

1. **`text` / `strings`**: `trim`, `uppercase`, `lowercase`, `split`, `join`, `replace`, `starts_with`, `ends_with`, `contains`.
2. **`math`**: `round`, `floor`, `ceil`, `abs`, `sqrt`, `min`, `max`, `pow`, `sin`, `cos`, `pi`, `e`.
3. **`collections` / `lists`**: `append`, `pop`, `length`, `contains`, `slice`, `sort`, `reverse`, `map`, `filter`, `reduce`.
4. **`files` / `fs`**: `read_text`, `write_text`, `append_text`, `exists`, `delete`, `list_directory`, `create_directory`.
5. **`json`**: `parse(text)`, `stringify(value, indent)`.
6. **`http`**: `get(url, options)`, `post(url, options)`, `put`, `delete`, `patch`, `request`.
7. **`time`**: `now()`, `sleep(seconds)`, `timestamp()`, `format(fmt)`.
8. **`random`**: `random()`, `integer(min, max)`, `choice(list)`, `shuffle(list)`.
9. **`env`**: `get(key, default)`, `set(key, value)`, `has(key)`.
10. **`log`**: `info(msg)`, `warn(msg)`, `error(msg)`, `debug(msg)`.
