from __future__ import annotations

import uuid
from datetime import datetime, date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.user_models import gen_uuid


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    time: Mapped[str | None] = mapped_column(String(8), nullable=True)  # HH:MM:SS
    transaction_type: Mapped[str] = mapped_column(String(20), index=True)  # income | expense | savings | investment
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)  # comma-separated
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    receipt_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual | csv_import | pdf_import | demo
    import_batch_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # soft delete
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="transactions")  # noqa: F821


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)  # NULL = overall budget
    name: Mapped[str] = mapped_column(String(150))
    period_month: Mapped[int] = mapped_column()  # 1-12
    period_year: Mapped[int] = mapped_column()
    limit_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    warning_threshold_50: Mapped[bool] = mapped_column(Boolean, default=True)
    warning_threshold_75: Mapped[bool] = mapped_column(Boolean, default=True)
    warning_threshold_90: Mapped[bool] = mapped_column(Boolean, default=True)
    warning_threshold_100: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    goal_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_name: Mapped[str] = mapped_column(String(150))
    target_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    current_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    monthly_required_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | completed | abandoned
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contributions: Mapped[list["GoalContribution"]] = relationship(back_populates="goal", cascade="all, delete-orphan")


class GoalContribution(Base):
    __tablename__ = "goal_contributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("savings_goals.goal_id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    contribution_date: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    goal: Mapped["SavingsGoal"] = relationship(back_populates="contributions")
