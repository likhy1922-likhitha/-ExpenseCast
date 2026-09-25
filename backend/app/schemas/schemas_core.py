from __future__ import annotations

from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth / Profile ---

class ProfileCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    user_type: Literal["student", "teenager", "salaried", "freelancer", "other"]
    preferred_currency: str = Field(default="INR", max_length=10)
    approx_monthly_income: Optional[float] = Field(default=None, ge=0)
    budget_start_day: int = Field(default=1, ge=1, le=28)
    savings_target: Optional[float] = Field(default=None, ge=0)
    preferred_categories: Optional[list[str]] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    user_type: Optional[Literal["student", "teenager", "salaried", "freelancer", "other"]] = None
    preferred_currency: Optional[str] = None
    approx_monthly_income: Optional[float] = Field(default=None, ge=0)
    budget_start_day: Optional[int] = Field(default=None, ge=1, le=28)
    savings_target: Optional[float] = Field(default=None, ge=0)
    preferred_categories: Optional[list[str]] = None
    theme: Optional[Literal["light", "dark"]] = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    user_type: str
    preferred_currency: str
    approx_monthly_income: Optional[float]
    budget_start_day: int
    savings_target: Optional[float]
    preferred_categories: Optional[str]
    onboarding_completed: bool
    theme: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    full_name: str
    is_demo_user: bool
    created_at: datetime


# --- Transactions ---

class TransactionCreate(BaseModel):
    account_id: Optional[str] = None
    date: date
    time: Optional[str] = None
    transaction_type: Literal["income", "expense", "savings", "investment"]
    amount: float = Field(gt=0)
    currency: str = Field(default="INR", max_length=10)
    category_id: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=2000)
    merchant: Optional[str] = Field(default=None, max_length=255)
    payment_method: Optional[str] = None
    tags: Optional[list[str]] = None
    is_recurring: bool = False
    receipt_reference: Optional[str] = None


class TransactionUpdate(BaseModel):
    account_id: Optional[str] = None
    date: Optional[date] = None
    time: Optional[str] = None
    transaction_type: Optional[Literal["income", "expense", "savings", "investment"]] = None
    amount: Optional[float] = Field(default=None, gt=0)
    category_id: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    tags: Optional[list[str]] = None
    is_recurring: Optional[bool] = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transaction_id: str
    user_id: str
    account_id: Optional[str]
    date: date
    time: Optional[str]
    transaction_type: str
    amount: float
    currency: str
    category_id: Optional[str]
    description: Optional[str]
    merchant: Optional[str]
    payment_method: Optional[str]
    tags: Optional[str]
    is_recurring: bool
    source: str
    created_at: datetime
    updated_at: datetime


class PaginatedTransactions(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int
    total_pages: int
