from __future__ import annotations

import re
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber

from app.imports.csv_import_service import parse_date_flexible

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[-/\s][A-Za-z]{3,9}[-/\s]\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
)
AMOUNT_PATTERN = re.compile(r"[-+]?₹?\s?[\d,]+\.\d{2}")


def is_scanned_pdf(file_path: str) -> bool:
    """A PDF is treated as scanned (image-only) if PyMuPDF extracts
    essentially no selectable text from its pages."""
    doc = fitz.open(file_path)
    total_text_len = 0
    for page in doc:
        total_text_len += len(page.get_text().strip())
    doc.close()
    return total_text_len < 50  # heuristic: near-empty extraction means it's scanned


def extract_text_pymupdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def extract_lines_pdfplumber(file_path: str) -> list[str]:
    lines: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.split("\n"))
    return lines


def _parse_amount(token: str) -> Optional[float]:
    cleaned = token.replace("₹", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_transaction_lines(lines: list[str]) -> list[dict]:
    """
    Heuristically identifies transaction rows in extracted bank/UPI-app
    statement text. Real statement layouts vary a lot (this is genuinely
    the hardest part of PDF import), so every row gets an explicit
    confidence score instead of being silently trusted.
    """
    results = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        date_match = DATE_PATTERN.search(line)
        amounts = AMOUNT_PATTERN.findall(line)

        if not date_match or not amounts:
            continue  # not a transaction row

        parsed_date = parse_date_flexible(date_match.group(0))
        amount_values = [_parse_amount(a) for a in amounts]
        amount_values = [a for a in amount_values if a is not None]
        if not amount_values:
            continue

        description = line
        for a in amounts:
            description = description.replace(a, "")
        description = description.replace(date_match.group(0), "").strip(" -|\t")

        # Confidence scoring: higher when we clearly have exactly a date,
        # a description, and 1-2 amount-like tokens (debit/credit/balance);
        # lower when the line is ambiguous (too many numbers, no clear
        # description, etc).
        confidence = 0.9
        if len(amount_values) > 3:
            confidence -= 0.3
        if not description:
            confidence -= 0.2
        if len(description) < 3:
            confidence -= 0.2
        confidence = max(0.1, min(0.95, confidence))

        debit = credit = balance = None
        if len(amount_values) == 1:
            debit = amount_values[0]
        elif len(amount_values) == 2:
            debit, balance = amount_values
        elif len(amount_values) >= 3:
            debit, credit, balance = amount_values[0], amount_values[1], amount_values[2]

        results.append({
            "date": parsed_date,
            "description": description or None,
            "debit": debit,
            "credit": credit,
            "balance": balance,
            "confidence": round(confidence, 2),
        })

    return results
