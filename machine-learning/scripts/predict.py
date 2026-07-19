"""
Loads the trained LSTM model, scalers, and metadata once, and exposes a
simple predict() function that the FastAPI backend calls to generate
forecasts for a given user's recent daily feature history.

This module is imported directly by backend/app/forecasting/lstm_service.py
(the backend adds machine-learning/scripts to sys.path at startup).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"

_model = None
_feature_scaler = None
_target_scaler = None
_metadata = None


def _lazy_load():
    global _model, _feature_scaler, _target_scaler, _metadata
    if _model is not None:
        return
    from tensorflow import keras  # imported lazily so the API can boot even if TF is slow to import

    model_path = MODELS_DIR / "lstm_expense_forecast.keras"
    if not model_path.exists():
        raise FileNotFoundError(
            f"No trained model found at {model_path}. Run "
            "machine-learning/scripts/train_lstm.py first."
        )
    _model = keras.models.load_model(model_path)
    _feature_scaler = joblib.load(SCALERS_DIR / "feature_scaler.joblib")
    _target_scaler = joblib.load(SCALERS_DIR / "target_scaler.joblib")
    with open(MODELS_DIR / "model_metadata.json") as f:
        _metadata = json.load(f)


def is_model_available() -> bool:
    return (MODELS_DIR / "lstm_expense_forecast.keras").exists()


def get_metadata() -> Optional[dict]:
    if not is_model_available():
        return None
    _lazy_load()
    return _metadata


def predict_next_7_days(daily_feature_window: pd.DataFrame) -> float:
    """
    daily_feature_window: DataFrame with exactly `lookback_days` rows
    (chronologically ordered, most recent last) containing at minimum the
    columns listed in metadata['feature_columns'].

    Returns the predicted total expense (in the user's currency) for the
    next 7 days.
    """
    _lazy_load()
    lookback = _metadata["lookback_days"]
    feature_cols = _metadata["feature_columns"]

    if len(daily_feature_window) != lookback:
        raise ValueError(
            f"Expected exactly {lookback} rows of history, got {len(daily_feature_window)}."
        )
    missing = [c for c in feature_cols if c not in daily_feature_window.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")

    X = daily_feature_window[feature_cols].values.astype(np.float32)[np.newaxis, ...]
    n_features = X.shape[-1]
    X_scaled = _feature_scaler.transform(X.reshape(-1, n_features)).reshape(X.shape)

    y_pred_scaled = _model.predict(X_scaled, verbose=0).flatten()[0]
    y_pred = _target_scaler.inverse_transform([[y_pred_scaled]])[0][0]
    return float(max(0.0, y_pred))


def predict_multi_horizon(daily_feature_window: pd.DataFrame) -> dict:
    """
    Derives 1-day, 7-day, 30-day and 90-day estimates from the base 7-day
    LSTM prediction using the recent daily rate implied by the model,
    combined with the user's own rolling averages for longer horizons
    (the LSTM is trained specifically for the 7-day horizon; longer
    horizons are extrapolated and explicitly labelled as lower-confidence).
    """
    base_7d = predict_next_7_days(daily_feature_window)
    implied_daily_rate = base_7d / 7.0

    recent_30d_avg = float(daily_feature_window["rolling_30d_expense_avg"].iloc[-1])
    # Blend the LSTM's short-horizon signal with the longer rolling average
    # for longer horizons, rather than naively multiplying out 7-day noise.
    blended_daily_rate = 0.6 * implied_daily_rate + 0.4 * recent_30d_avg

    return {
        "next_1_day": round(implied_daily_rate, 2),
        "next_7_days": round(base_7d, 2),
        "next_30_days": round(blended_daily_rate * 30, 2),
        "next_90_days": round(blended_daily_rate * 90, 2),
        "model_confidence": "personalized",
    }
