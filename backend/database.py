"""Small thread-safe PostgreSQL connection pools for the two service databases."""
from contextlib import contextmanager
from threading import Lock
from typing import Iterator

from psycopg2.pool import ThreadedConnectionPool

from backend.config import settings

_pools: dict[str, ThreadedConnectionPool] = {}
_pool_lock = Lock()


def _pool(name: str) -> ThreadedConnectionPool:
    if name not in {"advisory", "risk"}:
        raise ValueError(f"Unknown database pool: {name}")
    with _pool_lock:
        if name not in _pools:
            dsn = settings.ADVISORY_DB_URL if name == "advisory" else settings.RISK_DB_URL
            _pools[name] = ThreadedConnectionPool(1, 12, dsn=dsn, connect_timeout=3)
        return _pools[name]


@contextmanager
def connection(name: str) -> Iterator:
    pool = _pool(name)
    conn = pool.getconn()
    discard = False
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        if not conn.closed:
            if not conn.get_transaction_status() == 0:
                conn.rollback()
        else:
            discard = True
        pool.putconn(conn, close=discard)


def close_pools() -> None:
    with _pool_lock:
        for pool in _pools.values():
            pool.closeall()
        _pools.clear()
