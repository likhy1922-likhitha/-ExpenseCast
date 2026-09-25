from __future__ import annotations

from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Imports ---

class ColumnMapping(BaseModel):
    date_column: str
    description_column: Optional[str] = None
    merchant_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    amount_column: Optional[str] = None
    balance_column: Optional[str] = None


class CsvPreviewRow(BaseModel):
    row_number: int
    raw: dict
    parsed_date: Optional[str] = None
    parsed_amount: Optional[float] = None
    parsed_type: Optional[Literal["income", "expense"]] = None
    suggested_category: Optional[str] = None
    is_duplicate: bool = False
    is_valid: bool = True
    validation_message: Optional[str] = None


class CsvPreviewResponse(BaseModel):
    imported_file_id: str
    detected_encoding: str
    detected_delimiter: str
    detected_columns: list[str]
    suggested_mapping: ColumnMapping
    preview_rows: list[CsvPreviewRow]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int


class ConfirmImportRequest(BaseModel):
    imported_file_id: str
    mapping: ColumnMapping
    row_numbers_to_import: list[int]  # allows excluding specific rows (e.g. flagged duplicates)


class ImportSummaryOut(BaseModel):
    import_batch_id: str
    total_rows: int
    imported_rows: int
    skipped_duplicate_rows: int
    invalid_rows: int


class PdfPreviewRow(BaseModel):
    row_number: int
    date: Optional[str] = None
    description: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: Optional[float] = None
    confidence: float
    is_duplicate: bool = False


class PdfPreviewResponse(BaseModel):
    imported_file_id: str
    is_scanned: bool
    extraction_method: str
    preview_rows: list[PdfPreviewRow]
    total_rows: int
    low_confidence_rows: int


# --- Forecasts ---

class ForecastOut(BaseModel):
    confidence_level: Literal["insufficient_data", "low_confidence", "personalized"]
    history_days_available: int
    predicted_next_1_day: Optional[float] = None
    predicted_next_7_days: Optional[float] = None
    predicted_next_30_days: Optional[float] = None
    predicted_next_90_days: Optional[float] = None
    predicted_end_of_month_expense: Optional[float] = None
    predicted_end_of_month_balance: Optional[float] = None
    overspending_risk: Optional[Literal["low", "medium", "high"]] = None
    generated_at: datetime
    is_estimate_disclaimer: str = "This forecast is a statistical estimate, not financial advice."


class ModelStatusOut(BaseModel):
    model_available: bool
    lookback_days: Optional[int] = None
    horizon_days: Optional[int] = None
    trained_at: Optional[str] = None
    test_mae: Optional[float] = None
    test_rmse: Optional[float] = None
    test_mape: Optional[float] = None
