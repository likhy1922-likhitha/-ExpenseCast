from __future__ import annotations

import io
import json
import os
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.database.session import get_db
from app.imports.csv_import_service import build_preview_rows, detect_delimiter, detect_encoding, suggest_column_mapping
from app.imports.pdf_import_service import extract_lines_pdfplumber, extract_text_pymupdf, is_scanned_pdf, parse_transaction_lines
from app.models.finance_models import Transaction
from app.models.import_models import ImportBatch, ImportedFile, ImportError_
from app.models.user_models import User
from app.schemas.schemas_import_forecast import (
    ColumnMapping, ConfirmImportRequest, CsvPreviewResponse, ImportSummaryOut,
    PdfPreviewResponse, PdfPreviewRow,
)
from app.services.audit import log_action
from app.services.categorization import DEFAULT_KEYWORD_RULES

router = APIRouter(prefix="/api/imports", tags=["imports"])
settings = get_settings()

ALLOWED_CSV_EXTENSIONS = {".csv"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

# In-memory cache of parsed dataframes keyed by imported_file_id, so the
# preview -> confirm flow doesn't need to re-upload the file. Cleared after
# confirm/cancel. In a multi-worker deployment this should move to Redis;
# noted in DEPLOYMENT_GUIDE.md.
_PENDING_IMPORTS: dict[str, dict] = {}


def _safe_temp_path(filename: str) -> Path:
    """Never trusts the uploaded filename directly -- generates a random
    server-side name and keeps only a safe extension from the original."""
    ext = Path(filename).suffix.lower()
    tmp_dir = Path(settings.UPLOAD_TMP_DIR)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir / f"{uuid.uuid4()}{ext}"


@router.post("/csv/upload", response_model=CsvPreviewResponse)
async def upload_csv(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_CSV_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv files are accepted.")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds maximum upload size.")
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    encoding = detect_encoding(raw_bytes)
    try:
        text = raw_bytes.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        text = raw_bytes.decode("utf-8", errors="replace")
        encoding = "utf-8"

    delimiter = detect_delimiter(text[:2000])

    try:
        df = pd.read_csv(io.StringIO(text), delimiter=delimiter, dtype=str, keep_default_na=False, na_filter=False)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse CSV: {exc}") from exc

    if df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file contains no rows.")

    headers = list(df.columns)
    mapping = suggest_column_mapping(headers)

    imported_file = ImportedFile(
        user_id=current_user.id,
        original_filename=file.filename or "upload.csv",
        file_type="csv",
        file_size_bytes=len(raw_bytes),
        detected_encoding=encoding,
        detected_delimiter=delimiter,
        status="previewed",
    )
    db.add(imported_file)
    db.commit()
    db.refresh(imported_file)

    existing_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False)
    ).all()
    preview_rows = build_preview_rows(df, mapping, existing_txns)

    _PENDING_IMPORTS[imported_file.id] = {
        "df": df, "mapping": mapping, "user_id": current_user.id,
    }

    log_action(db, current_user.id, "import.csv_upload", "imported_file", imported_file.id)

    return CsvPreviewResponse(
        imported_file_id=imported_file.id,
        detected_encoding=encoding,
        detected_delimiter=delimiter,
        detected_columns=headers,
        suggested_mapping=mapping,
        preview_rows=preview_rows,
        total_rows=len(df),
        valid_rows=sum(1 for r in preview_rows if r.is_valid),
        invalid_rows=sum(1 for r in preview_rows if not r.is_valid),
        duplicate_rows=sum(1 for r in preview_rows if r.is_duplicate),
    )


