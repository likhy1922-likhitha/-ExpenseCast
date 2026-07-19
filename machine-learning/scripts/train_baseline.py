"""
Trains and evaluates the baseline forecasting models that the LSTM must be
compared against:
    1. Moving average (rolling 7-day average * 7)
    2. Previous-period average (previous 7-day sum)
    3. Linear regression on engineered features

Usage:
    python train_baseline.py

Output:
    machine-learning/evaluation/baseline_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

from sequence_utils import chronological_split, load_daily_features, make_sequences

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED = BASE_DIR / "data" / "processed" / "daily_features.csv"
EVAL_DIR = BASE_DIR / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    # avoid div-by-zero in MAPE
    mask = y_true != 0
    mape = mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100 if mask.any() else float("nan")
    print(f"[{name}] MAE={mae:.2f}  RMSE={rmse:.2f}  MAPE={mape:.2f}%")
    return {"mae": float(mae), "rmse": float(rmse), "mape": float(mape)}


def main():
    df = load_daily_features(PROCESSED)
    X, y, meta, feature_cols = make_sequences(df)
    (X_train, y_train, _), (X_val, y_val, _), (X_test, y_test, _) = chronological_split(X, y, meta)

    results = {}

    # 1. Moving average baseline: last 7 days (in the lookback window) * 7 vs actual next-7-day sum
    # X columns index 0 = daily_expense
    ma_pred = X_test[:, -7:, 0].mean(axis=1) * 7
    results["moving_average"] = evaluate(y_test, ma_pred, "Moving Average (7d)")

    # 2. Previous-period average: sum of the last 7 days of the lookback window (direct carry-forward)
    prev_pred = X_test[:, -7:, 0].sum(axis=1)
    results["previous_period"] = evaluate(y_test, prev_pred, "Previous-Period Sum")

    # 3. Linear regression on flattened features
    X_train_flat = X_train.reshape(X_train.shape[0], -1)
    X_test_flat = X_test.reshape(X_test.shape[0], -1)
    lr = LinearRegression()
    lr.fit(X_train_flat, y_train)
    lr_pred = lr.predict(X_test_flat)
    results["linear_regression"] = evaluate(y_test, np.clip(lr_pred, 0, None), "Linear Regression")

    out_path = EVAL_DIR / "baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved baseline results -> {out_path}")


if __name__ == "__main__":
    main()
