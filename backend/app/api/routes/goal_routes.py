from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.finance_models import GoalContribution, SavingsGoal
from app.models.user_models import User
from app.schemas.schemas_budget import ContributionCreate, ContributionOut, GoalCreate, GoalOut, GoalUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/api/goals", tags=["goals"])


def _recompute_monthly_required(goal: SavingsGoal) -> None:
    if not goal.target_date:
        goal.monthly_required_amount = None
        return
    months_remaining = max(
        1,
        (goal.target_date.year - date.today().year) * 12 + (goal.target_date.month - date.today().month),
    )
    remaining_amount = max(0.0, float(goal.target_amount) - float(goal.current_amount))
    goal.monthly_required_amount = round(remaining_amount / months_remaining, 2)


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = SavingsGoal(
        user_id=current_user.id,
        goal_name=payload.goal_name,
        target_amount=payload.target_amount,
        current_amount=payload.current_amount,
        target_date=payload.target_date,
    )
    _recompute_monthly_required(goal)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    log_action(db, current_user.id, "goal.create", "goal", goal.goal_id)
    return goal


@router.get("", response_model=list[GoalOut])
def list_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SavingsGoal).filter(
        SavingsGoal.user_id == current_user.id, SavingsGoal.is_deleted.is_(False)
    ).all()


@router.put("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.goal_id == goal_id, SavingsGoal.user_id == current_user.id, SavingsGoal.is_deleted.is_(False)
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    _recompute_monthly_required(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.goal_id == goal_id, SavingsGoal.user_id == current_user.id, SavingsGoal.is_deleted.is_(False)
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")
    goal.is_deleted = True
    db.commit()
    log_action(db, current_user.id, "goal.delete", "goal", goal_id)
    return None


@router.post("/{goal_id}/contributions", response_model=ContributionOut, status_code=status.HTTP_201_CREATED)
def add_contribution(
    goal_id: str,
    payload: ContributionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.goal_id == goal_id, SavingsGoal.user_id == current_user.id, SavingsGoal.is_deleted.is_(False)
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    contribution = GoalContribution(
        goal_id=goal_id, user_id=current_user.id, amount=payload.amount,
        contribution_date=payload.contribution_date, note=payload.note,
    )
    db.add(contribution)
    goal.current_amount = float(goal.current_amount) + payload.amount
    if goal.current_amount >= float(goal.target_amount):
        goal.status = "completed"
    _recompute_monthly_required(goal)
    db.commit()
    db.refresh(contribution)
    log_action(db, current_user.id, "goal_contribution.create", "goal_contribution", contribution.id)
    return contribution


@router.delete("/{goal_id}/contributions/{contribution_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contribution(
    goal_id: str,
    contribution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contribution = db.query(GoalContribution).filter(
        GoalContribution.id == contribution_id,
        GoalContribution.goal_id == goal_id,
        GoalContribution.user_id == current_user.id,
    ).first()
    if not contribution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found.")

    goal = db.query(SavingsGoal).filter(SavingsGoal.goal_id == goal_id).first()
    if goal:
        goal.current_amount = max(0.0, float(goal.current_amount) - float(contribution.amount))
        if goal.status == "completed" and goal.current_amount < float(goal.target_amount):
            goal.status = "active"
        _recompute_monthly_required(goal)

    db.delete(contribution)
    db.commit()
    log_action(db, current_user.id, "goal_contribution.delete", "goal_contribution", contribution_id)
    return None
