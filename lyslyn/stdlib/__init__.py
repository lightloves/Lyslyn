"""Standard library registry for Lyslyn."""
from typing import Dict, Any, Optional
from ..values import LyslynModule
from . import http as http_mod
from . import json_mod
from . import files as files_mod
from . import text as text_mod
from . import math_mod
from . import db as db_mod
from . import server_mod
from . import validation as validation_mod
from . import crypto_mod
from . import tasks_mod
from .misc_mods import (
    export_time_module,
    export_random_module,
    export_env_module,
    export_log_module,
)


STDLIB_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Core general-purpose
    "http": http_mod.export_module(),
    "json": json_mod.export_module(),
    "files": files_mod.export_module(),
    "fs": files_mod.export_module(),
    "text": text_mod.export_module(),
    "strings": text_mod.export_module(),
    "math": math_mod.export_module(),
    "time": export_time_module(),
    "random": export_random_module(),
    "env": export_env_module(),
    "log": export_log_module(),

    # Backend & Server Stack
    "db": db_mod.export_module(),
    "database": db_mod.export_module(),
    "server": server_mod.export_module(),
    "validation": validation_mod.export_module(),
    "crypto": crypto_mod.export_module(),
    "tasks": tasks_mod.export_module(),
}


def get_stdlib_module(name: str) -> Optional[LyslynModule]:
    """Retrieve a standard library module by name."""
    name = name.lower()
    if name in STDLIB_REGISTRY:
        return LyslynModule(name, STDLIB_REGISTRY[name])
    return None
