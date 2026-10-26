"""Global built-in functions for the Lyslyn language."""
from typing import Any, List, Dict
from .values import LyslynBuiltin, LyslynFunction


def _lyslyn_type(val: Any) -> str:
    if val is None:
        return "nil"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, (int, float)):
        return "number"
    if isinstance(val, str):
        return "string"
    if isinstance(val, list):
        return "list"
    if isinstance(val, dict):
        return "object"
    if isinstance(val, (LyslynFunction, LyslynBuiltin)):
        return "function"
    return "object"


def _lyslyn_assert(condition: Any, message: str = "Assertion failed") -> bool:
    if not bool(condition):
        raise AssertionError(str(message))
    return True


def _lyslyn_range(*args: Any) -> List[int]:
    if len(args) == 1:
        return list(range(int(args[0])))
    elif len(args) == 2:
        return list(range(int(args[0]), int(args[1])))
    elif len(args) == 3:
        return list(range(int(args[0]), int(args[1]), int(args[2])))
    raise TypeError(f"range expected 1 to 3 arguments, got {len(args)}")


def _lyslyn_append(lst: List[Any], item: Any) -> List[Any]:
    if not isinstance(lst, list):
        raise TypeError(f"append expected list as first argument, got {_lyslyn_type(lst)}")
    lst.append(item)
    return lst


def _lyslyn_pop(lst: List[Any], index: int = -1) -> Any:
    if not isinstance(lst, list):
        raise TypeError(f"pop expected list as first argument, got {_lyslyn_type(lst)}")
    return lst.pop(int(index))


def _lyslyn_keys(d: Dict[str, Any]) -> List[Any]:
    if not isinstance(d, dict):
        raise TypeError(f"keys expected object/dict, got {_lyslyn_type(d)}")
    return list(d.keys())


def _lyslyn_values(d: Dict[str, Any]) -> List[Any]:
    if not isinstance(d, dict):
        raise TypeError(f"values expected object/dict, got {_lyslyn_type(d)}")
    return list(d.values())


def get_global_builtins() -> Dict[str, Any]:
    from .stdlib.collections_mod import (
        map_fn, filter_fn, reduce_fn, sort_fn,
        reverse_fn, unique_fn, chunk_fn, flatten_fn,
        zip_fn, find_fn, keys_fn, values_fn
    )

    b = {
        "print": LyslynBuiltin("print", lambda *args: print(*args)),
        "println": LyslynBuiltin("println", lambda *args: print(*args)),
        "input": LyslynBuiltin("input", lambda prompt="": input(str(prompt))),
        "len": LyslynBuiltin("len", lambda x: len(x), arity=1),
        "length": LyslynBuiltin("length", lambda x: len(x), arity=1),
        "type": LyslynBuiltin("type", _lyslyn_type, arity=1),
        "str": LyslynBuiltin("str", lambda x: str(x) if x is not None else "nil", arity=1),
        "int": LyslynBuiltin("int", lambda x: int(float(x)), arity=1),
        "float": LyslynBuiltin("float", lambda x: float(x), arity=1),
        "bool": LyslynBuiltin("bool", lambda x: bool(x), arity=1),
        "range": LyslynBuiltin("range", _lyslyn_range),
        "append": LyslynBuiltin("append", _lyslyn_append, arity=2),
        "pop": LyslynBuiltin("pop", _lyslyn_pop),
        "keys": LyslynBuiltin("keys", keys_fn, arity=1),
        "values": LyslynBuiltin("values", values_fn, arity=1),
        "assert": LyslynBuiltin("assert", _lyslyn_assert),
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
    }
    title_aliases = {
        "Assert": b["assert"],
        "Print": b["print"],
        "Println": b["println"],
        "Input": b["input"],
        "Length": b["length"],
        "Type": b["type"],
        "Range": b["range"],
        "Append": b["append"],
        "Keys": b["keys"],
        "Values": b["values"],
        "Map": b["map"],
        "Filter": b["filter"],
        "Reduce": b["reduce"],
        "Sort": b["sort"],
        "Reverse": b["reverse"],
        "Unique": b["unique"],
        "Chunk": b["chunk"],
        "Flatten": b["flatten"],
        "Zip": b["zip"],
        "Find": b["find"],
    }
    b.update(title_aliases)
    return b
