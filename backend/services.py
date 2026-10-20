"""Shared risk evaluation and durable cross-database feedback delivery."""
import hashlib
import json
import logging
import time
from typing import Any

from fastapi import HTTPException
from psycopg2 import errors
from psycopg2.extras import RealDictCursor

from backend.config import settings

logger = logging.getLogger(__name__)


def risk_summary(conn, portfolio_id: str) -> dict[str, Any]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM portfolio_risk_summary_v2(%s)", (portfolio_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return dict(row)


def _feedback_snapshot(cur, user_id: str, evaluated_portfolio_id: str) -> tuple[dict, str, str | None, str | None]:
    cur.execute(
        """SELECT a.alert_id::text, a.portfolio_id::text, a.breached_metric::text AS metric
           FROM rebalance_alert a JOIN portfolio p USING (portfolio_id)
           WHERE p.user_id=%s AND a.resolved_flag=FALSE
           ORDER BY CASE a.breached_metric::text
                    WHEN 'VAR_95_BREACH' THEN 1 WHEN 'VOLATILITY_SPIKE' THEN 2 ELSE 3 END,
                    a.created_at, a.alert_id""",
        (user_id,),
    )
    alerts = [dict(row) for row in cur.fetchall()]
    metrics = {row["metric"] for row in alerts}
    sector_portfolios = sorted({row["portfolio_id"] for row in alerts if row["metric"] == "SECTOR_HHI_EXCEEDED"})
    blocked_sectors: list[str] = []
    if sector_portfolios:
        cur.execute(
            """SELECT DISTINCT ON (portfolio_id) portfolio_id::text, sector_name
               FROM mv_daily_sector_concentration WHERE portfolio_id=ANY(%s::uuid[])
               ORDER BY portfolio_id, sector_weight DESC, sector_name""",
            (sector_portfolios,),
        )
        blocked_sectors = sorted({row["sector_name"] for row in cur.fetchall()})

    reducing_metrics = sorted(metrics.intersection({"VAR_95_BREACH", "VOLATILITY_SPIKE"}))
    multiplier = 1.0 if not reducing_metrics else (0.25 if len(reducing_metrics) > 1 else 0.5)
    reasons = []
    if "VAR_95_BREACH" in metrics:
        reasons.append("Equity allocation reduced because portfolio VaR exceeds the configured limit.")
    if "VOLATILITY_SPIKE" in metrics:
        reasons.append("Equity allocation reduced because portfolio volatility exceeds the configured limit.")
    if "SECTOR_HHI_EXCEEDED" in metrics:
        reasons.append("New investments in the most concentrated sector are restricted because portfolio HHI exceeds its limit.")
    if not reasons:
        reasons = ["No active risk breach; normal allocation policy applies."]

    trigger = next((metric for metric in ("VAR_95_BREACH", "VOLATILITY_SPIKE", "SECTOR_HHI_EXCEEDED") if metric in metrics), None)
    trigger_portfolio = next((a["portfolio_id"] for a in alerts if a["metric"] == trigger), evaluated_portfolio_id if trigger is None else None)
    payload = {
        "capacity_multiplier": multiplier,
        "blocked_sectors": blocked_sectors,
        "reason": " ".join(reasons),
        "triggering_portfolio_id": trigger_portfolio,
        "triggering_metric": trigger,
    }
    canonical = {"alerts": alerts, **payload}
    signature = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
    return payload, signature, trigger_portfolio, trigger


