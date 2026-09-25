from __future__ import annotations

from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Categories ---

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category_type: Literal["income", "expense", "transfer"] = "expense"
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: Optional[str]
    name: str
    category_type: str
    icon: Optional[str]
    color: Optional[str]
    is_default: bool


# --- Budgets ---

class BudgetCreate(BaseModel):
    category_id: Optional[str] = None
    name: str = Field(min_length=1, max_length=150)
    period_month: int = Field(ge=1, le=12)
    period_year: int = Field(ge=2000, le=2100)
    limit_amount: float = Field(gt=0)


class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    limit_amount: Optional[float] = Field(default=None, gt=0)


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    category_id: Optional[str]
    name: str
    period_month: int
    period_year: int
    limit_amount: float


class BudgetProgressOut(BaseModel):
    budget: BudgetOut
    spent_amount: float
    remaining_amount: float
    percent_used: float
    warning_level: Optional[Literal["50", "75", "90", "100"]]


# --- Savings goals ---

class GoalCreate(BaseModel):
    goal_name: str = Field(min_length=1, max_length=150)
    target_amount: float = Field(gt=0)
    current_amount: float = Field(default=0, ge=0)
    target_date: Optional[date] = None


class GoalUpdate(BaseModel):
    goal_name: Optional[str] = None
    target_amount: Optional[float] = Field(default=None, gt=0)
    target_date: Optional[date] = None
    status: Optional[Literal["active", "completed", "abandoned"]] = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    goal_id: str
    user_id: str
    goal_name: str
    target_amount: float
    current_amount: float
    target_date: Optional[date]
    monthly_required_amount: Optional[float]
    status: str


class ContributionCreate(BaseModel):
    amount: float = Field(gt=0)
    contribution_date: date
    note: Optional[str] = None


class ContributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    goal_id: str
    amount: float
    contribution_date: date
    note: Optional[str]


# --- Investments ---

class InvestmentCreate(BaseModel):
    investment_name: str = Field(min_length=1, max_length=150)
    investment_type: Literal[
        "fixed_deposit", "recurring_deposit", "mutual_fund", "sip",
        "stocks", "gold", "provident_fund", "other",
    ]
    amount_invested: float = Field(gt=0)
    investment_date: date
    current_value: Optional[float] = Field(default=None, ge=0)
    expected_return_percent: Optional[float] = None
    notes: Optional[str] = None


class InvestmentUpdate(BaseModel):
    current_value: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None


class InvestmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    investment_name: str
    investment_type: str
    amount_invested: float
    investment_date: date
    current_value: Optional[float]
    expected_return_percent: Optional[float]
    notes: Optional[str]
