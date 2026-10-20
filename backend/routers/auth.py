import re
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from psycopg2 import errors
from psycopg2.extras import RealDictCursor

from backend.auth import (
    SESSION_COOKIE, SESSION_TTL_HOURS, clear_session_cookie, current_session,
    digest, issue_tokens, rate_limit_key, require_csrf, set_session_cookie,
)
from backend.dependencies import advisory_connection
from backend.config import settings
from backend.schemas import RiskTolerance

router = APIRouter(prefix="/auth", tags=["Authentication"])
password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
# Verify an unrecognized or legacy account against a real Argon2id hash too,
# so an empty result does not skip the expensive password check.
DUMMY_PASSWORD_HASH = password_hasher.hash(secrets.token_urlsafe(32))


class Registration(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    pan_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    risk_tolerance_tier: RiskTolerance = RiskTolerance.MODERATE
    password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("A valid email address is required")
        return normalized


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("A valid email address is required")
        return normalized


def _public(user):
    return {"user_id": str(user["user_id"]), "full_name": user["full_name"],
            "email": user["email"], "risk_tolerance_tier": user["risk_tolerance_tier"]}


def _validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    allowed = {item.strip() for item in settings.ALLOWED_ORIGINS.split(",") if item.strip()}
    if origin and origin not in allowed:
        raise HTTPException(status_code=403, detail="Request origin is not allowed")


def _create_session(conn, user_id, request, response):
    raw_token, csrf_token = issue_tokens()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO auth_session(user_id,token_hash,csrf_token_hash,expires_at)
                   VALUES (%s,%s,%s,now()+(%s * interval '1 hour'))""",
                (str(user_id), digest(raw_token), digest(csrf_token), SESSION_TTL_HOURS),
            )
    set_session_cookie(response, request, raw_token)
    return csrf_token


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: Registration, request: Request, response: Response, conn=Depends(advisory_connection)):
    _validate_origin(request)
    password_hash = password_hasher.hash(body.password)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """INSERT INTO user_profile(full_name,email,pan_hash,risk_tolerance_tier,password_hash)
                       VALUES (%s,%s,%s,%s,%s)
                       RETURNING user_id::text,full_name,email,risk_tolerance_tier::text""",
                    (body.full_name, str(body.email).lower(), body.pan_hash.lower(), body.risk_tolerance_tier.value, password_hash),
                )
                user = dict(cur.fetchone())
    except errors.UniqueViolation:
        # Avoid identifying which unique field collided.
        raise HTTPException(status_code=409, detail="Registration could not be completed")
    csrf = _create_session(conn, user["user_id"], request, response)
    return {"user": _public(user), "csrf_token": csrf}


@router.post("/login")
def login(body: Login, request: Request, response: Response, conn=Depends(advisory_connection)):
    _validate_origin(request)
    normalized = str(body.email).lower()
    identifier_hash = rate_limit_key(normalized)
    client_hash = rate_limit_key(request.client.host if request.client else "unknown")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT COUNT(*) AS failed_count FROM auth_login_attempt
               WHERE attempted_at>now()-interval '15 minutes' AND succeeded=FALSE
                 AND (identifier_hash=%s OR client_hash=%s)""",
            (identifier_hash, client_hash),
        )
        if cur.fetchone()["failed_count"] >= 5:
            raise HTTPException(status_code=429, detail="Too many login attempts; try again later")
        cur.execute(
            """SELECT user_id::text,full_name,email,risk_tolerance_tier::text,password_hash
               FROM user_profile WHERE lower(email)=%s""", (normalized,),
        )
        user = cur.fetchone()
    stored_hash = user["password_hash"] if user and user["password_hash"] else DUMMY_PASSWORD_HASH
    try:
        valid = password_hasher.verify(stored_hash, body.password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        valid = False
    valid = valid and bool(user and user["password_hash"])
    if not valid:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO auth_login_attempt(identifier_hash,client_hash,succeeded) VALUES (%s,%s,FALSE)",
                    (identifier_hash, client_hash),
                )
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO auth_login_attempt(identifier_hash,client_hash,succeeded) VALUES (%s,%s,TRUE)",
                (identifier_hash, client_hash),
            )
    csrf = _create_session(conn, user["user_id"], request, response)
    return {"user": _public(user), "csrf_token": csrf}


@router.get("/me")
def me(request: Request, session=Depends(current_session), conn=Depends(advisory_connection)):
    csrf = secrets.token_urlsafe(32)
    with conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE auth_session SET csrf_token_hash=%s WHERE token_hash=%s",
                        (digest(csrf), digest(request.cookies.get(SESSION_COOKIE, ""))))
    return {"user": _public(session), "csrf_token": csrf}


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(request: Request, response: Response, session=Depends(current_session), conn=Depends(advisory_connection)):
    supplied = request.headers.get("x-csrf-token", "")
    import hmac
    if not supplied or not hmac.compare_digest(digest(supplied), session["csrf_token_hash"]):
        raise HTTPException(status_code=403, detail="CSRF token is missing or invalid")
    token = request.cookies.get(SESSION_COOKIE, "")
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM auth_session WHERE token_hash=%s", (digest(token),))
    clear_session_cookie(response)
    return {"logged_out": True}
