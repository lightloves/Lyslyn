"""Functional collections and array/object processing for Lyslyn.

Provides high-order algorithms: Map, Filter, Reduce, Sort, Unique, Chunk,
GroupBy, Flatten, Zip, and Object manipulations.
"""
from typing import Any, List, Dict, Optional
from ..values import LyslynBuiltin
from ..diagnostics import RuntimeError_


def _invoke(fn: Any, *args: Any) -> Any:
    """Invoke either a Lyslyn closure/function or standard Python callable."""
    if hasattr(fn, "call"):
        return fn.call(list(args))
    elif callable(fn):
        return fn(*args)
    raise RuntimeError_(f"Target is not a callable function, got {type(fn).__name__}")


def map_fn(items: List[Any], fn: Any) -> List[Any]:
    if not isinstance(items, list):
        raise RuntimeError_(f"Map expects a list, got {type(items).__name__}")
    return [_invoke(fn, item) for item in items]


def filter_fn(items: List[Any], fn: Any) -> List[Any]:
    if not isinstance(items, list):
        raise RuntimeError_(f"Filter expects a list, got {type(items).__name__}")
    return [item for item in items if bool(_invoke(fn, item))]


def reduce_fn(items: List[Any], fn: Any, initial: Any = None) -> Any:
    if not isinstance(items, list):
        raise RuntimeError_(f"Reduce expects a list, got {type(items).__name__}")
    if not items and initial is None:
        raise RuntimeError_("Reduce on empty list with no initial value")

    it = iter(items)
    acc = initial if initial is not None else next(it)
    for item in it:
        acc = _invoke(fn, acc, item)
    return acc


def sort_fn(items: List[Any], key_fn: Optional[Any] = None, reverse: bool = False) -> List[Any]:
    if not isinstance(items, list):
        raise RuntimeError_(f"Sort expects a list, got {type(items).__name__}")
    res = list(items)
    if key_fn is not None:
        res.sort(key=lambda x: _invoke(key_fn, x), reverse=bool(reverse))
    else:
        res.sort(reverse=bool(reverse))
    return res


def reverse_fn(items: List[Any]) -> List[Any]:
    if not isinstance(items, list):
        raise RuntimeError_(f"Reverse expects a list, got {type(items).__name__}")
    return list(reversed(items))


def unique_fn(items: List[Any]) -> List[Any]:
    if not isinstance(items, list):
        raise RuntimeError_(f"Unique expects a list, got {type(items).__name__}")
    seen = set()
    result = []
    for item in items:
        try:
            if item not in seen:
                seen.add(item)
                result.append(item)
        except TypeError:
            if item not in result:
                result.append(item)
    return result


def chunk_fn(items: List[Any], size: int) -> List[List[Any]]:
    if not isinstance(items, list):
        raise RuntimeError_(f"Chunk expects a list, got {type(items).__name__}")
    s = int(size)
    if s <= 0:
        raise RuntimeError_("Chunk size must be greater than zero")
    return [items[i:i + s] for i in range(0, len(items), s)]


def flatten_fn(items: List[Any]) -> List[Any]:
    if not isinstance(items, list):
        raise RuntimeError_(f"Flatten expects a list, got {type(items).__name__}")
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def zip_fn(list1: List[Any], list2: List[Any]) -> List[List[Any]]:
    if not isinstance(list1, list) or not isinstance(list2, list):
        raise RuntimeError_("Zip requires two list arguments")
    return [[a, b] for a, b in zip(list1, list2)]


def find_fn(items: List[Any], predicate: Any) -> Any:
    if not isinstance(items, list):
        raise RuntimeError_(f"Find expects a list, got {type(items).__name__}")
    for item in items:
        if bool(_invoke(predicate, item)):
            return item
    return None


def find_index_fn(items: List[Any], predicate: Any) -> int:
    if not isinstance(items, list):
        raise RuntimeError_(f"FindIndex expects a list, got {type(items).__name__}")
    for i, item in enumerate(items):
        if bool(_invoke(predicate, item)):
            return i
    return -1


def every_fn(items: List[Any], predicate: Any) -> bool:
    if not isinstance(items, list):
        raise RuntimeError_(f"Every expects a list, got {type(items).__name__}")
    return all(bool(_invoke(predicate, item)) for item in items)


def some_fn(items: List[Any], predicate: Any) -> bool:
    if not isinstance(items, list):
        raise RuntimeError_(f"Some expects a list, got {type(items).__name__}")
    return any(bool(_invoke(predicate, item)) for item in items)


def group_by_fn(items: List[Any], key_fn: Any) -> Dict[str, List[Any]]:
    if not isinstance(items, list):
        raise RuntimeError_(f"GroupBy expects a list, got {type(items).__name__}")
    result: Dict[str, List[Any]] = {}
    for item in items:
        k = str(_invoke(key_fn, item))
        if k not in result:
            result[k] = []
        result[k].append(item)
    return result


def keys_fn(d: Dict[str, Any]) -> List[str]:
    if not isinstance(d, dict):
        raise RuntimeError_(f"Keys expects a dictionary, got {type(d).__name__}")
    return list(d.keys())


def values_fn(d: Dict[str, Any]) -> List[Any]:
    if not isinstance(d, dict):
        raise RuntimeError_(f"Values expects a dictionary, got {type(d).__name__}")
    return list(d.values())


def entries_fn(d: Dict[str, Any]) -> List[List[Any]]:
    if not isinstance(d, dict):
        raise RuntimeError_(f"Entries expects a dictionary, got {type(d).__name__}")
    return [[k, v] for k, v in d.items()]


def merge_fn(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(d1, dict) or not isinstance(d2, dict):
        raise RuntimeError_("Merge requires two dictionary arguments")
    merged = dict(d1)
    merged.update(d2)
    return merged


def export_module() -> Dict[str, Any]:
    return {
        "map": LyslynBuiltin("map", map_fn, arity=2),
        "filter": LyslynBuiltin("filter", filter_fn, arity=2),
        "reduce": LyslynBuiltin("reduce", reduce_fn),
        "sort": LyslynBuiltin("sort", sort_fn),
        "reverse": LyslynBuiltin("reverse", reverse_fn, arity=1),
        "unique": LyslynBuiltin("unique", unique_fn, arity=1),
        "chunk": LyslynBuiltin("chunk", chunk_fn, arity=2),
        "flatten": LyslynBuiltin("flatten", flatten_fn, arity=1),
        "zip": LyslynBuiltin("zip", zip_fn, arity=2),
        "find": LyslynBuiltin("find", find_fn, arity=2),
        "find_index": LyslynBuiltin("find_index", find_index_fn, arity=2),
        "every": LyslynBuiltin("every", every_fn, arity=2),
        "some": LyslynBuiltin("some", some_fn, arity=2),
        "group_by": LyslynBuiltin("group_by", group_by_fn, arity=2),
        "keys": LyslynBuiltin("keys", keys_fn, arity=1),
        "values": LyslynBuiltin("values", values_fn, arity=1),
        "entries": LyslynBuiltin("entries", entries_fn, arity=1),
        "merge": LyslynBuiltin("merge", merge_fn, arity=2),
    }
