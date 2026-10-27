use lyslyn::compiler::Compiler;
use lyslyn::lexer::Scanner;
use lyslyn::parser::Parser;
use lyslyn::values::Value;
use lyslyn::vm::VM;

fn run_code(source: &str) -> (Value, Vec<String>) {
    let mut scanner = Scanner::new(source, "<test>");
    let tokens = scanner.scan_tokens().expect("Scan failed");

    let mut parser = Parser::new(tokens, "<test>", source);
    let program = parser.parse().expect("Parse failed");

    let mut compiler = Compiler::new("<test>", source);
    let chunk = compiler.compile(&program).expect("Compile failed");

    let mut vm = VM::new(None);
    vm.capture_output = true;
    let res = vm.run(chunk).expect("Execution failed");
    (res, vm.output)
}

#[test]
fn test_basic_variables_and_arithmetic() {
    let code = r#"
Set a to 10
Set b to 25
Set total to a + b * 2
Say total
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["60"]);
}

#[test]
fn test_natural_english_comparisons() {
    let code = r#"
Set score to 95
If score is at least 90:
    Say "Grade A"
Otherwise:
    Say "Retake"

If score is positive and score is odd:
    Say "Score is positive and odd"
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["Grade A", "Score is positive and odd"]);
}

#[test]
fn test_while_and_repeat_loops() {
    let code = r#"
Set counter to 1
While counter is at most 3:
    Say counter
    Increase counter by 1

Repeat 2 times:
    Say "Repeating"
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["1", "2", "3", "Repeating", "Repeating"]);
}

#[test]
fn test_functions_and_recursion() {
    let code = r#"
Create a function called factorial with n:
    If n is at most 1:
        Return 1
    Return n * factorial(n - 1)

Set res to factorial(5)
Say res
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["120"]);
}

#[test]
fn test_simple_english_collections() {
    let code = r#"
Set fruits to a list of "Apple", "Banana" and "Cherry"
Say fruits[0]
Say fruits.length

For every f in fruits:
    Say f
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["Apple", "3", "Apple", "Banana", "Cherry"]);
}

#[test]
fn test_stdlib_math_and_json() {
    let code = r#"
Get math
Get json

Set root to math.sqrt(144)
Say root

Set raw to "{\"user\": \"raj\", \"active\": true}"
Set parsed to json.parse(raw)
Say parsed.user
Say parsed.active
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["12", "raj", "true"]);
}

#[test]
fn test_oop_classes_and_inheritance() {
    let code = r#"
Define a class called Animal:
    To initialize with name:
        Set this.name to name

    Method speak:
        Return this.name + " speaks"

Define a class called Dog inheriting from Animal:
    To initialize with name, breed:
        Call parent with name
        Set this.breed to breed

    Method speak:
        Return this.name + " barks"

Set d to a new Dog with "Rex", "Husky"
Say d.speak()
Say d.breed
Say d is an instance of Animal
Say d is an instance of Dog
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["Rex barks", "Husky", "true", "true"]);
}

#[test]
fn test_type_reflection_and_regex() {
    let code = r#"
Get regex
Say type("text")
Say type(100)
Say 50 is an integer
Say "email@test.com" is a string
Say regex.is_match("^[a-z]+@[a-z]+\\.[a-z]+$", "email@test.com")
"#;
    let (_, out) = run_code(code);
    assert_eq!(out, vec!["string", "int", "true", "true", "true"]);
}
