from __future__ import annotations

import math
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.finance_models import Transaction
from app.models.user_models import User
from app.schemas.schemas_core import PaginatedTransactions, TransactionCreate, TransactionOut, TransactionUpdate
from app.services.audit import log_action
from app.services.categorization import suggest_category_id
from app.services.recurring_detection import rescan_recurring_for_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _to_out(t: Transaction) -> TransactionOut:
    return TransactionOut.model_validate(t)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_id = payload.category_id
    if category_id is None and payload.transaction_type == "expense":
        category_id = suggest_category_id(db, current_user.id, payload.merchant, payload.description)

    txn = Transaction(
        user_id=current_user.id,
        account_id=payload.account_id,
        date=payload.date,
        time=payload.time,
        transaction_type=payload.transaction_type,
        amount=payload.amount,
        currency=payload.currency,
        category_id=category_id,
        description=payload.description,
        merchant=payload.merchant,
        payment_method=payload.payment_method,
        tags=",".join(payload.tags) if payload.tags else None,
        is_recurring=payload.is_recurring,
        receipt_reference=payload.receipt_reference,
        source="manual",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    log_action(db, current_user.id, "transaction.create", "transaction", txn.transaction_id)
    rescan_recurring_for_user(db, current_user.id)
    return _to_out(txn)


@router.get("", response_model=PaginatedTransactions)
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    transaction_type: Optional[Literal["income", "expense", "savings", "investment"]] = None,
    category_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    is_recurring: Optional[bool] = None,
    sort_by: Literal["date", "amount", "created_at"] = "date",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    q = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.is_deleted.is_(False),
    )
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Transaction.description.ilike(like), Transaction.merchant.ilike(like)))
    if transaction_type:
        q = q.filter(Transaction.transaction_type == transaction_type)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if date_from:
        q = q.filter(Transaction.date >= date_from)
    if date_to:
        q = q.filter(Transaction.date <= date_to)
    if is_recurring is not None:
        q = q.filter(Transaction.is_recurring == is_recurring)

    total = q.count()
    sort_col = getattr(Transaction, sort_by)
    q = q.order_by(asc(sort_col) if sort_order == "asc" else desc(sort_col))
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedTransactions(
        items=[_to_out(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.is_deleted.is_(False),
    ).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    return _to_out(txn)


@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.is_deleted.is_(False),
    ).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    data = payload.model_dump(exclude_unset=True)
    if "tags" in data:
        tags = data.pop("tags")
        txn.tags = ",".join(tags) if tags else None
    for field, value in data.items():
        setattr(txn, field, value)

    db.commit()
    db.refresh(txn)
    log_action(db, current_user.id, "transaction.update", "transaction", txn.transaction_id)
    return _to_out(txn)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.is_deleted.is_(False),
    ).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    txn.is_deleted = True
    db.commit()
    log_action(db, current_user.id, "transaction.delete", "transaction", txn.transaction_id)
    return None


@router.post("/bulk-update", response_model=list[TransactionOut])
def bulk_update_transactions(
    transaction_ids: list[str],
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txns = db.query(Transaction).filter(
        Transaction.transaction_id.in_(transaction_ids),
        Transaction.user_id == current_user.id,
        Transaction.is_deleted.is_(False),
    ).all()
    data = payload.model_dump(exclude_unset=True)
    data.pop("tags", None)  # bulk tag overwrite intentionally unsupported to avoid accidental data loss
    for txn in txns:
        for field, value in data.items():
            setattr(txn, field, value)
    db.commit()
    log_action(db, current_user.id, "transaction.bulk_update", "transaction", None)
    return [_to_out(t) for t in txns]


@router.get("/export/csv")
def export_transactions_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import csv
    import io

    from fastapi.responses import StreamingResponse

    txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.is_deleted.is_(False),
    ).order_by(Transaction.date.desc()).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "type", "amount", "currency", "category_id", "merchant", "description", "payment_method"])
    for t in txns:
        writer.writerow([t.date, t.transaction_type, t.amount, t.currency, t.category_id, t.merchant, t.description, t.payment_method])
    buf.seek(0)
    log_action(db, current_user.id, "transaction.export_csv", "transaction", None)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expensecast_transactions.csv"},
    )
