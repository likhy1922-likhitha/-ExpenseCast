from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.forecasting.forecast_service import generate_forecast
from app.models.finance_models import Budget, SavingsGoal, Transaction
from app.models.investment_models import Investment, RecurringTransaction
from app.models.user_models import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _date_range_for_filter(range_key: str, custom_from: Optional[date], custom_to: Optional[date]) -> tuple[date, date]:
    today = date.today()
    if range_key == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if range_key == "this_month":
        return today.replace(day=1), today
    if range_key == "last_3_months":
        return today - timedelta(days=90), today
    if range_key == "last_6_months":
        return today - timedelta(days=180), today
    if range_key == "this_year":
        return today.replace(month=1, day=1), today
    if range_key == "custom" and custom_from and custom_to:
        return custom_from, custom_to
    return today.replace(day=1), today


@router.get("/summary")
def dashboard_summary(
    date_range: Literal["this_week", "this_month", "last_3_months", "last_6_months", "this_year", "custom"] = "this_month",
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end = _date_range_for_filter(date_range, date_from, date_to)

    txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False),
        Transaction.date >= start, Transaction.date <= end,
    ).all()

    total_income = sum(float(t.amount) for t in txns if t.transaction_type == "income")
    total_expense = sum(float(t.amount) for t in txns if t.transaction_type == "expense")
    total_savings = sum(float(t.amount) for t in txns if t.transaction_type == "savings")
    total_investment = sum(float(t.amount) for t in txns if t.transaction_type == "investment")
    current_balance = total_income - total_expense - total_savings - total_investment
    savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0.0

    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id, Budget.is_deleted.is_(False),
        Budget.period_month == date.today().month, Budget.period_year == date.today().year,
    ).all()
    remaining_budget = sum(float(b.limit_amount) for b in budgets) - total_expense

    forecast = generate_forecast(db, current_user.id)

    return {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "current_balance": round(current_balance, 2),
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expense, 2),
        "total_savings": round(total_savings, 2),
        "total_investments": round(total_investment, 2),
        "remaining_budget": round(remaining_budget, 2),
        "savings_rate": round(savings_rate, 2),
        "predicted_7_day_expense": forecast.get("predicted_next_7_days"),
        "predicted_30_day_expense": forecast.get("predicted_next_30_days"),
        "predicted_end_of_month_balance": (
            round(current_balance - forecast["predicted_next_30_days"], 2)
            if forecast.get("predicted_next_30_days") is not None else None
        ),
        "overspending_risk": forecast.get("overspending_risk"),
        "forecast_confidence": forecast.get("confidence_level"),
    }


@router.get("/charts/income-vs-expense")
def income_vs_expense_trend(
    date_range: Literal["this_week", "this_month", "last_3_months", "last_6_months", "this_year", "custom"] = "last_3_months",
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end = _date_range_for_filter(date_range, date_from, date_to)
    txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False),
        Transaction.date >= start, Transaction.date <= end,
        Transaction.transaction_type.in_(["income", "expense"]),
    ).all()

    by_month: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for t in txns:
        key = t.date.strftime("%Y-%m")
        by_month[key][t.transaction_type] += float(t.amount)

    series = [{"month": k, **v} for k, v in sorted(by_month.items())]
    return {"series": series}


@router.get("/charts/category-breakdown")
def category_breakdown(
    date_range: Literal["this_week", "this_month", "last_3_months", "last_6_months", "this_year", "custom"] = "this_month",
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end = _date_range_for_filter(date_range, date_from, date_to)
    txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False),
        Transaction.transaction_type == "expense",
        Transaction.date >= start, Transaction.date <= end,
    ).all()

    by_category: dict[str, float] = defaultdict(float)
    for t in txns:
        key = t.category_id or "uncategorized"
        by_category[key] += float(t.amount)

    total = sum(by_category.values()) or 1
    return {
        "categories": [
            {"category_id": k, "amount": round(v, 2), "percent": round(v / total * 100, 2)}
            for k, v in sorted(by_category.items(), key=lambda x: -x[1])
        ]
    }


@router.get("/upcoming-recurring")
def upcoming_recurring(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    upcoming = db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == current_user.id,
        RecurringTransaction.is_active.is_(True),
        RecurringTransaction.next_expected_date >= date.today(),
    ).order_by(RecurringTransaction.next_expected_date.asc()).limit(10).all()

    return [
        {
            "id": r.id, "merchant": r.merchant, "average_amount": float(r.average_amount),
            "frequency": r.frequency, "next_expected_date": r.next_expected_date,
            "confirmed_by_user": r.confirmed_by_user,
        }
        for r in upcoming
    ]


@router.post("/upcoming-recurring/{recurring_id}/confirm")
def confirm_recurring(
    recurring_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == current_user.id
    ).first()
    if r:
        r.confirmed_by_user = True
        db.commit()
    return {"confirmed": bool(r)}


@router.get("/insights")
def financial_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generates factual, non-judgemental insights purely from the user's
    own data -- no hard-coded values."""
    today = date.today()
    this_month_start = today.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    this_month_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False),
        Transaction.transaction_type == "expense", Transaction.date >= this_month_start,
    ).all()
    last_month_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False),
        Transaction.transaction_type == "expense",
        Transaction.date >= last_month_start, Transaction.date <= last_month_end,
    ).all()

    by_cat_this_month: dict[str, float] = defaultdict(float)
    for t in this_month_txns:
        by_cat_this_month[t.category_id or "uncategorized"] += float(t.amount)

    highest_category = max(by_cat_this_month.items(), key=lambda x: x[1]) if by_cat_this_month else None

    this_month_total = sum(by_cat_this_month.values())
    last_month_total = sum(float(t.amount) for t in last_month_txns)
    mom_change_pct = (
        ((this_month_total - last_month_total) / last_month_total * 100) if last_month_total > 0 else None
    )

    weekday_total = sum(float(t.amount) for t in this_month_txns if t.date.weekday() < 5)
    weekend_total = sum(float(t.amount) for t in this_month_txns if t.date.weekday() >= 5)

    days_elapsed = max(1, (today - this_month_start).days + 1)
    avg_daily_expense = this_month_total / days_elapsed

    largest_recent = max(this_month_txns, key=lambda t: float(t.amount)) if this_month_txns else None

    subscription_total = sum(
        float(t.amount) for t in this_month_txns if t.is_recurring
    )

    return {
        "highest_spending_category": highest_category[0] if highest_category else None,
        "highest_spending_category_amount": round(highest_category[1], 2) if highest_category else None,
        "average_daily_expense": round(avg_daily_expense, 2),
        "weekday_spending": round(weekday_total, 2),
        "weekend_spending": round(weekend_total, 2),
        "total_recurring_subscriptions": round(subscription_total, 2),
        "month_over_month_change_percent": round(mom_change_pct, 2) if mom_change_pct is not None else None,
        "largest_recent_transaction_amount": float(largest_recent.amount) if largest_recent else None,
        "largest_recent_transaction_merchant": largest_recent.merchant if largest_recent else None,
    }
