from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.finance_models import Budget, Transaction
from app.models.user_models import User
from app.schemas.schemas_budget import BudgetCreate, BudgetOut, BudgetProgressOut, BudgetUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = Budget(
        user_id=current_user.id,
        category_id=payload.category_id,
        name=payload.name,
        period_month=payload.period_month,
        period_year=payload.period_year,
        limit_amount=payload.limit_amount,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    log_action(db, current_user.id, "budget.create", "budget", budget.id)
    return budget


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    period_month: int | None = None,
    period_year: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Budget).filter(Budget.user_id == current_user.id, Budget.is_deleted.is_(False))
    if period_month:
        q = q.filter(Budget.period_month == period_month)
    if period_year:
        q = q.filter(Budget.period_year == period_year)
    return q.all()


@router.put("/{budget_id}", response_model=BudgetOut)
def update_budget(
    budget_id: str,
    payload: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id, Budget.user_id == current_user.id, Budget.is_deleted.is_(False)
    ).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id, Budget.user_id == current_user.id, Budget.is_deleted.is_(False)
    ).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    budget.is_deleted = True
    db.commit()
    log_action(db, current_user.id, "budget.delete", "budget", budget_id)
    return None


@router.post("/copy-previous-month", response_model=list[BudgetOut])
def copy_previous_month_budgets(
    target_month: int,
    target_year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prev_month = target_month - 1 or 12
    prev_year = target_year if target_month > 1 else target_year - 1

    source_budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.period_month == prev_month,
        Budget.period_year == prev_year,
        Budget.is_deleted.is_(False),
    ).all()
    if not source_budgets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No budgets found for the previous month.")

    new_budgets = []
    for b in source_budgets:
        new_budget = Budget(
            user_id=current_user.id,
            category_id=b.category_id,
            name=b.name,
            period_month=target_month,
            period_year=target_year,
            limit_amount=b.limit_amount,
        )
        db.add(new_budget)
        new_budgets.append(new_budget)
    db.commit()
    for nb in new_budgets:
        db.refresh(nb)
    return new_budgets


@router.get("/{budget_id}/progress", response_model=BudgetProgressOut)
def get_budget_progress(
    budget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id, Budget.user_id == current_user.id, Budget.is_deleted.is_(False)
    ).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")

    q = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == "expense",
        Transaction.is_deleted.is_(False),
        Transaction.date >= date(budget.period_year, budget.period_month, 1),
    )
    next_month = budget.period_month % 12 + 1
    next_month_year = budget.period_year + (1 if budget.period_month == 12 else 0)
    q = q.filter(Transaction.date < date(next_month_year, next_month, 1))

    if budget.category_id:
        q = q.filter(Transaction.category_id == budget.category_id)

    spent = sum(float(t.amount) for t in q.all())
    remaining = float(budget.limit_amount) - spent
    percent = (spent / float(budget.limit_amount) * 100) if float(budget.limit_amount) > 0 else 0.0

    warning_level = None
    for threshold in (100, 90, 75, 50):
        if percent >= threshold:
            warning_level = str(threshold)
            break

    return BudgetProgressOut(
        budget=budget,
        spent_amount=round(spent, 2),
        remaining_amount=round(remaining, 2),
        percent_used=round(percent, 2),
        warning_level=warning_level,
    )
