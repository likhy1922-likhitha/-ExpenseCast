from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user_models import gen_uuid


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    investment_name: Mapped[str] = mapped_column(String(150))
    investment_type: Mapped[str] = mapped_column(String(50))  # fixed_deposit | recurring_deposit | mutual_fund | sip | stocks | gold | provident_fund | other
    amount_invested: Mapped[float] = mapped_column(Numeric(14, 2))
    investment_date: Mapped[date] = mapped_column(Date)
    current_value: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    expected_return_percent: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    merchant: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    average_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    frequency: Mapped[str] = mapped_column(String(20))  # weekly | monthly
    next_expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL = global rule
    keyword: Mapped[str] = mapped_column(String(150), index=True)
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("categories.id", ondelete="CASCADE"))
    match_field: Mapped[str] = mapped_column(String(20), default="merchant")  # merchant | description
    priority: Mapped[int] = mapped_column(default=0)
    source: Mapped[str] = mapped_column(String(20), default="system")  # system | user_correction
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
