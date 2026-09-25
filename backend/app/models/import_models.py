from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user_models import gen_uuid


class ImportedFile(Base):
    __tablename__ = "imported_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(10))  # csv | pdf
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    detected_encoding: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detected_delimiter: Mapped[str | None] = mapped_column(String(5), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded | previewed | confirmed | cancelled | failed
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    imported_file_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("imported_files.id", ondelete="SET NULL"), nullable=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0)
    skipped_duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    column_mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ImportError_(Base):
    __tablename__ = "import_errors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    import_batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("import_batches.id", ondelete="CASCADE"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    raw_row_json: Mapped[str] = mapped_column(Text)
    error_reason: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
