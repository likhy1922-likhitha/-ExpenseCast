from __future__ import annotations

import uuid
from datetime import datetime, date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Mirrors the Supabase auth.users row for this application's own
    relational data. The primary key equals the Supabase auth user id
    (a UUID string) so RLS policies in Postgres can match on it directly."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # Supabase auth UID
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    is_demo_user: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    accounts: Mapped[list["Account"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    user_type: Mapped[str] = mapped_column(String(50))  # student | teenager | salaried | freelancer | other
    preferred_currency: Mapped[str] = mapped_column(String(10), default="INR")
    approx_monthly_income: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    budget_start_day: Mapped[int] = mapped_column(default=1)
    savings_target: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    preferred_categories: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    theme: Mapped[str] = mapped_column(String(10), default="light")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_name: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(50), default="bank")  # bank | wallet | cash | card
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="accounts")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_category_user_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    # user_id is NULL for global default categories, set for user-custom categories
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    category_type: Mapped[str] = mapped_column(String(20), default="expense")  # income | expense | transfer
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
