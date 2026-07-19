from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.finance_models import Budget, SavingsGoal, Transaction
from app.models.investment_models import Investment
from app.models.user_models import User
from app.services.audit import log_action

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _period_range(period: Literal["weekly", "monthly", "yearly"]) -> tuple[date, date]:
    today = date.today()
    if period == "weekly":
        return today - timedelta(days=7), today
    if period == "monthly":
        return today.replace(day=1), today
    return today.replace(month=1, day=1), today


def _build_report(db: Session, user_id: str, period: Literal["weekly", "monthly", "yearly"]) -> dict:
    start, end = _period_range(period)
    txns = db.query(Transaction).filter(
        Transaction.user_id == user_id, Transaction.is_deleted.is_(False),
        Transaction.date >= start, Transaction.date <= end,
    ).all()

    income = sum(float(t.amount) for t in txns if t.transaction_type == "income")
    expense = sum(float(t.amount) for t in txns if t.transaction_type == "expense")
    savings = sum(float(t.amount) for t in txns if t.transaction_type == "savings")
    investment = sum(float(t.amount) for t in txns if t.transaction_type == "investment")

    by_category: dict[str, float] = defaultdict(float)
    for t in txns:
        if t.transaction_type == "expense":
            by_category[t.category_id or "uncategorized"] += float(t.amount)

    budgets = db.query(Budget).filter(
        Budget.user_id == user_id, Budget.is_deleted.is_(False),
        Budget.period_month == date.today().month, Budget.period_year == date.today().year,
    ).all()
    budget_total = sum(float(b.limit_amount) for b in budgets)

    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id, SavingsGoal.is_deleted.is_(False)).all()
    investments = db.query(Investment).filter(Investment.user_id == user_id, Investment.is_deleted.is_(False)).all()

    return {
        "period": period,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "total_savings": round(savings, 2),
        "total_investment": round(investment, 2),
        "net_change": round(income - expense - savings - investment, 2),
        "category_breakdown": {k: round(v, 2) for k, v in by_category.items()},
        "budget_total": round(budget_total, 2),
        "budget_utilization_percent": round(expense / budget_total * 100, 2) if budget_total > 0 else None,
        "active_savings_goals": len([g for g in goals if g.status == "active"]),
        "investment_portfolio_value": round(sum(float(i.current_value or i.amount_invested) for i in investments), 2),
        "transaction_count": len(txns),
    }


@router.get("/weekly")
def weekly_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_report(db, current_user.id, "weekly")


@router.get("/monthly")
def monthly_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_report(db, current_user.id, "monthly")


@router.get("/yearly")
def yearly_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_report(db, current_user.id, "yearly")


@router.get("/export/csv")
def export_report_csv(
    period: Literal["weekly", "monthly", "yearly"] = "monthly",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _build_report(db, current_user.id, period)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Metric", "Value"])
    for k, v in report.items():
        if k == "category_breakdown":
            continue
        writer.writerow([k, v])
    writer.writerow([])
    writer.writerow(["Category", "Amount"])
    for cat, amt in report["category_breakdown"].items():
        writer.writerow([cat, amt])
    buf.seek(0)
    log_action(db, current_user.id, "report.export_csv")
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=expensecast_{period}_report.csv"},
    )


@router.get("/export/pdf")
def export_report_pdf(
    period: Literal["weekly", "monthly", "yearly"] = "monthly",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    report = _build_report(db, current_user.id, period)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 30 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, "ExpenseCast Financial Report")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Period: {report['period'].capitalize()} ({report['start_date']} to {report['end_date']})")
    y -= 12 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Summary")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    for label, key in [
        ("Total Income", "total_income"), ("Total Expense", "total_expense"),
        ("Total Savings", "total_savings"), ("Total Investment", "total_investment"),
        ("Net Change", "net_change"), ("Transactions", "transaction_count"),
    ]:
        c.drawString(20 * mm, y, f"{label}: {report[key]}")
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Category Breakdown")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    for cat, amt in report["category_breakdown"].items():
        if y < 20 * mm:
            c.showPage()
            y = height - 20 * mm
        c.drawString(20 * mm, y, f"{cat}: {amt}")
        y -= 6 * mm

    c.showPage()
    c.save()
    buf.seek(0)

    log_action(db, current_user.id, "report.export_pdf")
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=expensecast_{period}_report.pdf"},
    )
