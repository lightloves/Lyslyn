# Contributing to Lyslyn

Thank you for your interest in contributing to Lyslyn!

## Development Setup

Lyslyn is written in standard, memory-safe Rust (edition 2021).

### Prerequisites
- Rust stable (1.75+) and Cargo

### Building from Source
```bash
cargo build --release --locked
```

The resulting binary will be located at `target/release/lyslyn`.

## Running Tests

Before submitting any pull request, ensure all tests pass:

```bash
# Run Rust integration tests
cargo test --locked

# Run Lyslyn native test suite
cargo run --release -- test

# Verify all examples run cleanly
for f in examples/*.lys; do
  cargo run --release -- "$f"
done
```

## Code Style & Formatting

- Code in Lyslyn should always be clear, readable Simple English.
- Run `cargo fmt --check` to verify Rust code formatting.
- Ensure no warnings or errors are introduced.

## Pull Request Process

1. Fork the repository and create your branch from `master`.
2. Ensure new features include corresponding test suites in `tests/`.
3. Submit a pull request describing the motivation and changes made.
