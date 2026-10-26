"""Production Telemetry & Prometheus-compatible Metrics module for Lyslyn."""
import time
import os
from typing import Dict, Any, List
from ..values import LyslynBuiltin


class MetricsRegistry:
    def __init__(self):
        self.counters: Dict[str, int] = {
            "http_requests_total": 0,
            "http_errors_total": 0,
            "db_queries_total": 0
        }
        self.latencies: List[float] = []

    def inc(self, counter_name: str, val: int = 1) -> None:
        if counter_name in self.counters:
            self.counters[counter_name] += val
        else:
            self.counters[counter_name] = val

    def observe_latency(self, duration_sec: float) -> None:
        self.latencies.append(float(duration_sec))
        if len(self.latencies) > 10000:
            self.latencies = self.latencies[-10000:]

    def get_percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(p * len(sorted_l))
        return sorted_l[min(idx, len(sorted_l) - 1)]

    def to_prometheus_format(self) -> str:
        out = [
            "# HELP http_requests_total Total number of HTTP requests processed",
            "# TYPE http_requests_total counter",
            f"http_requests_total {self.counters.get('http_requests_total', 0)}",
            "",
            "# HELP http_errors_total Total number of HTTP errors (4xx/5xx)",
            "# TYPE http_errors_total counter",
            f"http_errors_total {self.counters.get('http_errors_total', 0)}",
            "",
            "# HELP db_queries_total Total database queries executed",
            "# TYPE db_queries_total counter",
            f"db_queries_total {self.counters.get('db_queries_total', 0)}",
            "",
            "# HELP http_request_duration_seconds Request duration percentiles",
            "# TYPE http_request_duration_seconds summary",
            f'http_request_duration_seconds{{quantile="0.5"}} {self.get_percentile(0.5):.6f}',
            f'http_request_duration_seconds{{quantile="0.9"}} {self.get_percentile(0.9):.6f}',
            f'http_request_duration_seconds{{quantile="0.99"}} {self.get_percentile(0.99):.6f}',
        ]
        return "\n".join(out) + "\n"


_registry = MetricsRegistry()


def export_module() -> Dict[str, Any]:
    return {
        "inc": LyslynBuiltin("inc", lambda name, val=1: _registry.inc(name, val)),
        "observe": LyslynBuiltin("observe", lambda d: _registry.observe_latency(d), arity=1),
        "export": LyslynBuiltin("export", lambda: _registry.to_prometheus_format(), arity=0),
        "snapshot": LyslynBuiltin("snapshot", lambda: dict(_registry.counters), arity=0),
    }
