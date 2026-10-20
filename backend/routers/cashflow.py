from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg2.extras import RealDictCursor

from backend.config import settings
from backend.dependencies import advisory_connection
from backend.schemas import CashflowEvaluate, ExpenseInput, IncomeInput

router = APIRouter(prefix="/cashflow", tags=["Cashflow"])


@router.get("/{user_id}/income")
def list_income(user_id: UUID, conn=Depends(advisory_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT income_id::text,user_id::text,source_category,gross_amount,frequency::text,last_updated FROM income_stream WHERE user_id=%s ORDER BY last_updated DESC,income_id", (str(user_id),))
        return [dict(row) for row in cur.fetchall()]


@router.post("/{user_id}/income", status_code=status.HTTP_201_CREATED)
def add_income(user_id: UUID, body: IncomeInput, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM user_profile WHERE user_id=%s", (str(user_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
            cur.execute("""INSERT INTO income_stream(user_id,source_category,gross_amount,frequency)
                           VALUES (%s,%s,%s,%s) RETURNING income_id,user_id,source_category,gross_amount,frequency,last_updated""",
                        (str(user_id), body.source_category.strip(), body.gross_amount, body.frequency))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            return dict(row)


@router.put("/income/{income_id}")
def update_income(income_id: UUID, body: IncomeInput, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""UPDATE income_stream SET source_category=%s,gross_amount=%s,frequency=%s,last_updated=now()
                           WHERE income_id=%s RETURNING income_id,user_id,source_category,gross_amount,frequency,last_updated""",
                        (body.source_category.strip(), body.gross_amount, body.frequency, str(income_id)))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Income stream not found")
            return dict(row)


@router.delete("/income/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(income_id: UUID, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM income_stream WHERE income_id=%s", (str(income_id),))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Income stream not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/expenses")
def list_expenses(user_id: UUID, conn=Depends(advisory_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT expense_id::text,user_id::text,category,amount,is_mandatory,recurrence_interval FROM expense_item WHERE user_id=%s ORDER BY category,expense_id", (str(user_id),))
        return [dict(row) for row in cur.fetchall()]


@router.post("/{user_id}/expenses", status_code=status.HTTP_201_CREATED)
def add_expense(user_id: UUID, body: ExpenseInput, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM user_profile WHERE user_id=%s", (str(user_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
            cur.execute("""INSERT INTO expense_item(user_id,category,amount,is_mandatory,recurrence_interval)
                           VALUES (%s,%s,%s,%s,%s)
                           RETURNING expense_id,user_id,category,amount,is_mandatory,recurrence_interval""",
                        (str(user_id), body.category.strip(), body.amount, body.is_mandatory, body.recurrence_interval))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            return dict(row)


@router.put("/expenses/{expense_id}")
def update_expense(expense_id: UUID, body: ExpenseInput, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""UPDATE expense_item SET category=%s,amount=%s,is_mandatory=%s,recurrence_interval=%s
                           WHERE expense_id=%s
                           RETURNING expense_id,user_id,category,amount,is_mandatory,recurrence_interval""",
                        (body.category.strip(), body.amount, body.is_mandatory, body.recurrence_interval, str(expense_id)))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Expense item not found")
            return dict(row)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: UUID, conn=Depends(advisory_connection)):
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expense_item WHERE expense_id=%s", (str(expense_id),))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Expense item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _summary(conn, user_id: str, reserve: Decimal):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT gross_amount,frequency::text AS frequency FROM income_stream WHERE user_id=%s", (user_id,))
        incomes = cur.fetchall()
        cur.execute("SELECT amount,is_mandatory,recurrence_interval FROM expense_item WHERE user_id=%s", (user_id,))
        expenses = cur.fetchall()
        cur.execute("SELECT 1 FROM user_profile WHERE user_id=%s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
    monthly_income = sum((row["gross_amount"] if row["frequency"] == "MONTHLY" else row["gross_amount"] / 12 for row in incomes), Decimal("0"))
    mandatory = Decimal("0")
    discretionary = Decimal("0")
    for row in expenses:
        interval = row["recurrence_interval"].upper()
        if interval not in {"MONTHLY", "YEARLY"}:
            raise HTTPException(status_code=422, detail=f"Unsupported expense recurrence: {interval}")
        monthly_amount = row["amount"] if interval == "MONTHLY" else row["amount"] / 12
        if row["is_mandatory"]:
            mandatory += monthly_amount
        else:
            discretionary += monthly_amount
    surplus = monthly_income - mandatory
    return {
        "monthly_income": monthly_income,
        "monthly_mandatory_expenses": mandatory,
        "monthly_discretionary_expenses": discretionary,
        "computed_surplus": surplus,
        "liquid_safety_reserve": reserve,
        "investable_buffer": max(Decimal("0"), surplus - reserve),
    }


@router.get("/{user_id}/summary")
def get_summary(user_id: UUID, conn=Depends(advisory_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT liquid_safety_reserve FROM surplus_snapshot WHERE user_id=%s ORDER BY evaluated_at DESC,snapshot_id DESC LIMIT 1", (str(user_id),))
        row = cur.fetchone()
    reserve = row[0] if row and row[0] is not None else Decimal(str(settings.DEFAULT_LIQUID_SAFETY_RESERVE))
    return {"user_id": str(user_id), **_summary(conn, str(user_id), reserve)}


@router.post("/{user_id}/evaluate")
def evaluate_cashflow(user_id: UUID, body: CashflowEvaluate | None = None, conn=Depends(advisory_connection)):
    reserve = body.liquid_safety_reserve if body and body.liquid_safety_reserve is not None else Decimal(str(settings.DEFAULT_LIQUID_SAFETY_RESERVE))
    snapshot = _summary(conn, str(user_id), reserve)
    total_expense = snapshot["monthly_mandatory_expenses"] + snapshot["monthly_discretionary_expenses"]
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""INSERT INTO surplus_snapshot(user_id,total_income,total_expense,computed_surplus,investable_buffer,liquid_safety_reserve)
                           VALUES (%s,%s,%s,%s,%s,%s) RETURNING snapshot_id,evaluated_date,liquid_safety_reserve""",
                        (str(user_id), snapshot["monthly_income"], total_expense, snapshot["computed_surplus"], snapshot["investable_buffer"], reserve))
            persisted = dict(cur.fetchone())
    return {"user_id": str(user_id), **snapshot, **persisted}
