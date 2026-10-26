"""Production-grade Database (SQLite / SQL Query Engine & ORM) module for Lyslyn."""
import sqlite3
import threading
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from ..values import LyslynBuiltin


class DatabaseManager:
    def __init__(self, default_path: str = "app.db"):
        self.default_path = default_path
        self._local = threading.local()

    def get_connection(self, path: Optional[str] = None) -> sqlite3.Connection:
        db_path = path or self.default_path
        if not hasattr(self._local, "connections"):
            self._local.connections = {}
        if db_path not in self._local.connections:
            # Enable row factory for dictionary-like column access
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable foreign keys and WAL mode for production concurrency
            conn.execute("PRAGMA foreign_keys = ON;")
            if db_path != ":memory:":
                try:
                    conn.execute("PRAGMA journal_mode = WAL;")
                except Exception:
                    pass
            self._local.connections[db_path] = conn
        return self._local.connections[db_path]

    def connect(self, path: str = "app.db") -> "DatabaseManager":
        self.default_path = str(path)
        self.get_connection(self.default_path)
        return self

    def query(self, sql: str, params: Any = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        p = self._normalize_params(params)
        cursor = conn.cursor()
        try:
            cursor.execute(sql, p)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            cursor.close()

    def execute(self, sql: str, params: Any = None) -> Dict[str, Any]:
        conn = self.get_connection()
        p = self._normalize_params(params)
        cursor = conn.cursor()
        try:
            cursor.execute(sql, p)
            conn.commit()
            return {
                "rows_affected": cursor.rowcount,
                "last_id": cursor.lastrowid
            }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Database execute error: {e}")
        finally:
            cursor.close()

    def create_table(self, table: str, schema: Dict[str, str]) -> bool:
        cols = []
        for col_name, col_type in schema.items():
            cols.append(f"{col_name} {col_type}")
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(cols)});"
        self.execute(sql)
        return True

    def table_exists(self, table: str) -> bool:
        res = self.query("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", [table])
        return len(res) > 0

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data:
            raise ValueError("Cannot insert empty data dictionary")
        columns = list(data.keys())
        placeholders = ["?"] * len(columns)
        values = [data[k] for k in columns]

        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"
        res = self.execute(sql, values)
        out = dict(data)
        if res.get("last_id"):
            out["id"] = res["last_id"]
        return out

    def find(
        self,
        table: str,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM {table}"
        params: List[Any] = []

        if where:
            clauses = []
            for k, v in where.items():
                clauses.append(f"{k} = ?")
                params.append(v)
            sql += f" WHERE {' AND '.join(clauses)}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        if limit is not None:
            sql += f" LIMIT {int(limit)}"

        return self.query(sql, params)

    def find_one(self, table: str, where: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        results = self.find(table, where=where, limit=1)
        if results:
            return results[0]
        return None

    def update(self, table: str, where: Dict[str, Any], updates: Dict[str, Any]) -> int:
        if not updates:
            return 0
        set_clauses = []
        params = []
        for k, v in updates.items():
            set_clauses.append(f"{k} = ?")
            params.append(v)

        where_clauses = []
        for k, v in where.items():
            where_clauses.append(f"{k} = ?")
            params.append(v)

        sql = f"UPDATE {table} SET {', '.join(set_clauses)}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"

        res = self.execute(sql, params)
        return res["rows_affected"]

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        where_clauses = []
        params = []
        for k, v in where.items():
            where_clauses.append(f"{k} = ?")
            params.append(v)

        sql = f"DELETE FROM {table}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"
        else:
            raise ValueError("Delete without WHERE condition is not allowed for safety")

        res = self.execute(sql, params)
        return res["rows_affected"]

    def count(self, table: str, where: Optional[Dict[str, Any]] = None) -> int:
        sql = f"SELECT COUNT(*) as cnt FROM {table}"
        params = []
        if where:
            clauses = []
            for k, v in where.items():
                clauses.append(f"{k} = ?")
                params.append(v)
            sql += f" WHERE {' AND '.join(clauses)}"
        rows = self.query(sql, params)
        return int(rows[0]["cnt"]) if rows else 0

    def close(self) -> None:
        if hasattr(self._local, "connections"):
            for conn in self._local.connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            self._local.connections.clear()

    def _normalize_params(self, params: Any) -> Union[Tuple, List]:
        if params is None:
            return []
        if isinstance(params, (list, tuple)):
            return params
        return [params]


# Global singleton instance
_db_manager = DatabaseManager()


def export_module() -> Dict[str, Any]:
    return {
        "connect": LyslynBuiltin("connect", lambda path="app.db": _db_manager.connect(path)),
        "query": LyslynBuiltin("query", lambda sql, params=None: _db_manager.query(sql, params)),
        "execute": LyslynBuiltin("execute", lambda sql, params=None: _db_manager.execute(sql, params)),
        "create_table": LyslynBuiltin("create_table", lambda table, schema: _db_manager.create_table(table, schema)),
        "table_exists": LyslynBuiltin("table_exists", lambda table: _db_manager.table_exists(table)),
        "insert": LyslynBuiltin("insert", lambda table, data: _db_manager.insert(table, data)),
        "find": LyslynBuiltin("find", lambda table, where=None, order_by=None, limit=None: _db_manager.find(table, where, order_by, limit)),
        "find_one": LyslynBuiltin("find_one", lambda table, where: _db_manager.find_one(table, where)),
        "update": LyslynBuiltin("update", lambda table, where, updates: _db_manager.update(table, where, updates)),
        "delete": LyslynBuiltin("delete", lambda table, where: _db_manager.delete(table, where)),
        "count": LyslynBuiltin("count", lambda table, where=None: _db_manager.count(table, where)),
        "close": LyslynBuiltin("close", lambda: _db_manager.close()),
    }
