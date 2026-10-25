"""Filesystem standard library module for Lyslyn."""
import os
import shutil
from typing import Any, Dict, List
from ..values import LyslynBuiltin


def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Could not read file '{path}': {e}")


def write_text(path: str, content: str) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))
        return True
    except Exception as e:
        raise IOError(f"Could not write to file '{path}': {e}")


def append_text(path: str, content: str) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(content))
        return True
    except Exception as e:
        raise IOError(f"Could not append to file '{path}': {e}")


def exists(path: str) -> bool:
    return os.path.exists(path)


def delete(path: str) -> bool:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True
    except Exception as e:
        raise IOError(f"Could not delete '{path}': {e}")


def list_directory(path: str = ".") -> List[str]:
    try:
        return os.listdir(path)
    except Exception as e:
        raise IOError(f"Could not list directory '{path}': {e}")


def create_directory(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        raise IOError(f"Could not create directory '{path}': {e}")


def export_module() -> Dict[str, Any]:
    return {
        "read_text": LyslynBuiltin("read_text", read_text, arity=1),
        "write_text": LyslynBuiltin("write_text", write_text, arity=2),
        "append_text": LyslynBuiltin("append_text", append_text, arity=2),
        "exists": LyslynBuiltin("exists", exists, arity=1),
        "delete": LyslynBuiltin("delete", delete, arity=1),
        "list_directory": LyslynBuiltin("list_directory", list_directory),
        "create_directory": LyslynBuiltin("create_directory", create_directory, arity=1),
    }
