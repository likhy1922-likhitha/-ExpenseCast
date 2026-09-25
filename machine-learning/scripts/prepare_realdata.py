"""
Normalizes the two real Kaggle datasets the user supplied into ExpenseCast's
canonical transaction schema. Kept SEPARATE from the synthetic training
population and used purely as a real-data validation/holdout set for the
LSTM (per user's explicit choice).

Inputs (already copied into machine-learning/data/realdata/):
    Personal_Finance_Dataset.csv   (by "ramya" on Kaggle)
        Date, Transaction Description, Category, Amount, Type
    Expenses_clean.csv / Income_clean.csv
        date_time, category, amount, currency, account, tags

Output:
    machine-learning/data/realdata/realdata_normalized.csv
"""

from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "realdata"

CANONICAL_COLUMNS = [
    "transaction_id", "user_id", "user_type", "date", "description",
    "merchant", "category", "transaction_type", "amount", "currency",
    "payment_method", "account_name", "is_recurring", "balance",
]

# Category harmonization so the real data's category vocabulary lines up
# reasonably with ExpenseCast's default category list.
CATEGORY_MAP = {
    "Food & Drink": "Food", "Food": "Food", "Cafe": "Food", "Restaurant": "Food",
    "Groceries": "Groceries", "Grocery": "Groceries",
    "Transport": "Transport", "Public transport": "Transport", "Transportation": "Transport",
    "Utilities": "Utilities", "Rent": "Rent", "Housing": "Rent",
    "Shopping": "Shopping", "Entertainment": "Entertainment", "Travel": "Travel",
    "Health": "Healthcare", "Healthcare": "Healthcare", "Medical": "Healthcare",
    "Education": "Education", "Subscriptions": "Subscriptions", "Subscription": "Subscriptions",
    "Investment": "Investment", "Investments": "Investment",
    "Savings": "Savings", "Insurance": "Insurance", "Family": "Family",
    "Job": "Salary", "Salary": "Salary", "Freelance": "Freelance Income",
    "Personal Care": "Personal Care", "Gift": "Family",
}


def harmonize_category(raw: str) -> str:
    if not isinstance(raw, str):
        return "Other"
    return CATEGORY_MAP.get(raw.strip(), raw.strip().title() if raw.strip() else "Other")


def normalize_ramya_dataset() -> pd.DataFrame:
    path = DATA_DIR / "Personal_Finance_Dataset.csv"
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    out = pd.DataFrame()
    out["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    out["user_id"] = "real_ramya_user"
    out["user_type"] = "real_data"
    out["date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date.astype(str)
    out["description"] = df["Transaction Description"].fillna("")
    out["merchant"] = df["Transaction Description"].fillna("Unknown").str.split().str[0]
    out["category"] = df["Category"].apply(harmonize_category)
    out["transaction_type"] = df["Type"].str.lower().map(
        {"income": "income", "expense": "expense"}
    ).fillna("expense")
    out["amount"] = pd.to_numeric(df["Amount"], errors="coerce").abs()
    out["currency"] = "INR"
    out["payment_method"] = "Unknown"
    out["account_name"] = "Primary Account"
    out["is_recurring"] = False
    out["balance"] = np.nan
    return out


def normalize_expenses_income() -> pd.DataFrame:
    exp = pd.read_csv(DATA_DIR / "Expenses_clean.csv")
    inc = pd.read_csv(DATA_DIR / "Income_clean.csv")

    exp = exp.copy()
    exp["transaction_type"] = "expense"
    inc = inc.copy()
    inc["transaction_type"] = "income"

    combined = pd.concat([exp, inc], ignore_index=True)
    combined.columns = [c.strip() for c in combined.columns]

    out = pd.DataFrame()
    out["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(combined))]
    out["user_id"] = "real_belarus_user"
    out["user_type"] = "real_data"
    out["date"] = pd.to_datetime(combined["date_time"], errors="coerce").dt.date.astype(str)
    out["description"] = combined["category"].astype(str) + " - " + combined["tags"].astype(str)
    out["merchant"] = combined["category"].astype(str)
    out["category"] = combined["category"].apply(harmonize_category)
    out["transaction_type"] = combined["transaction_type"]
    out["amount"] = pd.to_numeric(combined["amount"], errors="coerce").abs()
    out["currency"] = combined["currency"].fillna("BYN")
    out["payment_method"] = "Unknown"
    out["account_name"] = combined["account"].fillna("acct_1")
    out["is_recurring"] = False
    out["balance"] = np.nan
    return out


def compute_running_balance(df: pd.DataFrame) -> pd.DataFrame:
    out_frames = []
    for user_id, group in df.groupby("user_id"):
        group = group.sort_values("date").copy()
        balance = 0.0
        balances = []
        for _, row in group.iterrows():
            if row["transaction_type"] == "income":
                balance += row["amount"]
            else:
                balance -= row["amount"]
            balances.append(round(balance, 2))
        group["balance"] = balances
        out_frames.append(group)
    return pd.concat(out_frames, ignore_index=True)


def main():
    ramya = normalize_ramya_dataset()
    combo = normalize_expenses_income()

    merged = pd.concat([ramya, combo], ignore_index=True)
    merged = merged.dropna(subset=["date", "amount"])
    merged = merged[merged["amount"] > 0]
    merged = compute_running_balance(merged)
    merged = merged[CANONICAL_COLUMNS]
    merged = merged.sort_values(["user_id", "date"]).reset_index(drop=True)

    out_path = DATA_DIR / "realdata_normalized.csv"
    merged.to_csv(out_path, index=False)
    print(f"Normalized {len(merged):,} real transactions -> {out_path}")
    print(merged.groupby("user_id").agg(
        rows=("transaction_id", "count"),
        first_date=("date", "min"),
        last_date=("date", "max"),
        currency=("currency", "first"),
    ))


if __name__ == "__main__":
    main()
