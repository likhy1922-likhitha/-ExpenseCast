from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.forecasting.forecast_service import generate_forecast
from app.models.system_models import Prediction
from app.models.user_models import User
from app.schemas.schemas_import_forecast import ForecastOut, ModelStatusOut
from app.services.audit import log_action

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])

ML_SCRIPTS_DIR = Path(__file__).resolve().parents[2].parent / "machine-learning" / "scripts"
if str(ML_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(ML_SCRIPTS_DIR))


@router.post("/generate", response_model=ForecastOut)
def generate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = generate_forecast(db, current_user.id)

    if result["confidence_level"] != "insufficient_data":
        prediction = Prediction(
            user_id=current_user.id,
            predicted_next_1_day=result.get("predicted_next_1_day"),
            predicted_next_7_days=result.get("predicted_next_7_days"),
            predicted_next_30_days=result.get("predicted_next_30_days"),
            predicted_next_90_days=result.get("predicted_next_90_days"),
            overspending_risk=result.get("overspending_risk"),
            confidence_level=result["confidence_level"],
            model_version="lstm_expense_forecast_v1",
        )
        db.add(prediction)
        db.commit()

    log_action(db, current_user.id, "forecast.generate")
    return ForecastOut(generated_at=datetime.utcnow(), **result)


@router.get("/latest", response_model=ForecastOut)
def get_latest(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    latest = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(Prediction.generated_at.desc()).first()

    if not latest:
        result = generate_forecast(db, current_user.id)
        return ForecastOut(generated_at=datetime.utcnow(), **result)

    return ForecastOut(
        confidence_level=latest.confidence_level,
        history_days_available=0,
        predicted_next_1_day=float(latest.predicted_next_1_day) if latest.predicted_next_1_day else None,
        predicted_next_7_days=float(latest.predicted_next_7_days) if latest.predicted_next_7_days else None,
        predicted_next_30_days=float(latest.predicted_next_30_days) if latest.predicted_next_30_days else None,
        predicted_next_90_days=float(latest.predicted_next_90_days) if latest.predicted_next_90_days else None,
        overspending_risk=latest.overspending_risk,
        generated_at=latest.generated_at,
    )


@router.get("/history", response_model=list[ForecastOut])
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    predictions = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(Prediction.generated_at.desc()).limit(30).all()
    return [
        ForecastOut(
            confidence_level=p.confidence_level,
            history_days_available=0,
            predicted_next_1_day=float(p.predicted_next_1_day) if p.predicted_next_1_day else None,
            predicted_next_7_days=float(p.predicted_next_7_days) if p.predicted_next_7_days else None,
            predicted_next_30_days=float(p.predicted_next_30_days) if p.predicted_next_30_days else None,
            predicted_next_90_days=float(p.predicted_next_90_days) if p.predicted_next_90_days else None,
            overspending_risk=p.overspending_risk,
            generated_at=p.generated_at,
        )
        for p in predictions
    ]


@router.get("/model-status", response_model=ModelStatusOut)
def model_status():
    from predict import get_metadata, is_model_available

    if not is_model_available():
        return ModelStatusOut(model_available=False)

    metadata = get_metadata()
    return ModelStatusOut(
        model_available=True,
        lookback_days=metadata.get("lookback_days"),
        horizon_days=metadata.get("horizon_days"),
        trained_at=metadata.get("trained_at"),
        test_mae=metadata.get("test_metrics", {}).get("mae"),
        test_rmse=metadata.get("test_metrics", {}).get("rmse"),
        test_mape=metadata.get("test_metrics", {}).get("mape"),
    )