@router.post("/csv/remap", response_model=CsvPreviewResponse)
def remap_csv_columns(
    imported_file_id: str,
    mapping: ColumnMapping,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lets the user manually correct the auto-detected column mapping and
    re-preview before confirming the import."""
    cached = _PENDING_IMPORTS.get(imported_file_id)
    if not cached or cached["user_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending import found for this id.")

    df = cached["df"]
    existing_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False)
    ).all()
    preview_rows = build_preview_rows(df, mapping, existing_txns)
    cached["mapping"] = mapping

    imported_file = db.get(ImportedFile, imported_file_id)

    return CsvPreviewResponse(
        imported_file_id=imported_file_id,
        detected_encoding=imported_file.detected_encoding or "utf-8",
        detected_delimiter=imported_file.detected_delimiter or ",",
        detected_columns=list(df.columns),
        suggested_mapping=mapping,
        preview_rows=preview_rows,
        total_rows=len(df),
        valid_rows=sum(1 for r in preview_rows if r.is_valid),
        invalid_rows=sum(1 for r in preview_rows if not r.is_valid),
        duplicate_rows=sum(1 for r in preview_rows if r.is_duplicate),
    )


@router.post("/csv/confirm", response_model=ImportSummaryOut)
def confirm_csv_import(
    payload: ConfirmImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cached = _PENDING_IMPORTS.get(payload.imported_file_id)
    if not cached or cached["user_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending import found for this id.")

    df = cached["df"]
    existing_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False)
    ).all()
    preview_rows = build_preview_rows(df, payload.mapping, existing_txns, max_preview_rows=len(df))

    batch = ImportBatch(
        user_id=current_user.id,
        imported_file_id=payload.imported_file_id,
        total_rows=len(preview_rows),
        column_mapping_json=json.dumps(payload.mapping.model_dump()),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    imported_count = duplicate_count = invalid_count = 0
    for row in preview_rows:
        if row.row_number not in payload.row_numbers_to_import:
            continue
        if not row.is_valid:
            invalid_count += 1
            db.add(ImportError_(
                import_batch_id=batch.id, row_number=row.row_number,
                raw_row_json=json.dumps(row.raw), error_reason=row.validation_message or "Invalid row",
            ))
            continue
        if row.is_duplicate:
            duplicate_count += 1
            continue

        txn = Transaction(
            user_id=current_user.id,
            date=row.parsed_date,
            transaction_type=row.parsed_type or "expense",
            amount=row.parsed_amount,
            description=row.raw.get(payload.mapping.description_column or "", "") or None,
            merchant=row.raw.get(payload.mapping.merchant_column or "", "") or None,
            source="csv_import",
            import_batch_id=batch.id,
        )
        db.add(txn)
        imported_count += 1

    batch.imported_rows = imported_count
    batch.skipped_duplicate_rows = duplicate_count
    batch.invalid_rows = invalid_count

    imported_file = db.get(ImportedFile, payload.imported_file_id)
    if imported_file:
        imported_file.status = "confirmed"

    db.commit()
    del _PENDING_IMPORTS[payload.imported_file_id]

    log_action(db, current_user.id, "import.csv_confirm", "import_batch", batch.id)

    return ImportSummaryOut(
        import_batch_id=batch.id, total_rows=batch.total_rows,
        imported_rows=imported_count, skipped_duplicate_rows=duplicate_count, invalid_rows=invalid_count,
    )


@router.post("/csv/cancel/{imported_file_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_csv_import(
    imported_file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cached = _PENDING_IMPORTS.pop(imported_file_id, None)
    imported_file = db.get(ImportedFile, imported_file_id)
    if imported_file and imported_file.user_id == current_user.id:
        imported_file.status = "cancelled"
        db.commit()
    return None


# --- PDF import ---

@router.post("/pdf/upload", response_model=PdfPreviewResponse)
async def upload_pdf(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_PDF_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .pdf files are accepted.")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds maximum upload size.")

    temp_path = _safe_temp_path(file.filename or "upload.pdf")
    temp_path.write_bytes(raw_bytes)

    try:
        scanned = is_scanned_pdf(str(temp_path))
        if scanned:
            # OCR fallback would run here (pytesseract). Declared as an
            # optional dependency per the spec; if not installed we tell
            # the user plainly instead of silently returning nothing.
            try:
                import pytesseract
                from pdf2image import convert_from_path
                images = convert_from_path(str(temp_path))
                text = "\n".join(pytesseract.image_to_string(img) for img in images)
                lines = text.split("\n")
                extraction_method = "ocr_fallback"
            except ImportError:
                lines = []
                extraction_method = "ocr_unavailable"
        else:
            lines = extract_lines_pdfplumber(str(temp_path))
            extraction_method = "pdfplumber_text_extraction"

        parsed_rows = parse_transaction_lines(lines)

        imported_file = ImportedFile(
            user_id=current_user.id,
            original_filename=file.filename or "upload.pdf",
            file_type="pdf",
            file_size_bytes=len(raw_bytes),
            status="previewed",
        )
        db.add(imported_file)
        db.commit()
        db.refresh(imported_file)

        existing_txns = db.query(Transaction).filter(
            Transaction.user_id == current_user.id, Transaction.is_deleted.is_(False)
        ).all()
        existing_signatures = {
            (t.date.isoformat(), round(float(t.amount), 2)) for t in existing_txns
        }

        preview_rows = []
        for i, row in enumerate(parsed_rows):
            amount = row["debit"] or row["credit"]
            is_dup = bool(row["date"] and amount and (row["date"], round(amount, 2)) in existing_signatures)
            preview_rows.append(PdfPreviewRow(
                row_number=i + 1, date=row["date"], description=row["description"],
                debit=row["debit"], credit=row["credit"], balance=row["balance"],
                confidence=row["confidence"], is_duplicate=is_dup,
            ))

        _PENDING_IMPORTS[imported_file.id] = {"parsed_rows": parsed_rows, "user_id": current_user.id}

        log_action(db, current_user.id, "import.pdf_upload", "imported_file", imported_file.id)

        return PdfPreviewResponse(
            imported_file_id=imported_file.id,
            is_scanned=scanned,
            extraction_method=extraction_method,
            preview_rows=preview_rows,
            total_rows=len(preview_rows),
            low_confidence_rows=sum(1 for r in preview_rows if r.confidence < 0.6),
        )
    finally:
        # Clean up the temporary uploaded file immediately after processing.
        if temp_path.exists():
            os.remove(temp_path)


@router.post("/pdf/confirm", response_model=ImportSummaryOut)
def confirm_pdf_import(
    imported_file_id: str,
    row_numbers_to_import: list[int],
    min_confidence: float = 0.6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cached = _PENDING_IMPORTS.get(imported_file_id)
    if not cached or cached["user_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending PDF import found.")

    parsed_rows = cached["parsed_rows"]
    batch = ImportBatch(user_id=current_user.id, imported_file_id=imported_file_id, total_rows=len(parsed_rows))
    db.add(batch)
    db.commit()
    db.refresh(batch)

    imported_count = invalid_count = 0
    for i, row in enumerate(parsed_rows):
        row_number = i + 1
        if row_number not in row_numbers_to_import:
            continue
        # Never silently import low-confidence rows even if requested.
        if row["confidence"] < min_confidence or not row["date"]:
            invalid_count += 1
            db.add(ImportError_(
                import_batch_id=batch.id, row_number=row_number,
                raw_row_json=json.dumps(row, default=str),
                error_reason=f"Confidence {row['confidence']} below required minimum {min_confidence}.",
            ))
            continue

        amount = row["debit"] or row["credit"]
        if not amount:
            invalid_count += 1
            continue

        txn = Transaction(
            user_id=current_user.id,
            date=row["date"],
            transaction_type="expense" if row["debit"] else "income",
            amount=amount,
            description=row["description"],
            source="pdf_import",
            import_batch_id=batch.id,
        )
        db.add(txn)
        imported_count += 1

    batch.imported_rows = imported_count
    batch.invalid_rows = invalid_count
    db.commit()
    del _PENDING_IMPORTS[imported_file_id]

    log_action(db, current_user.id, "import.pdf_confirm", "import_batch", batch.id)

    return ImportSummaryOut(
        import_batch_id=batch.id, total_rows=batch.total_rows,
        imported_rows=imported_count, skipped_duplicate_rows=0, invalid_rows=invalid_count,
    )
