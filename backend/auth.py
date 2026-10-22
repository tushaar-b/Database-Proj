"""Database-backed opaque cookie sessions with Argon2id password hashes."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException, Request, status
from psycopg2.extras import RealDictCursor

from backend.config import settings
from backend.dependencies import advisory_connection

SESSION_COOKIE = "intellivest_session"
SESSION_TTL_HOURS = 12


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def session_csrf_token(session_token: str) -> str:
    """Stable, domain-separated CSRF proof derived from a high-entropy session.

    The HttpOnly cookie remains secret; exposing this HMAC does not disclose it.
    All tabs and concurrent /auth/me calls receive the same proof for a session.
    """
    return hmac.new(
        session_token.encode("utf-8"), b"intellivest:csrf:v1", hashlib.sha256,
    ).hexdigest()


def issue_tokens() -> tuple[str, str]:
    session_token = secrets.token_urlsafe(32)
    return session_token, session_csrf_token(session_token)


def set_session_cookie(response, request: Request, token: str) -> None:
    secure = request.url.scheme == "https" or settings.APP_ENV.lower() in {"production", "prod"}
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=secure, samesite="lax",
        max_age=SESSION_TTL_HOURS * 3600, path="/",
    )


def clear_session_cookie(response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax")


def current_session(request: Request, conn=Depends(advisory_connection)):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT s.user_id::text,s.csrf_token_hash,p.full_name,p.email,p.risk_tolerance_tier::text
               FROM auth_session s JOIN user_profile p USING(user_id)
               WHERE s.token_hash=%s AND s.expires_at>now()""",
            (digest(token),),
        )
        session = cur.fetchone()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
    request.state.user_id = session["user_id"]
    request.state.csrf_token_hash = session["csrf_token_hash"]
    request.state.public_user = dict(session)
    return session


def require_authenticated(session=Depends(current_session)):
    return session


def require_csrf(request: Request, session=Depends(current_session)):
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origins = {item.strip() for item in settings.ALLOWED_ORIGINS.split(",") if item.strip()}
    origin = request.headers.get("origin")
    if origin and origin not in origins:
        raise HTTPException(status_code=403, detail="Request origin is not allowed")
    supplied = request.headers.get("x-csrf-token", "")
    if not supplied or not hmac.compare_digest(digest(supplied), session["csrf_token_hash"]):
        raise HTTPException(status_code=403, detail="CSRF token is missing or invalid")


def ensure_user(request: Request, user_id) -> str:
    principal = getattr(request.state, "user_id", None)
    if not principal or str(user_id) != str(principal):
        # Same response for missing and foreign objects avoids confirming IDs.
        raise HTTPException(status_code=404, detail="Record not found")
    return str(principal)


def rate_limit_key(value: str) -> str:
    # Keys are hashes; raw email/IP are never stored in the attempts table.
    return digest(value.strip().lower())
