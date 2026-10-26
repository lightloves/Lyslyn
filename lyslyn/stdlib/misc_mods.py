"""Time, random, env, and log modules for Lyslyn."""
import os
import time
import random
from datetime import datetime
from typing import Any, Dict, List
from ..values import LyslynBuiltin


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


def _load_dotenv_file(filepath: str = ".env") -> int:
    """Parse and load variables from a .env file into os.environ."""
    if not os.path.isfile(filepath):
        return 0
    count = 0
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                        v = v[1:-1]
                    if k not in os.environ:
                        os.environ[k] = v
                        count += 1
    except Exception:
        pass
    return count

_load_dotenv_file(".env")


def env_get(key: str, default: Any = None) -> Any:
    return os.environ.get(str(key), default)

def env_get_int(key: str, default: Any = None) -> Any:
    val = os.environ.get(str(key))
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default

def env_get_bool(key: str, default: Any = False) -> bool:
    val = os.environ.get(str(key))
    if val is None:
        return bool(default)
    return str(val).lower() in ("true", "1", "yes", "on", "t")

def env_require(key: str) -> str:
    val = os.environ.get(str(key))
    if val is None or val == "":
        from ..diagnostics import RuntimeError_
        raise RuntimeError_(f"Missing required environment variable '{key}'")
    return val

def env_set(key: str, val: Any) -> None:
    os.environ[str(key)] = str(val)

def env_has(key: str) -> bool:
    return str(key) in os.environ

def env_all() -> Dict[str, str]:
    return dict(os.environ)

def export_env_module() -> Dict[str, Any]:
    return {
        "get": LyslynBuiltin("get", env_get),
        "get_int": LyslynBuiltin("get_int", env_get_int),
        "get_bool": LyslynBuiltin("get_bool", env_get_bool),
        "require": LyslynBuiltin("require", env_require, arity=1),
        "set": LyslynBuiltin("set", env_set, arity=2),
        "has": LyslynBuiltin("has", env_has, arity=1),
        "all": LyslynBuiltin("all", env_all, arity=0),
        "load": LyslynBuiltin("load", _load_dotenv_file),
    }


_LOG_LEVELS = {"debug": 10, "info": 20, "warn": 30, "warning": 30, "error": 40}
_CURRENT_LOG_LEVEL = 20
_LOG_FORMAT = "text"


def log_set_level(level: str) -> None:
    global _CURRENT_LOG_LEVEL
    lvl = str(level).lower()
    if lvl in _LOG_LEVELS:
        _CURRENT_LOG_LEVEL = _LOG_LEVELS[lvl]


def log_set_format(fmt: str) -> None:
    global _LOG_FORMAT
    fmt_clean = str(fmt).lower()
    if fmt_clean in ("text", "json"):
        _LOG_FORMAT = fmt_clean


def _emit_log(level_name: str, color_code: str, *args: Any) -> None:
    lvl_num = _LOG_LEVELS.get(level_name.lower(), 20)
    if lvl_num < _CURRENT_LOG_LEVEL:
        return

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    context = None
    messages = list(args)
    if len(messages) > 1 and isinstance(messages[-1], dict):
        context = messages.pop()

    msg_str = " ".join(str(x) for x in messages)

    if _LOG_FORMAT == "json":
        import json
        entry = {
            "timestamp": now_iso,
            "level": level_name.upper(),
            "message": msg_str
        }
        if context:
            entry["context"] = context
        print(json.dumps(entry))
    else:
        ctx_str = f" {context}" if context else ""
        print(f"\033[90m{now_iso}\033[0m {color_code}[{level_name.upper()}]\033[0m {msg_str}{ctx_str}")


def log_info(*args: Any) -> None:
    _emit_log("info", "\033[94m", *args)

def log_warn(*args: Any) -> None:
    _emit_log("warn", "\033[93m", *args)

def log_error(*args: Any) -> None:
    _emit_log("error", "\033[91m", *args)

def log_debug(*args: Any) -> None:
    _emit_log("debug", "\033[90m", *args)


def export_log_module() -> Dict[str, Any]:
    return {
        "info": LyslynBuiltin("info", log_info),
        "warn": LyslynBuiltin("warn", log_warn),
        "error": LyslynBuiltin("error", log_error),
        "debug": LyslynBuiltin("debug", log_debug),
        "set_level": LyslynBuiltin("set_level", log_set_level, arity=1),
        "set_format": LyslynBuiltin("set_format", log_set_format, arity=1),
    }
