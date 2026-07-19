"""
Turns raw ExpenseCast transaction rows into a per-user, per-day feature
table suitable for LSTM sequence generation.

Usage:
    python preprocess.py                # processes the synthetic dataset
    python preprocess.py --realdata     # processes the real Kaggle validation set

Output:
    machine-learning/data/processed/daily_features.csv
    machine-learning/data/processed/daily_features_realdata.csv (with --realdata)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
GENERATED = BASE_DIR / "data" / "generated" / "expensecast_transactions.csv"
REALDATA = BASE_DIR / "data" / "realdata" / "realdata_normalized.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def build_daily_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    frames = []
    for user_id, g in df.groupby("user_id"):
        g = g.sort_values("date")
        full_range = pd.date_range(g["date"].min(), g["date"].max(), freq="D")

        daily_expense = g[g["transaction_type"] == "expense"].groupby("date")["amount"].sum()
        daily_income = g[g["transaction_type"] == "income"].groupby("date")["amount"].sum()
        daily_savings = g[g["transaction_type"] == "savings"].groupby("date")["amount"].sum()
        daily_investment = g[g["transaction_type"] == "investment"].groupby("date")["amount"].sum()
        daily_recurring = g[g["is_recurring"] == True].groupby("date")["amount"].sum()  # noqa: E712

        daily = pd.DataFrame(index=full_range)
        daily.index.name = "date"
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

        # Category totals (top-level, kept generic to avoid per-user category explosion)
        cat_pivot = (
            g[g["transaction_type"] == "expense"]
            .groupby(["date", "category"])["amount"].sum()
            .unstack(fill_value=0.0)
            .reindex(full_range, fill_value=0.0)
        )
        cat_pivot.columns = [f"cat_{c.lower().replace(' ', '_')}" for c in cat_pivot.columns]
        daily = daily.join(cat_pivot)

        # Running budget-usage proxy: cumulative expense within the current month / income so far
        daily["month_key"] = daily.index.to_period("M")
        daily["cum_month_expense"] = daily.groupby("month_key")["daily_expense"].cumsum()
        daily["cum_month_income"] = daily.groupby("month_key")["daily_income"].cumsum()
        daily["budget_usage_ratio"] = np.where(
            daily["cum_month_income"] > 0,
            daily["cum_month_expense"] / daily["cum_month_income"].replace(0, np.nan),
            0.0,
        )
        daily["budget_usage_ratio"] = daily["budget_usage_ratio"].fillna(0.0).clip(0, 5)
        daily = daily.drop(columns=["month_key"])

        daily["user_id"] = user_id
        daily = daily.reset_index().rename(columns={"index": "date"})
        frames.append(daily)

    result = pd.concat(frames, ignore_index=True)
    result = result.fillna(0.0)
    cols = ["user_id", "date"] + [c for c in result.columns if c not in ("user_id", "date")]
    return result[cols]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--realdata", action="store_true")
    args = parser.parse_args()

    src = REALDATA if args.realdata else GENERATED
    out_name = "daily_features_realdata.csv" if args.realdata else "daily_features.csv"

    df = pd.read_csv(src)
    daily = build_daily_features(df)
    out_path = PROCESSED_DIR / out_name
    daily.to_csv(out_path, index=False)
    print(f"Built daily feature table: {daily.shape[0]:,} rows x {daily.shape[1]} cols -> {out_path}")
    print(f"Users: {daily['user_id'].nunique()}, date range: {daily['date'].min()} to {daily['date'].max()}")


if __name__ == "__main__":
    main()
