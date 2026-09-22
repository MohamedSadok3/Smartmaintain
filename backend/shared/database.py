import threading

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from .config import get_env

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                postgres_url = get_env("POSTGRES_URL", required=True)
                min_conn = int(get_env("DB_POOL_MIN", "1"))
                max_conn = int(get_env("DB_POOL_MAX", "10"))
                _pool = pool.ThreadedConnectionPool(
                    min_conn,
                    max_conn,
                    postgres_url,
                    cursor_factory=RealDictCursor,
                )
    return _pool


class _PooledConnection:
    def __enter__(self):
        self._conn = _get_pool().getconn()
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is not None:
            # Always reset transaction state before returning a connection to
            # the pool. This also protects early-return code paths that did not
            # explicitly commit.
            self._conn.rollback()
            _get_pool().putconn(self._conn)
        return False


def get_db_connection():
    return _PooledConnection()
