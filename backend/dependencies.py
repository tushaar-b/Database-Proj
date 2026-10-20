"""FastAPI dependencies for pooled advisory and risk database connections."""
from collections.abc import Iterator

from backend.database import connection


def advisory_connection() -> Iterator:
    with connection("advisory") as conn:
        yield conn


def risk_connection() -> Iterator:
    with connection("risk") as conn:
        yield conn
