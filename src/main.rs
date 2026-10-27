use lyslyn::cli::run_cli;
use std::env;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    if let Err(code) = run_cli(args) {
        process::exit(code);
    }
}
