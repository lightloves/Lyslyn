"""In-memory thread-safe key-value cache with TTL expiration for Lyslyn.

Zero external dependencies. Supports millisecond-precision TTL expiration,
atomic compute-or-set, cache size monitoring, and active eviction.
"""
import time
import threading
from typing import Any, Dict, List, Optional, Tuple, Callable
from ..values import LyslynBuiltin


class TTLCache:
    """Thread-safe in-memory cache supporting TTL expiration."""
    def __init__(self):
        self._lock = threading.RLock()
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}

    def _is_expired(self, expire_at: Optional[float]) -> bool:
        if expire_at is None:
            return False
        return time.time() > expire_at

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> Any:
        expire_at = (time.time() + float(ttl_seconds)) if ttl_seconds is not None and float(ttl_seconds) > 0 else None
        with self._lock:
            self._store[str(key)] = (value, expire_at)
        return value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._store.get(str(key))
            if entry is None:
                return default
            val, expire_at = entry
            if self._is_expired(expire_at):
                del self._store[str(key)]
                return default
            return val

    def has(self, key: str) -> bool:
        with self._lock:
            entry = self._store.get(str(key))
            if entry is None:
                return False
            val, expire_at = entry
            if self._is_expired(expire_at):
                del self._store[str(key)]
                return False
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            k = str(key)
            if k in self._store:
                del self._store[k]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            self._evict_expired()
            return len(self._store)

    def keys(self) -> List[str]:
        with self._lock:
            self._evict_expired()
            return list(self._store.keys())

    def _evict_expired(self) -> None:
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._store.items() if exp is not None and now > exp]
        for k in expired_keys:
            del self._store[k]

    def get_or_set(self, key: str, compute_fn: Any, ttl_seconds: Optional[float] = None) -> Any:
        """Atomic get or compute and store."""
        with self._lock:
            if self.has(key):
                return self.get(key)

            if callable(compute_fn):
                val = compute_fn()
            elif hasattr(compute_fn, "call"):
                val = compute_fn.call([])
            else:
                val = compute_fn

            self.set(key, val, ttl_seconds)
            return val


_GLOBAL_CACHE = TTLCache()


def export_module() -> Dict[str, Any]:
    return {
        "set": LyslynBuiltin("set", lambda k, v, ttl=None: _GLOBAL_CACHE.set(k, v, ttl)),
        "get": LyslynBuiltin("get", lambda k, d=None: _GLOBAL_CACHE.get(k, d)),
        "has": LyslynBuiltin("has", lambda k: _GLOBAL_CACHE.has(k), arity=1),
        "delete": LyslynBuiltin("delete", lambda k: _GLOBAL_CACHE.delete(k), arity=1),
        "clear": LyslynBuiltin("clear", lambda: _GLOBAL_CACHE.clear(), arity=0),
        "size": LyslynBuiltin("size", lambda: _GLOBAL_CACHE.size(), arity=0),
        "keys": LyslynBuiltin("keys", lambda: _GLOBAL_CACHE.keys(), arity=0),
        "get_or_set": LyslynBuiltin("get_or_set", lambda k, fn, ttl=None: _GLOBAL_CACHE.get_or_set(k, fn, ttl)),
        "new": LyslynBuiltin("new", lambda: TTLCache(), arity=0),
    }
