"""Time, random, env, and log modules for Lyslyn."""
import os
import time
import random
from datetime import datetime
from typing import Any, Dict, List
from ..values import LyslynBuiltin


# ==================== TIME ====================
def time_now() -> str:
    return datetime.now().isoformat()

def time_sleep(seconds: Any) -> None:
    time.sleep(float(seconds))

def time_timestamp() -> float:
    return time.time()

def time_format(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now().strftime(str(fmt))

def export_time_module() -> Dict[str, Any]:
    return {
        "now": LyslynBuiltin("now", time_now, arity=0),
        "sleep": LyslynBuiltin("sleep", time_sleep, arity=1),
        "timestamp": LyslynBuiltin("timestamp", time_timestamp, arity=0),
        "format": LyslynBuiltin("format", time_format),
    }


# ==================== RANDOM ====================
def rand_random() -> float:
    return random.random()

def rand_integer(min_val: Any, max_val: Any) -> int:
    return random.randint(int(min_val), int(max_val))

def rand_choice(items: List[Any]) -> Any:
    if not items:
        return None
    return random.choice(items)

def rand_shuffle(items: List[Any]) -> List[Any]:
    cp = list(items)
    random.shuffle(cp)
    return cp

def export_random_module() -> Dict[str, Any]:
    return {
        "random": LyslynBuiltin("random", rand_random, arity=0),
        "integer": LyslynBuiltin("integer", rand_integer, arity=2),
        "choice": LyslynBuiltin("choice", rand_choice, arity=1),
        "shuffle": LyslynBuiltin("shuffle", rand_shuffle, arity=1),
    }


# ==================== ENV ====================
def env_get(key: str, default: Any = None) -> Any:
    return os.environ.get(str(key), default)

def env_set(key: str, val: Any) -> None:
    os.environ[str(key)] = str(val)

def env_has(key: str) -> bool:
    return str(key) in os.environ

def export_env_module() -> Dict[str, Any]:
    return {
        "get": LyslynBuiltin("get", env_get),
        "set": LyslynBuiltin("set", env_set, arity=2),
        "has": LyslynBuiltin("has", env_has, arity=1),
    }


# ==================== LOG ====================
def log_info(*args: Any) -> None:
    print(f"\033[94m[INFO]\033[0m {' '.join(str(x) for x in args)}")

def log_warn(*args: Any) -> None:
    print(f"\033[93m[WARN]\033[0m {' '.join(str(x) for x in args)}")

def log_error(*args: Any) -> None:
    print(f"\033[91m[ERROR]\033[0m {' '.join(str(x) for x in args)}")

def log_debug(*args: Any) -> None:
    print(f"\033[90m[DEBUG]\033[0m {' '.join(str(x) for x in args)}")

def export_log_module() -> Dict[str, Any]:
    return {
        "info": LyslynBuiltin("info", log_info),
        "warn": LyslynBuiltin("warn", log_warn),
        "error": LyslynBuiltin("error", log_error),
        "debug": LyslynBuiltin("debug", log_debug),
    }
