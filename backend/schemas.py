"""Validated API request models for the Phase 4 gateway."""
import re
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RiskTolerance(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    pan_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    risk_tolerance_tier: RiskTolerance

    @field_validator("email")
    @classmethod
    def valid_email_shape(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("A valid email address is required")
        return value


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)


class RiskToleranceUpdate(BaseModel):
    risk_tolerance_tier: RiskTolerance


class IncomeInput(BaseModel):
    source_category: str = Field(min_length=1, max_length=100)
    gross_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    frequency: Literal["MONTHLY", "YEARLY"]


class ExpenseInput(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    is_mandatory: bool = True
    recurrence_interval: Literal["MONTHLY", "YEARLY"] = "MONTHLY"


class CashflowEvaluate(BaseModel):
    liquid_safety_reserve: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class PortfolioCreate(BaseModel):
    user_id: UUID
    portfolio_name: str = Field(min_length=1, max_length=255)
    cash_balance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    target_hhi_limit: Decimal = Field(default=Decimal("0.250"), gt=0, le=1, max_digits=4, decimal_places=3)


class PortfolioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    portfolio_name: str | None = Field(default=None, min_length=1, max_length=255)
    target_hhi_limit: Decimal | None = Field(default=None, gt=0, le=1, max_digits=4, decimal_places=3)


class HoldingInput(BaseModel):
    security_id: UUID
    quantity: int = Field(gt=0)
    average_buy_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class RebalanceOperation(BaseModel):
    security_id: UUID
    side: Literal["BUY", "SELL"]
    units: int = Field(gt=0)


class RebalanceExecute(BaseModel):
    idempotency_key: UUID
    approved: bool
    operations: list[RebalanceOperation] = Field(min_length=1, max_length=20)


class RecommendationDecision(BaseModel):
    decision: Literal["ACCEPTED", "REJECTED"]