def _persist_feedback_snapshot(cur, user_id: str, evaluated_portfolio_id: str) -> int | None:
    payload, signature, trigger_portfolio, trigger_metric = _feedback_snapshot(cur, user_id, evaluated_portfolio_id)
    cur.execute(
        "INSERT INTO risk_feedback_state(user_id,policy_signature) VALUES (%s,'') ON CONFLICT(user_id) DO NOTHING",
        (user_id,),
    )
    cur.execute("SELECT policy_signature FROM risk_feedback_state WHERE user_id=%s FOR UPDATE", (user_id,))
    current_signature = cur.fetchone()["policy_signature"]
    if current_signature == signature:
        return None
    cur.execute(
        """INSERT INTO risk_feedback_outbox(user_id,portfolio_id,triggering_metric,policy_signature,payload)
           VALUES (%s,%s,%s,%s,%s::jsonb) RETURNING event_seq""",
        (user_id, trigger_portfolio, trigger_metric, signature, json.dumps(payload)),
    )
    sequence = cur.fetchone()["event_seq"]
    cur.execute(
        "UPDATE risk_feedback_state SET policy_signature=%s,last_event_id=(SELECT event_id FROM risk_feedback_outbox WHERE event_seq=%s),updated_at=now() WHERE user_id=%s",
        (signature, sequence, user_id),
    )
    return sequence


def _evaluate_once(conn, portfolio_id: str) -> dict[str, Any]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT portfolio_id,user_id FROM portfolio WHERE portfolio_id=%s FOR UPDATE", (portfolio_id,))
        portfolio = cur.fetchone()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        cur.execute("REFRESH MATERIALIZED VIEW mv_daily_sector_concentration")
        summary = risk_summary(conn, portfolio_id)
        value = float(summary["portfolio_valuation"] or 0)
        var_value = float(summary["parametric_var_95"]) if summary["parametric_var_95"] is not None else None
        volatility = summary["volatility_30d"]
        hhi = summary["sector_hhi"]
        hhi_limit = summary["target_hhi_limit"]
        breaches: dict[str, tuple[bool, float]] = {
            "VAR_95_BREACH": (
                value > 0 and var_value is not None and var_value / value > settings.RISK_VAR_LIMIT_PERCENT,
                ((var_value / value / settings.RISK_VAR_LIMIT_PERCENT) - 1) * 100 if value > 0 and var_value is not None else 0,
            ),
            "VOLATILITY_SPIKE": (
                volatility is not None and volatility > settings.RISK_DAILY_VOLATILITY_LIMIT,
                ((float(volatility) / settings.RISK_DAILY_VOLATILITY_LIMIT) - 1) * 100 if volatility is not None else 0,
            ),
            "SECTOR_HHI_EXCEEDED": (
                hhi is not None and hhi_limit is not None and hhi > float(hhi_limit),
                ((float(hhi) / float(hhi_limit)) - 1) * 100 if hhi is not None and hhi_limit else 0,
            ),
        }
        new_alerts = []
        for metric, (breached, drift) in breaches.items():
            cur.execute(
                "SELECT alert_id FROM rebalance_alert WHERE portfolio_id=%s AND breached_metric=%s AND resolved_flag=FALSE LIMIT 1",
                (portfolio_id, metric),
            )
            existing = cur.fetchone()
            if breached and not existing:
                cur.execute(
                    """INSERT INTO rebalance_alert(portfolio_id,drift_magnitude_pct,breached_metric)
                       VALUES (%s,%s,%s) RETURNING alert_id::text""",
                    (portfolio_id, min(max(drift, 0), 999.99), metric),
                )
                new_alerts.append({"alert_id": cur.fetchone()["alert_id"], "metric": metric})
            elif not breached and existing:
                cur.execute(
                    "UPDATE rebalance_alert SET resolved_flag=TRUE WHERE portfolio_id=%s AND breached_metric=%s AND resolved_flag=FALSE",
                    (portfolio_id, metric),
                )
        event_seq = _persist_feedback_snapshot(cur, str(portfolio["user_id"]), portfolio_id)
    return {"summary": summary, "new_alerts": new_alerts, "feedback_event_seq": event_seq}


