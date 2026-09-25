"""
Final evaluation report: combines synthetic-data test metrics with an
out-of-distribution check against the real Kaggle datasets the user
supplied (kept fully separate from training, per the user's choice).

Usage:
    python evaluate.py

Output:
    machine-learning/evaluation/final_evaluation_report.json
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
from tensorflow import keras

from sequence_utils import load_daily_features, make_sequences, LOOKBACK, HORIZON_7D

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_REAL = BASE_DIR / "data" / "processed" / "daily_features_realdata.csv"
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"
EVAL_DIR = BASE_DIR / "evaluation"


def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    mask = y_true != 0
    mape = mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100 if mask.any() else float("nan")
    print(f"[{name}] MAE={mae:.2f}  RMSE={rmse:.2f}  MAPE={mape:.2f}%")
    return {"mae": float(mae), "rmse": float(rmse), "mape": float(mape), "n_samples": int(len(y_true))}


def main():
    model = keras.models.load_model(MODELS_DIR / "lstm_expense_forecast.keras")
    feature_scaler = joblib.load(SCALERS_DIR / "feature_scaler.joblib")
    target_scaler = joblib.load(SCALERS_DIR / "target_scaler.joblib")

    with open(MODELS_DIR / "model_metadata.json") as f:
        metadata = json.load(f)

    report = {"synthetic_test_metrics": metadata["test_metrics"]}

    # Real-data (INR "ramya" user only, since scale is comparable; the BYN
    # user is left out of the numeric evaluation because its currency
    # differs and metrics in absolute BYN vs INR aren't comparable).
    real_df = load_daily_features(PROCESSED_REAL)
    real_df = real_df[real_df["user_id"] == "real_ramya_user"]

    if len(real_df) > LOOKBACK + HORIZON_7D:
        X_real, y_real, meta_real, feat_cols = make_sequences(real_df, lookback=LOOKBACK, horizon=HORIZON_7D)
        n_features = X_real.shape[-1]
        X_real_scaled = feature_scaler.transform(X_real.reshape(-1, n_features)).reshape(X_real.shape)
        y_pred_s = model.predict(X_real_scaled, verbose=0).flatten()
        y_pred = target_scaler.inverse_transform(y_pred_s.reshape(-1, 1)).flatten()
        y_pred = np.clip(y_pred, 0, None)
        report["real_data_ood_metrics"] = evaluate(
            y_real, y_pred, "LSTM on real Kaggle data (ramya, INR, out-of-distribution)"
        )
        report["real_data_note"] = (
            "This dataset was never used in training or hyperparameter tuning. "
            "It is used purely to sanity-check generalization to real spending patterns."
        )
    else:
        report["real_data_ood_metrics"] = None
        report["real_data_note"] = "Not enough contiguous history to build evaluation sequences."

    out_path = EVAL_DIR / "final_evaluation_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved final evaluation report -> {out_path}")


if __name__ == "__main__":
    main()
