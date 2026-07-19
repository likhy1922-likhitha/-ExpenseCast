from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.finance_models import Transaction
from app.models.user_models import User, UserProfile
from app.schemas.schemas_core import ProfileCreate, ProfileOut, ProfileUpdate, UserOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists.")

    current_user.full_name = payload.full_name

    profile = UserProfile(
        user_id=current_user.id,
        user_type=payload.user_type,
        preferred_currency=payload.preferred_currency,
        approx_monthly_income=payload.approx_monthly_income,
        budget_start_day=payload.budget_start_day,
        savings_target=payload.savings_target,
        preferred_categories=",".join(payload.preferred_categories) if payload.preferred_categories else None,
        onboarding_completed=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("", response_model=ProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found. Complete onboarding first.")
    return profile


@router.put("", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data:
        current_user.full_name = data.pop("full_name")
    if "preferred_categories" in data:
        cats = data.pop("preferred_categories")
        profile.preferred_categories = ",".join(cats) if cats else None
    for field, value in data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hard-deletes the user and all owned records (cascades configured on
    every foreign key back to `users`)."""
    db.delete(current_user)
    db.commit()
    return None
