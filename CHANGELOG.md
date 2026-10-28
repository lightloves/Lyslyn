# Changelog

All notable changes to Lyslyn are documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [1.0.0] - 2026-10-28

### Added
- Complete rewrite from reference Python interpreter to an independent, native Rust implementation.
- 64-bit stack-based Virtual Machine with 74 bytecode instructions.
- Handwritten lexer with indentation tracking and position-accurate source spans.
- Recursive-descent parser producing strongly-typed Abstract Syntax Trees.
- Pure Simple English syntax support for variables, constants, collections, loops, conditionals, and functions.
- Full Object-Oriented Programming: classes, constructors, methods, inheritance, and Call parent delegation.
- Dynamic runtime reflection: type(), is an instance of, and English type predicates.
- Native standard library with 16 Rust modules: math, text, regex, os, fs, json, http, server, jwt, cache, collections, crypto, validation, db, time, and env.
- Developer toolchain CLI (lyslyn / lys) supporting run, -c, check, build, disasm, bench, repl, test, init, install, remove, and compile.
- Standalone single-binary compilation packaging the native VM and application into an executable.
- Multi-platform GitHub Actions CI/CD supporting Linux x64, macOS, Windows x64, and Android ARM64 cross-compilation.
- Comprehensive test suite with 11 native Lyslyn test suites and 8 Rust integration tests.
