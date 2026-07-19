"""
Shared utilities for turning the per-user daily feature table into
sliding-window sequences for the LSTM, with strict chronological
(non-shuffled) train/validation/test splitting.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

LOOKBACK = 30      # days of history fed into the model
HORIZON_7D = 7      # predict next 7 days total expense
TARGET_COL = "daily_expense"

FEATURE_COLUMNS = [
    "daily_expense", "daily_income", "daily_savings", "daily_investment",
    "recurring_amount", "day_of_week", "day_of_month", "month", "is_weekend",
    "days_remaining_in_month", "rolling_7d_expense_avg", "rolling_30d_expense_avg",
    "rolling_7d_income_avg", "budget_usage_ratio",
]


def load_daily_features(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values(["user_id", "date"]).reset_index(drop=True)


def make_sequences(df: pd.DataFrame, lookback: int = LOOKBACK, horizon: int = HORIZON_7D):
    """Builds (X, y) sequences per user: X = lookback days of features,
    y = sum of daily_expense over the following `horizon` days."""
    feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    X_list, y_list, meta = [], [], []

    for user_id, g in df.groupby("user_id"):
        g = g.sort_values("date").reset_index(drop=True)
        values = g[feature_cols].values.astype(np.float32)
        target = g[TARGET_COL].values.astype(np.float32)
        dates = g["date"].values

        n = len(g)
        for i in range(lookback, n - horizon + 1):
            X_list.append(values[i - lookback:i])
            y_list.append(target[i:i + horizon].sum())
            meta.append((user_id, dates[i]))

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    return X, y, meta, feature_cols


def chronological_split(X, y, meta, train_frac=0.7, val_frac=0.15):
    """Splits by the chronological order of the *global* sequence index
    (meta already accumulated in per-user date order via groupby loop above,
    so we sort explicitly by date to guarantee no leakage across the split)."""
    order = np.argsort([m[1] for m in meta])
    X, y = X[order], y[order]
    meta = [meta[i] for i in order]

    n = len(X)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))

    return (
        (X[:train_end], y[:train_end], meta[:train_end]),
        (X[train_end:val_end], y[train_end:val_end], meta[train_end:val_end]),
        (X[val_end:], y[val_end:], meta[val_end:]),
    )