def evaluate_portfolio_risk(conn, portfolio_id: str, retries: int = 3) -> dict[str, Any]:
    """Refresh SQL concentration, evaluate alerts, and transactionally enqueue policy changes."""
    for attempt in range(retries):
        try:
            conn.set_session(isolation_level="SERIALIZABLE")
            with conn:
                result = _evaluate_once(conn, portfolio_id)
            conn.set_session(isolation_level="READ COMMITTED")
            return result
        except (errors.SerializationFailure, errors.DeadlockDetected):
            conn.rollback()
            conn.set_session(isolation_level="READ COMMITTED")
            if attempt + 1 == retries:
                raise HTTPException(status_code=409, detail="Risk evaluation conflicted; retry the request")
            time.sleep(0.02 * (attempt + 1))
        except Exception:
            conn.rollback()
            conn.set_session(isolation_level="READ COMMITTED")
            raise
    raise HTTPException(status_code=409, detail="Risk evaluation could not complete")


def process_feedback_outbox(risk_conn, advisory_conn, limit: int = 100) -> dict[str, Any]:
    """Apply pending risk snapshots once; failed deliveries remain durable for retry."""
    with risk_conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT event_seq,event_id::text,user_id::text,payload FROM risk_feedback_outbox
               WHERE processed_at IS NULL ORDER BY event_seq LIMIT %s""",
            (limit,),
        )
        events = [dict(row) for row in cur.fetchall()]
    applied = 0
    failed = []
    for event in events:
        try:
            payload = event["payload"] if isinstance(event["payload"], dict) else json.loads(event["payload"])
            with advisory_conn:
                with advisory_conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO applied_feedback_events(event_id) VALUES (%s) ON CONFLICT(event_id) DO NOTHING RETURNING event_id",
                        (event["event_id"],),
                    )
                    if cur.fetchone():
                        cur.execute(
                            """INSERT INTO recommendation_policy
                               (user_id,capacity_multiplier,blocked_sectors,reason,triggering_portfolio_id,triggering_metric,source_sequence)
                               VALUES (%s,%s,%s,%s,%s,%s,%s)
                               ON CONFLICT(user_id) DO UPDATE SET
                                 capacity_multiplier=EXCLUDED.capacity_multiplier,
                                 blocked_sectors=EXCLUDED.blocked_sectors,
                                 reason=EXCLUDED.reason,
                                 triggering_portfolio_id=EXCLUDED.triggering_portfolio_id,
                                 triggering_metric=EXCLUDED.triggering_metric,
                                 source_sequence=EXCLUDED.source_sequence,
                                 updated_at=now()
                               WHERE recommendation_policy.source_sequence < EXCLUDED.source_sequence""",
                            (
                                event["user_id"], payload["capacity_multiplier"], payload["blocked_sectors"],
                                payload["reason"], payload["triggering_portfolio_id"], payload["triggering_metric"], event["event_seq"],
                            ),
                        )
            with risk_conn:
                with risk_conn.cursor() as cur:
                    cur.execute(
                        "UPDATE risk_feedback_outbox SET processed_at=now(),attempts=attempts+1,last_error=NULL WHERE event_seq=%s",
                        (event["event_seq"],),
                    )
            applied += 1
        except Exception as exc:
            logger.exception("Feedback outbox event %s failed", event["event_seq"])
            risk_conn.rollback()
            with risk_conn:
                with risk_conn.cursor() as cur:
                    cur.execute(
                        "UPDATE risk_feedback_outbox SET attempts=attempts+1,last_error=%s WHERE event_seq=%s",
                        (str(exc)[:1000], event["event_seq"]),
                    )
            failed.append(event["event_seq"])
    with risk_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM risk_feedback_outbox WHERE processed_at IS NULL")
        pending = cur.fetchone()[0]
    return {"events_seen": len(events), "events_applied": applied, "failed_event_sequences": failed, "pending_events": pending}


def require_feedback_delivery(risk_conn, advisory_conn) -> dict[str, Any]:
    result = process_feedback_outbox(risk_conn, advisory_conn)
    if result["failed_event_sequences"] or result["pending_events"]:
        raise HTTPException(status_code=503, detail={"message": "Risk feedback is queued for retry", **result})
    return result
