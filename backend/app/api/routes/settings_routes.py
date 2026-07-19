from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.system_models import UserSettings
from app.models.user_models import User

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings_for_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings_row = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings_row:
        settings_row = UserSettings(user_id=current_user.id)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return {
        "notify_budget_warnings": settings_row.notify_budget_warnings,
        "notify_recurring_upcoming": settings_row.notify_recurring_upcoming,
        "notify_forecast_ready": settings_row.notify_forecast_ready,
        "forecast_horizon_preference": settings_row.forecast_horizon_preference,
        "data_sharing_opt_in": settings_row.data_sharing_opt_in,
    }


@router.put("")
def update_settings_for_user(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings_row = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings_row:
        settings_row = UserSettings(user_id=current_user.id)
        db.add(settings_row)

    allowed_fields = {
        "notify_budget_warnings", "notify_recurring_upcoming", "notify_forecast_ready",
        "forecast_horizon_preference", "data_sharing_opt_in",
    }
    for field, value in payload.items():
        if field in allowed_fields:
            setattr(settings_row, field, value)

    db.commit()
    db.refresh(settings_row)
    return {"updated": True}


@router.get("/export-data")
def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """GDPR-style personal-data export: returns everything the app knows
    about this user as a single JSON payload."""
    from app.models.finance_models import Budget, GoalContribution, SavingsGoal, Transaction
    from app.models.investment_models import Investment

    return {
        "profile": {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name},
        "transactions": [
            {"date": t.date.isoformat(), "type": t.transaction_type, "amount": float(t.amount), "merchant": t.merchant}
            for t in db.query(Transaction).filter(Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False)).all()
        ],
        "budgets": [
            {"name": b.name, "limit_amount": float(b.limit_amount)}
            for b in db.query(Budget).filter(Budget.user_id == current_user.id, Budget.is_deleted.is_(False)).all()
        ],
        "goals": [
            {"name": g.goal_name, "target_amount": float(g.target_amount), "current_amount": float(g.current_amount)}
            for g in db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id, SavingsGoal.is_deleted.is_(False)).all()
        ],
        "investments": [
            {"name": i.investment_name, "type": i.investment_type, "amount_invested": float(i.amount_invested)}
            for i in db.query(Investment).filter(Investment.user_id == current_user.id, Investment.is_deleted.is_(False)).all()
        ],
    }
