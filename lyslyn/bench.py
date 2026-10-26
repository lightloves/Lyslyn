"""Industrial Benchmarking Harness for Lyslyn."""
import time
import os
from typing import Dict, Any, List, Callable
from .lexer import Lexer
from .parser import Parser
from .interpreter import Interpreter
from .values import LyslynFunction


class BenchmarkResult:
    def __init__(self, name: str, iterations: int, total_time: float, min_time: float, max_time: float):
        self.name = name
        self.iterations = iterations
        self.total_time = total_time
        self.min_time = min_time
        self.max_time = max_time

    @property
    def avg_time(self) -> float:
        return self.total_time / self.iterations if self.iterations else 0

    @property
    def ops_per_sec(self) -> float:
        return self.iterations / self.total_time if self.total_time > 0 else 0


def run_benchmark(filepath: str, iterations: int = 100) -> List[BenchmarkResult]:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tokens = Lexer(source, filename=filepath).tokenize()
    program = Parser(tokens, filename=filepath, source=source).parse()
    interp = Interpreter(filename=filepath, source=source)
    interp.interpret(program)

    bench_funcs: Dict[str, LyslynFunction] = {}
    for k, v in interp.environment.values.items():
        if (k.startswith("bench_") or k.startswith("benchmark_")) and isinstance(v, LyslynFunction):
            bench_funcs[k] = v

    if not bench_funcs:
        times = []
        for _ in range(iterations):
            sub_interp = Interpreter(filename=filepath, source=source)
            t0 = time.perf_counter()
            sub_interp.interpret(program)
            times.append(time.perf_counter() - t0)
        return [BenchmarkResult("file_execution", iterations, sum(times), min(times), max(times))]

    results = []
    for name, fn in bench_funcs.items():
        for _ in range(5):
            interp.call_function(fn, [])

        times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            interp.call_function(fn, [])
            times.append(time.perf_counter() - t0)

        results.append(BenchmarkResult(name, iterations, sum(times), min(times), max(times)))

    return results


def print_benchmark_table(results: List[BenchmarkResult], filename: str) -> None:
    print(f"\n\033[1m┌────────────────────────────────────────────────────────────────────────┐\033[0m")
    print(f"\033[1m│                      LYSLYN BENCHMARK REPORT                           │\033[0m")
    print(f"\033[1m├────────────────────────────────────────────────────────────────────────┤\033[0m")
    print(f"  Target: \033[96m{filename}\033[0m\n")
    print(f"  {'Benchmark':<24} {'Iterations':<12} {'Avg Time':<14} {'Ops / Sec':<16}")
    print(f"  {'-'*22:<24} {'-'*10:<12} {'-'*12:<14} {'-'*14:<16}")

    for r in results:
        avg_str = f"{r.avg_time * 1000:.3f} ms" if r.avg_time >= 0.001 else f"{r.avg_time * 1e6:.1f} µs"
        ops_str = f"{r.ops_per_sec:,.0f} op/s"
        print(f"  \033[1m{r.name:<24}\033[0m {r.iterations:<12} \033[92m{avg_str:<14}\033[0m \033[96m{ops_str:<16}\033[0m")

    print(f"\n\033[1m└────────────────────────────────────────────────────────────────────────┘\033[0m\n")
