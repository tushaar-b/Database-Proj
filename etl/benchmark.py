"""Temporal Query Performance Benchmark for DAILY_MARKET_QUOTE.

Validates that query latency for retrieving the last 30 daily quotes for any security
is strictly under 10ms (NFR requirement) utilizing the idx_quote_temporal index.
"""
import time
import uuid
import logging
from typing import Dict, Any, Optional

from etl.db import get_db_connection, get_cursor

logger = logging.getLogger("etl.benchmark")


def benchmark_temporal_query(
    conn,
    security_id: str,
    iterations: int = 100,
    limit: int = 30
) -> Dict[str, Any]:
    """Measures execution latency of 30-day temporal quote lookups."""
    query = """
        SELECT quote_id, trade_date, close_price, adjusted_close, volume
        FROM DAILY_MARKET_QUOTE
        WHERE security_id = %s
        ORDER BY trade_date DESC
        LIMIT %s;
    """

    # Check if sqlite
    is_sqlite = type(conn).__module__.startswith("sqlite3")
    if is_sqlite:
        query = query.replace("%s", "?")

    latencies_ms = []

    with get_cursor(conn) as cur:
        # Warmup query
        cur.execute(query, (str(security_id), limit))
        cur.fetchall()

        for _ in range(iterations):
            t0 = time.perf_counter()
            cur.execute(query, (str(security_id), limit))
            rows = cur.fetchall()
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)

    avg_ms = sum(latencies_ms) / len(latencies_ms)
    p95_ms = sorted(latencies_ms)[int(0.95 * len(latencies_ms))]
    p99_ms = sorted(latencies_ms)[int(0.99 * len(latencies_ms))]
    min_ms = min(latencies_ms)
    max_ms = max(latencies_ms)

    return {
        "iterations": iterations,
        "rows_returned": len(rows),
        "avg_latency_ms": round(avg_ms, 4),
        "p95_latency_ms": round(p95_ms, 4),
        "p99_latency_ms": round(p99_ms, 4),
        "min_latency_ms": round(min_ms, 4),
        "max_latency_ms": round(max_ms, 4),
        "target_met_sub_10ms": p95_ms < 10.0
    }
