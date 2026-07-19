"""
Trains the LSTM expense-forecasting model.

Architecture: two stacked LSTM layers -> dense head, predicting the sum of
the next 7 days' expense from the previous 30 days of engineered features.

Usage:
    python train_lstm.py

Outputs:
    machine-learning/models/lstm_expense_forecast.keras
    machine-learning/scalers/feature_scaler.joblib
    machine-learning/scalers/target_scaler.joblib
    machine-learning/models/model_metadata.json
    machine-learning/evaluation/lstm_results.json
    machine-learning/evaluation/training_history.png
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras import layers

from sequence_utils import chronological_split, load_daily_features, make_sequences, LOOKBACK, HORIZON_7D

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED = BASE_DIR / "data" / "processed" / "daily_features.csv"
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"
EVAL_DIR = BASE_DIR / "evaluation"
for d in (MODELS_DIR, SCALERS_DIR, EVAL_DIR):
    d.mkdir(parents=True, exist_ok=True)

SEED = 42
np.random.seed(SEED)
keras.utils.set_random_seed(SEED)


def scale_features(X_train, X_val, X_test):
    n_features = X_train.shape[-1]
    scaler = MinMaxScaler()
    scaler.fit(X_train.reshape(-1, n_features))

    def apply(X):
        shape = X.shape
        flat = X.reshape(-1, n_features)
        scaled = scaler.transform(flat)
        return scaled.reshape(shape)

    return apply(X_train), apply(X_val), apply(X_test), scaler


def scale_target(y_train, y_val, y_test):
    scaler = MinMaxScaler()
    y_train_2d = y_train.reshape(-1, 1)
    scaler.fit(y_train_2d)
    return (
        scaler.transform(y_train.reshape(-1, 1)).flatten(),
        scaler.transform(y_val.reshape(-1, 1)).flatten(),
        scaler.transform(y_test.reshape(-1, 1)).flatten(),
        scaler,
    )


def build_model(n_timesteps: int, n_features: int) -> keras.Model:
    model = keras.Sequential([
        layers.Input(shape=(n_timesteps, n_features)),
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(32),
        layers.Dropout(0.2),
        layers.Dense(16, activation="relu"),
        layers.Dense(1),
    ])
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3), loss="mse", metrics=["mae"])
    return model


def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    mask = y_true != 0
    mape = mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100 if mask.any() else float("nan")
    print(f"[{name}] MAE={mae:.2f}  RMSE={rmse:.2f}  MAPE={mape:.2f}%")
    return {"mae": float(mae), "rmse": float(rmse), "mape": float(mape)}


def main():
    df = load_daily_features(PROCESSED)
    X, y, meta, feature_cols = make_sequences(df, lookback=LOOKBACK, horizon=HORIZON_7D)
    print(f"Total sequences: {len(X)}, features: {feature_cols}")

    (X_train, y_train, _), (X_val, y_val, _), (X_test, y_test, meta_test) = chronological_split(X, y, meta)
    print(f"Train: {len(X_train)}  Val: {len(X_val)}  Test: {len(X_test)}")

    X_train_s, X_val_s, X_test_s, feature_scaler = scale_features(X_train, X_val, X_test)
    y_train_s, y_val_s, y_test_s, target_scaler = scale_target(y_train, y_val, y_test)

    model = build_model(n_timesteps=LOOKBACK, n_features=X_train.shape[-1])
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-5),
    ]

    history = model.fit(
        X_train_s, y_train_s,
        validation_data=(X_val_s, y_val_s),
        epochs=100,
        batch_size=32,
        callbacks=callbacks,
        verbose=2,
    )

    # Evaluate on test set (inverse-transform back to rupee scale)
    y_pred_s = model.predict(X_test_s).flatten()
    y_pred = target_scaler.inverse_transform(y_pred_s.reshape(-1, 1)).flatten()
    y_pred = np.clip(y_pred, 0, None)

    results = {"lstm": evaluate(y_test, y_pred, "LSTM (7-day expense forecast)")}

    # Merge with baseline results if present, for a combined comparison report
    baseline_path = EVAL_DIR / "baseline_results.json"
    if baseline_path.exists():
        with open(baseline_path) as f:
            results.update(json.load(f))

    with open(EVAL_DIR / "lstm_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Save training curve
    plt.figure(figsize=(8, 5))
    plt.plot(history.history["loss"], label="train_loss")
    plt.plot(history.history["val_loss"], label="val_loss")
    plt.xlabel("Epoch")
    plt.ylabel("MSE (scaled)")
    plt.title("ExpenseCast LSTM Training History")
    plt.legend()
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "training_history.png", dpi=120)
    plt.close()

    # Save model + scalers + metadata
    model_path = MODELS_DIR / "lstm_expense_forecast.keras"
    model.save(model_path)
    joblib.dump(feature_scaler, SCALERS_DIR / "feature_scaler.joblib")
    joblib.dump(target_scaler, SCALERS_DIR / "target_scaler.joblib")

    metadata = {
        "model_file": model_path.name,
        "feature_scaler_file": "feature_scaler.joblib",
        "target_scaler_file": "target_scaler.joblib",
        "lookback_days": LOOKBACK,
        "horizon_days": HORIZON_7D,
        "feature_columns": feature_cols,
        "target_column": "daily_expense (summed over horizon)",
        "training_sequences": len(X_train),
        "validation_sequences": len(X_val),
        "test_sequences": len(X_test),
        "test_metrics": results["lstm"],
        "trained_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "min_history_days_for_personalized_forecast": 60,
        "min_history_days_for_low_confidence_forecast": 30,
    }
    with open(MODELS_DIR / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved model -> {model_path}")
    print(f"Saved scalers -> {SCALERS_DIR}")
    print(f"Saved metadata -> {MODELS_DIR / 'model_metadata.json'}")
    print("\n=== Model comparison (test set) ===")
    for k, v in results.items():
        print(f"{k:20s} MAE={v['mae']:.2f}  RMSE={v['rmse']:.2f}  MAPE={v['mape']:.2f}%")


if __name__ == "__main__":
    main()
