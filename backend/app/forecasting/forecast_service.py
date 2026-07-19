"""
Bridges the FastAPI backend to the trained LSTM model in
machine-learning/scripts/predict.py. Builds a live 30-day feature window
from a user's actual transaction history (same feature engineering as
machine-learning/scripts/preprocess.py) and calls the saved model.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.finance_models import Budget, Transaction

# Make the ML pipeline's prediction module importable.
ML_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "machine-learning" / "scripts"
if str(ML_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(ML_SCRIPTS_DIR))

MIN_DAYS_FOR_LOW_CONFIDENCE = 30
MIN_DAYS_FOR_PERSONALIZED = 60
LOOKBACK = 30


def _build_daily_window(db: Session, user_id: str, as_of: date, lookback_days: int) -> pd.DataFrame:
    """Reconstructs the same engineered daily features used at training
    time, but from this user's live transactions in the relational
    database rather than the offline CSV."""
    start = as_of - timedelta(days=lookback_days - 1)
    txns = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.is_deleted.is_(False),
        Transaction.date >= start - timedelta(days=30),  # extra history for rolling averages
        Transaction.date <= as_of,
    ).all()

    if not txns:
        return pd.DataFrame()

    rows = [{
        "date": t.date, "amount": float(t.amount), "transaction_type": t.transaction_type,
        "is_recurring": t.is_recurring,
    } for t in txns]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])

    full_range = pd.date_range(start - timedelta(days=30), as_of, freq="D")
    daily_expense = df[df["transaction_type"] == "expense"].groupby("date")["amount"].sum()
    daily_income = df[df["transaction_type"] == "income"].groupby("date")["amount"].sum()
    daily_savings = df[df["transaction_type"] == "savings"].groupby("date")["amount"].sum()
    daily_investment = df[df["transaction_type"] == "investment"].groupby("date")["amount"].sum()
    daily_recurring = df[df["is_recurring"] == True].groupby("date")["amount"].sum()  # noqa: E712

    daily = pd.DataFrame(index=full_range)
    daily["daily_expense"] = daily_expense.reindex(full_range, fill_value=0.0)
    daily["daily_income"] = daily_income.reindex(full_range, fill_value=0.0)
    daily["daily_savings"] = daily_savings.reindex(full_range, fill_value=0.0)
    daily["daily_investment"] = daily_investment.reindex(full_range, fill_value=0.0)
    daily["recurring_amount"] = daily_recurring.reindex(full_range, fill_value=0.0)

    daily["day_of_week"] = daily.index.dayofweek
    daily["day_of_month"] = daily.index.day
    daily["month"] = daily.index.month
    daily["is_weekend"] = (daily["day_of_week"] >= 5).astype(int)
    daily["days_remaining_in_month"] = daily.index.days_in_month - daily["day_of_month"]

    daily["rolling_7d_expense_avg"] = daily["daily_expense"].rolling(7, min_periods=1).mean()
    daily["rolling_30d_expense_avg"] = daily["daily_expense"].rolling(30, min_periods=1).mean()
    daily["rolling_7d_income_avg"] = daily["daily_income"].rolling(7, min_periods=1).mean()

    daily["month_key"] = daily.index.to_period("M")
    daily["cum_month_expense"] = daily.groupby("month_key")["daily_expense"].cumsum()
    daily["cum_month_income"] = daily.groupby("month_key")["daily_income"].cumsum()
    daily["budget_usage_ratio"] = (
        daily["cum_month_expense"] / daily["cum_month_income"].replace(0, pd.NA)
    ).fillna(0.0).clip(0, 5)
    daily = daily.drop(columns=["month_key"]).fillna(0.0)

    # Return exactly the trailing `lookback_days` window the model expects.
    return daily.tail(lookback_days)


def history_days_available(db: Session, user_id: str) -> int:
    first_txn = db.query(Transaction).filter(
        Transaction.user_id == user_id, Transaction.is_deleted.is_(False)
    ).order_by(Transaction.date.asc()).first()
    if not first_txn:
        return 0
    return (date.today() - first_txn.date).days + 1


def generate_forecast(db: Session, user_id: str) -> dict:
    """
    Returns a dict matching schemas_import_forecast.ForecastOut fields.
    Implements the tiered confidence policy from the spec:
      < 30 days history -> no personalized prediction
      30-59 days        -> early prediction, low-confidence label
      >= 60 days        -> personalized forecast
    """
    from predict import is_model_available, predict_multi_horizon  # ML module

    days_available = history_days_available(db, user_id)

    if days_available < MIN_DAYS_FOR_LOW_CONFIDENCE:
        return {
            "confidence_level": "insufficient_data",
            "history_days_available": days_available,
        }

    if not is_model_available():
        return {
            "confidence_level": "insufficient_data",
            "history_days_available": days_available,
        }

    window = _build_daily_window(db, user_id, date.today(), LOOKBACK)
    if len(window) < LOOKBACK:
        return {
            "confidence_level": "insufficient_data",
            "history_days_available": days_available,
        }

    predictions = predict_multi_horizon(window)
    confidence = "personalized" if days_available >= MIN_DAYS_FOR_PERSONALIZED else "low_confidence"

    # Overspending risk: compare predicted 30-day expense against active budgets.
    total_budget = db.query(Budget).filter(
        Budget.user_id == user_id, Budget.is_deleted.is_(False),
        Budget.period_month == date.today().month, Budget.period_year == date.today().year,
    ).all()
    overspending_risk = None
    if total_budget:
        budget_sum = sum(float(b.limit_amount) for b in total_budget)
        ratio = predictions["next_30_days"] / budget_sum if budget_sum > 0 else 0
        overspending_risk = "high" if ratio > 1.0 else ("medium" if ratio > 0.85 else "low")

    return {
        "confidence_level": confidence,
        "history_days_available": days_available,
        "predicted_next_1_day": predictions["next_1_day"],
        "predicted_next_7_days": predictions["next_7_days"],
        "predicted_next_30_days": predictions["next_30_days"],
        "predicted_next_90_days": predictions["next_90_days"],
        "predicted_end_of_month_expense": predictions["next_30_days"],
        "overspending_risk": overspending_risk,
    }
