import sqlite3
import threading
from contextlib import contextmanager

_lock = threading.Lock()
_local = threading.local()

class ConnectionManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(_local, "connection") or _local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            _local.connection = conn
        return _local.connection

    @contextmanager
    def transaction(self):
        with _lock:
            conn = self.get_connection()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @contextmanager
    def cursor(self):
        with _lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def close(self) -> None:
        if hasattr(_local, "connection") and _local.connection is not None:
            _local.connection.close()
            _local.connection = None
