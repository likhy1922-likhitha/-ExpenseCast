from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.investment_models import Investment
from app.models.user_models import User
from app.schemas.schemas_budget import InvestmentCreate, InvestmentOut, InvestmentUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/api/investments", tags=["investments"])


@router.post("", response_model=InvestmentOut, status_code=status.HTTP_201_CREATED)
def create_investment(
    payload: InvestmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = Investment(
        user_id=current_user.id,
        investment_name=payload.investment_name,
        investment_type=payload.investment_type,
        amount_invested=payload.amount_invested,
        investment_date=payload.investment_date,
        current_value=payload.current_value,
        expected_return_percent=payload.expected_return_percent,
        notes=payload.notes,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    log_action(db, current_user.id, "investment.create", "investment", inv.id)
    return inv


@router.get("", response_model=list[InvestmentOut])
def list_investments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Investment).filter(
        Investment.user_id == current_user.id, Investment.is_deleted.is_(False)
    ).all()


@router.put("/{investment_id}", response_model=InvestmentOut)
def update_investment(
    investment_id: str,
    payload: InvestmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Investment).filter(
        Investment.id == investment_id, Investment.user_id == current_user.id, Investment.is_deleted.is_(False)
    ).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Investment).filter(
        Investment.id == investment_id, Investment.user_id == current_user.id, Investment.is_deleted.is_(False)
    ).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found.")
    inv.is_deleted = True
    db.commit()
    log_action(db, current_user.id, "investment.delete", "investment", investment_id)
    return None
