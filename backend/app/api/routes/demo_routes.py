from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.models.finance_models import Budget, SavingsGoal, Transaction
from app.models.investment_models import Investment
from app.models.user_models import User, UserProfile
from app.seed.seed_demo import seed_demo_user

router = APIRouter(prefix="/api/demo", tags=["demo"])
settings = get_settings()


@router.get("/status")
def demo_status():
    return {"demo_mode_enabled": settings.ENABLE_DEMO_MODE}


@router.post("/activate")
def activate_demo(db: Session = Depends(get_db)):
    """
    Idempotently ensures the isolated demo user + demo dataset exists and
    returns its id. The frontend signs the browser into this fixed demo
    account (via a Supabase anonymous/demo session) rather than creating a
    new demo user per visitor, keeping Demo Mode data isolated from every
    real personal account by construction (a completely separate user_id).
    """
    if not settings.ENABLE_DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo Mode is disabled.")

    demo_user = db.get(User, settings.DEMO_USER_ID)
    if demo_user is None:
        seed_demo_user(db)

    return {"demo_user_id": settings.DEMO_USER_ID}
