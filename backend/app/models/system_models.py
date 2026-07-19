from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user_models import gen_uuid


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    predicted_next_1_day: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    predicted_next_7_days: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    predicted_next_30_days: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    predicted_next_90_days: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    predicted_end_of_month_balance: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    overspending_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)  # low | medium | high
    confidence_level: Mapped[str] = mapped_column(String(30))  # insufficient_data | low_confidence | personalized
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    notification_type: Mapped[str] = mapped_column(String(50))  # budget_warning | recurring_upcoming | forecast_ready | goal_progress
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    notify_budget_warnings: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_recurring_upcoming: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_forecast_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    forecast_horizon_preference: Mapped[str] = mapped_column(String(10), default="30d")
    data_sharing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100))  # e.g. "transaction.create", "auth.login"
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
