from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.finance_models import Transaction
from app.models.investment_models import RecurringTransaction

SIMILARITY_AMOUNT_TOLERANCE = 0.10  # 10% amount variance still counts as "similar"
MIN_OCCURRENCES = 3


def _amounts_similar(a: float, b: float) -> bool:
    if a == 0 or b == 0:
        return a == b
    return abs(a - b) / max(a, b) <= SIMILARITY_AMOUNT_TOLERANCE


def rescan_recurring_for_user(db: Session, user_id: str) -> list[RecurringTransaction]:
    """
    Groups the user's expense transactions by merchant, and flags a merchant
    as a recurring-payment *candidate* when it has at least MIN_OCCURRENCES
    transactions with similar amounts spaced roughly monthly or weekly
    apart. Candidates are written with confirmed_by_user=False; the
    frontend must still ask the user to confirm before it's treated as
    truly recurring, per the project's requirement not to auto-mark
    recurring status.
    """
    txns = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.is_deleted.is_(False),
            Transaction.merchant.isnot(None),
        )
        .order_by(Transaction.date.asc())
        .all()
    )

    by_merchant: dict[str, list[Transaction]] = defaultdict(list)
    for t in txns:
        by_merchant[t.merchant.strip().lower()].append(t)

    candidates: list[RecurringTransaction] = []
    for merchant, group in by_merchant.items():
        if len(group) < MIN_OCCURRENCES:
            continue

        # cluster by similar amount
        group_sorted = sorted(group, key=lambda t: t.date)
        amounts = [float(t.amount) for t in group_sorted]
        avg_amount = sum(amounts) / len(amounts)
        similar = [t for t in group_sorted if _amounts_similar(float(t.amount), avg_amount)]
        if len(similar) < MIN_OCCURRENCES:
            continue

        gaps = [
            (similar[i].date - similar[i - 1].date).days
            for i in range(1, len(similar))
        ]
        if not gaps:
            continue
        avg_gap = sum(gaps) / len(gaps)

        if 25 <= avg_gap <= 35:
            frequency = "monthly"
        elif 5 <= avg_gap <= 9:
            frequency = "weekly"
        else:
            continue  # not a recognizable recurring interval

        last_date = similar[-1].date
        next_expected = last_date + timedelta(days=round(avg_gap))

        existing = (
            db.query(RecurringTransaction)
            .filter(RecurringTransaction.user_id == user_id, RecurringTransaction.merchant == merchant)
            .first()
        )
        if existing:
            existing.average_amount = round(avg_amount, 2)
            existing.frequency = frequency
            existing.next_expected_date = next_expected
            candidates.append(existing)
        else:
            new_candidate = RecurringTransaction(
                user_id=user_id,
                merchant=merchant,
                average_amount=round(avg_amount, 2),
                frequency=frequency,
                next_expected_date=next_expected,
                confirmed_by_user=False,
                is_active=True,
            )
            db.add(new_candidate)
            candidates.append(new_candidate)

    db.commit()
    return candidates
