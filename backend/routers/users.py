from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg2 import errors
from psycopg2.extras import RealDictCursor

from backend.dependencies import advisory_connection
from backend.schemas import OnboardingProgress, RiskToleranceUpdate, UserUpdate
from backend.auth import require_authenticated, require_csrf
from backend.ownership import enforce_ownership

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_authenticated), Depends(require_csrf), Depends(enforce_ownership)])
PUBLIC_COLUMNS = "user_id,full_name,email,risk_tolerance_tier,created_at"


@router.get("/{user_id}/onboarding")
def get_onboarding_progress(user_id: UUID, conn=Depends(advisory_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT onboarding_step FROM user_profile WHERE user_id=%s", (str(user_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"step": row[0]}


@router.put("/{user_id}/onboarding")
def update_onboarding_progress(user_id: UUID, body: OnboardingProgress, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE user_profile SET onboarding_step=%s WHERE user_id=%s RETURNING onboarding_step", (body.step, str(user_id)))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"step": row[0]}


@router.get("/{user_id}")
def get_user(user_id: UUID, conn=Depends(advisory_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"SELECT {PUBLIC_COLUMNS} FROM user_profile WHERE user_id=%s", (str(user_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


@router.patch("/{user_id}")
def update_user(user_id: UUID, body: UserUpdate, conn=Depends(advisory_connection)):
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(status_code=422, detail="At least one profile field is required")
    if "email" in changes and changes["email"] is not None:
        email = changes["email"].strip().lower()
        import re
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise HTTPException(status_code=422, detail="A valid email address is required")
        changes["email"] = email
    assignments = ",".join(f"{column}=%s" for column in changes)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"UPDATE user_profile SET {assignments} WHERE user_id=%s RETURNING {PUBLIC_COLUMNS}", (*changes.values(), str(user_id)))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="User not found")
                return dict(row)
    except errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email is already registered")


@router.put("/{user_id}/risk-tolerance")
def update_risk_tolerance(user_id: UUID, body: RiskToleranceUpdate, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"UPDATE user_profile SET risk_tolerance_tier=%s WHERE user_id=%s RETURNING {PUBLIC_COLUMNS}",
                (body.risk_tolerance_tier.value, str(user_id)),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            return dict(row)
