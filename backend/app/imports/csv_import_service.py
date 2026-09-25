from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Optional

import chardet
import pandas as pd
from sqlalchemy.orm import Session

from app.models.finance_models import Transaction
from app.schemas.schemas_import_forecast import ColumnMapping, CsvPreviewRow
from app.services.categorization import DEFAULT_KEYWORD_RULES

# Column-name synonyms this importer recognises out of the box.
KNOWN_DATE_HEADERS = ["date", "transaction date", "value date", "txn date", "posting date"]
KNOWN_DESCRIPTION_HEADERS = ["description", "narration", "particulars", "details", "remarks"]
KNOWN_MERCHANT_HEADERS = ["merchant", "payee", "beneficiary"]
KNOWN_DEBIT_HEADERS = ["debit", "withdrawal", "withdrawal amt", "debit amount"]
KNOWN_CREDIT_HEADERS = ["credit", "deposit", "deposit amt", "credit amount"]
KNOWN_AMOUNT_HEADERS = ["amount", "transaction amount", "amt"]
KNOWN_BALANCE_HEADERS = ["balance", "closing balance", "running balance"]

DATE_FORMATS = [
    "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y",
    "%Y/%m/%d", "%b %d, %Y", "%d-%b-%Y", "%d-%b-%y",
]


def detect_encoding(raw_bytes: bytes) -> str:
    result = chardet.detect(raw_bytes)
    return result.get("encoding") or "utf-8"


def detect_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def _match_header(headers: list[str], candidates: list[str], exclude: set[str] | None = None) -> Optional[str]:
    exclude = exclude or set()
    lower_map = {h.lower().strip(): h for h in headers if h not in exclude}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    # fallback: partial match
    for h_lower, h_orig in lower_map.items():
        for cand in candidates:
            if cand in h_lower:
                return h_orig
    return None


def suggest_column_mapping(headers: list[str]) -> ColumnMapping:
    date_col = _match_header(headers, KNOWN_DATE_HEADERS) or headers[0]
    description_col = _match_header(headers, KNOWN_DESCRIPTION_HEADERS)
    merchant_col = _match_header(headers, KNOWN_MERCHANT_HEADERS)
    # Debit/credit-style statements (separate withdrawal/deposit columns)
    # are matched first, since headers like "Withdrawal Amt" would
    # otherwise false-positive-match the generic "amt" keyword used for
    # single-amount-column statements.
    debit_col = _match_header(headers, KNOWN_DEBIT_HEADERS)
    credit_col = _match_header(headers, KNOWN_CREDIT_HEADERS)
    used = {c for c in (date_col, description_col, merchant_col, debit_col, credit_col) if c}
    amount_col = None
    if not debit_col and not credit_col:
        amount_col = _match_header(headers, KNOWN_AMOUNT_HEADERS, exclude=used)
    balance_col = _match_header(headers, KNOWN_BALANCE_HEADERS, exclude=used)

    return ColumnMapping(
        date_column=date_col,
        description_column=description_col,
        merchant_column=merchant_col,
        debit_column=debit_col,
        credit_column=credit_col,
        amount_column=amount_col,
        balance_column=balance_col,
    )


def parse_date_flexible(raw: str) -> Optional[str]:
    raw = str(raw).strip()
    if not raw:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    # last resort: let pandas try
    try:
        return pd.to_datetime(raw, errors="raise").date().isoformat()
    except Exception:
        return None


def suggest_category_name(description: str, merchant: str) -> Optional[str]:
    haystack = f"{merchant} {description}".lower()
    for keyword, category in DEFAULT_KEYWORD_RULES.items():
        if keyword in haystack:
            return category
    return None


def build_preview_rows(
    df: pd.DataFrame,
    mapping: ColumnMapping,
    existing_txns: list[Transaction],
    max_preview_rows: int = 200,
) -> list[CsvPreviewRow]:
    rows: list[CsvPreviewRow] = []

    existing_signatures = {
        (t.date.isoformat(), round(float(t.amount), 2), (t.merchant or "").lower())
        for t in existing_txns
    }

    for idx, raw_row in df.iterrows():
        row_dict = raw_row.to_dict()
        parsed_date = parse_date_flexible(row_dict.get(mapping.date_column, ""))

        parsed_amount = None
        parsed_type = None
        if mapping.amount_column and mapping.amount_column in row_dict:
            raw_val = str(row_dict[mapping.amount_column]).replace(",", "").strip()
            if raw_val and raw_val.lower() != "nan":
                try:
                    val = float(raw_val)
                    parsed_amount = abs(val)
                    parsed_type = "income" if val >= 0 else "expense"
                except (ValueError, TypeError):
                    pass
        else:
            debit_val = None
            credit_val = None
            if mapping.debit_column and mapping.debit_column in row_dict:
                raw_val = str(row_dict[mapping.debit_column]).replace(",", "").strip()
                if raw_val and raw_val.lower() != "nan":
                    try:
                        debit_val = float(raw_val)
                    except (ValueError, TypeError):
                        debit_val = None
            if mapping.credit_column and mapping.credit_column in row_dict:
                raw_val = str(row_dict[mapping.credit_column]).replace(",", "").strip()
                if raw_val and raw_val.lower() != "nan":
                    try:
                        credit_val = float(raw_val)
                    except (ValueError, TypeError):
                        credit_val = None
            if credit_val:
                parsed_amount, parsed_type = credit_val, "income"
            elif debit_val:
                parsed_amount, parsed_type = debit_val, "expense"

        description = str(row_dict.get(mapping.description_column, "") or "") if mapping.description_column else ""
        merchant = str(row_dict.get(mapping.merchant_column, "") or "") if mapping.merchant_column else description[:100]
        suggested_category = suggest_category_name(description, merchant)

        is_valid = True
        message = None
        if not parsed_date:
            is_valid, message = False, "Could not parse a valid date for this row."
        elif parsed_amount is None or parsed_amount <= 0:
            is_valid, message = False, "Could not determine a valid transaction amount for this row."

        is_duplicate = False
        if is_valid:
            sig = (parsed_date, round(parsed_amount, 2), merchant.lower())
            is_duplicate = sig in existing_signatures

        rows.append(CsvPreviewRow(
            row_number=int(idx) + 1,
            raw={k: ("" if pd.isna(v) else str(v)) for k, v in row_dict.items()},
            parsed_date=parsed_date,
            parsed_amount=parsed_amount,
            parsed_type=parsed_type,
            suggested_category=suggested_category,
            is_duplicate=is_duplicate,
            is_valid=is_valid,
            validation_message=message,
        ))
        if len(rows) >= max_preview_rows:
            break

    return rows
