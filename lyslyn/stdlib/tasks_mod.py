"""Background asynchronous tasks and worker queue module for Lyslyn."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Callable, List
from ..values import LyslynBuiltin

_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="LyslynWorker")


def dispatch_task(func: Any, args: Any = None) -> bool:
    if args is None:
        args_list = []
    elif isinstance(args, (list, tuple)):
        args_list = list(args)
    else:
        args_list = [args]

    def runner():
        try:
            if callable(func):
                func(*args_list)
        except Exception as e:
            print(f"\033[91m[Worker Error]\033[0m Task execution failed: {e}")

    _executor.submit(runner)
    return True


def export_module() -> Dict[str, Any]:
    return {
        "dispatch": LyslynBuiltin("dispatch", dispatch_task),
    }
