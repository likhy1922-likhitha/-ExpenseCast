"""
ExpenseCast synthetic transaction data generator.

Generates realistic personal-finance transaction histories for a set of
fictional Indian users (students, salaried employees, freelancers) so the
LSTM forecasting pipeline has enough sequential data to train on before any
real user data exists.

Usage:
    python generate_sample_data.py
    python generate_sample_data.py --demo   # also (re)generate the demo-mode dataset

Output:
    machine-learning/data/generated/expensecast_transactions.csv
    machine-learning/data/generated/expensecast_demo_transactions.csv (with --demo)
"""

from __future__ import annotations

import argparse
import random
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = Path(__file__).parent / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MONTHS_OF_HISTORY = 19  # >= 18 months required
DAYS_OF_HISTORY = MONTHS_OF_HISTORY * 30

CURRENCY = "INR"

# ---------------------------------------------------------------------------
# Category / merchant tables
# ---------------------------------------------------------------------------

EXPENSE_CATEGORIES = {
    "Food": ["Swiggy", "Zomato", "Campus Canteen", "Domino's", "Local Cafe", "Tiffin Service"],
    "Groceries": ["BigBasket", "DMart", "Local Kirana Store", "Reliance Fresh", "Blinkit"],
    "Transport": ["Uber", "Ola", "Metro Card Recharge", "Local Bus Pass", "Petrol Pump", "IRCTC"],
    "Education": ["College Fee Office", "Udemy", "Coaching Institute", "Book Store", "Byju's"],
    "Rent": ["Landlord Transfer", "PG Rent"],
    "Hostel": ["Hostel Fee Office"],
    "Utilities": ["Electricity Board", "Water Board", "Broadband Provider", "Piped Gas"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Local Market"],
    "Healthcare": ["Apollo Pharmacy", "Local Clinic", "Diagnostics Lab", "Practo"],
    "Entertainment": ["BookMyShow", "PVR Cinemas", "Gaming Top-up", "Bowling Alley"],
    "Subscriptions": ["Netflix", "Spotify", "Hotstar", "Amazon Prime", "iCloud Storage"],
    "Travel": ["MakeMyTrip", "IRCTC", "RedBus", "Airbnb", "Fuel - Road Trip"],
    "Personal Care": ["Salon", "Cosmetics Store", "Gym Membership"],
    "Family": ["Family Transfer", "Gift Purchase"],
    "EMI": ["Bank EMI Debit", "NBFC EMI Debit"],
    "Insurance": ["LIC Premium", "Health Insurance Premium"],
}

INCOME_CATEGORIES = {
    "Salary": ["Employer Payroll"],
    "Scholarship": ["University Scholarship Office"],
    "Freelance Income": ["Upwork", "Fiverr", "Client Transfer"],
    "Investment": ["Dividend Credit", "Interest Credit"],
}

TRANSFER_CATEGORIES = {
    "Savings": ["Auto-Sweep Savings", "Recurring Deposit Debit"],
    "Investment": ["SIP - Mutual Fund", "Stock Purchase", "Gold ETF Purchase", "PPF Contribution"],
}

PAYMENT_METHODS = ["UPI", "Debit Card", "Credit Card", "Net Banking", "Cash", "Wallet"]

FESTIVAL_MONTHS = {10, 11}  # Oct/Nov - Diwali season spending bump


@dataclass
class UserProfile:
    user_id: str
    name_seed: str
    user_type: str  # student | salaried | freelancer
    monthly_income: float
    base_daily_spend: float
    accounts: list = field(default_factory=lambda: ["Primary Bank Account"])
    recurring: list = field(default_factory=list)  # list of (category, merchant, amount, day_of_month)
    start_balance: float = 15000.0


def build_user_profiles() -> list[UserProfile]:
    profiles = []

    students = [
        ("stu_ananya", "Ananya", 8000, 350),
        ("stu_rohit", "Rohit", 6000, 300),
        ("stu_priya", "Priya", 9000, 380),
    ]
    for uid, name, income, spend in students:
        p = UserProfile(user_id=uid, name_seed=name, user_type="student",
                         monthly_income=income, base_daily_spend=spend, start_balance=5000.0)
        p.recurring = [
            ("Hostel", "Hostel Fee Office", 7000, 5),
            ("Subscriptions", "Netflix", 199, 12),
            ("Subscriptions", "Spotify", 119, 15),
        ]
        profiles.append(p)

    salaried = [
        ("sal_arjun", "Arjun", 65000, 900),
        ("sal_kavya", "Kavya", 82000, 1100),
        ("sal_vikram", "Vikram", 55000, 800),
        ("sal_meera", "Meera", 95000, 1300),
    ]
    for uid, name, income, spend in salaried:
        p = UserProfile(user_id=uid, name_seed=name, user_type="salaried",
                         monthly_income=income, base_daily_spend=spend, start_balance=40000.0)
        p.recurring = [
            ("Rent", "Landlord Transfer", income * 0.28, 3),
            ("EMI", "Bank EMI Debit", income * 0.12, 7),
            ("Insurance", "LIC Premium", 2500, 10),
            ("Investment", "SIP - Mutual Fund", income * 0.10, 5),
            ("Subscriptions", "Amazon Prime", 299, 18),
            ("Subscriptions", "Hotstar", 149, 20),
            ("Utilities", "Electricity Board", 1800, 8),
            ("Utilities", "Broadband Provider", 999, 9),
        ]
        profiles.append(p)

    freelancers = [
        ("free_rahul", "Rahul", 45000, 700),
        ("free_sneha", "Sneha", 38000, 650),
        ("free_imran", "Imran", 52000, 750),
    ]
    for uid, name, income, spend in freelancers:
        p = UserProfile(user_id=uid, name_seed=name, user_type="freelancer",
                         monthly_income=income, base_daily_spend=spend, start_balance=25000.0)
        p.recurring = [
            ("Rent", "Landlord Transfer", income * 0.22, 4),
            ("Utilities", "Electricity Board", 1500, 8),
            ("Insurance", "Health Insurance Premium", 1800, 12),
            ("Investment", "Stock Purchase", income * 0.08, 15),
            ("Subscriptions", "Netflix", 199, 16),
        ]
        profiles.append(p)

    return profiles


def weighted_expense_category(user_type: str) -> str:
    if user_type == "student":
        weights = {
            "Food": 22, "Transport": 12, "Education": 10, "Shopping": 12,
            "Entertainment": 10, "Subscriptions": 5, "Groceries": 8,
            "Personal Care": 6, "Healthcare": 5, "Travel": 5, "Family": 5,
        }
    elif user_type == "salaried":
        weights = {
            "Food": 15, "Groceries": 14, "Transport": 10, "Shopping": 12,
            "Entertainment": 6, "Healthcare": 6, "Personal Care": 5,
            "Travel": 6, "Family": 8, "Utilities": 8, "Subscriptions": 3, "EMI": 7,
        }
    else:  # freelancer
        weights = {
            "Food": 16, "Groceries": 13, "Transport": 9, "Shopping": 11,
            "Entertainment": 7, "Healthcare": 6, "Personal Care": 5,
            "Travel": 7, "Family": 7, "Utilities": 7, "Subscriptions": 4, "Education": 8,
        }
    cats, w = zip(*weights.items())
    return random.choices(cats, weights=w, k=1)[0]


def make_transaction(user: UserProfile, dt: date, category: str, ttype: str,
                      amount: float, merchant: str, is_recurring: bool = False) -> dict:
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_type": user.user_type,
        "date": dt.isoformat(),
        "description": f"{merchant} payment",
        "merchant": merchant,
        "category": category,
        "transaction_type": ttype,  # income | expense | savings | investment
        "amount": round(amount, 2),
        "currency": "INR",
        "payment_method": random.choice(PAYMENT_METHODS),
        "account_name": random.choice(user.accounts),
        "is_recurring": is_recurring,
        "balance": None,  # filled in after chronological pass
    }


def generate_for_user(user: UserProfile, start: date, end: date) -> list[dict]:
    rows: list[dict] = []
    day = start
    while day <= end:
        # --- Salary / scholarship / freelance income ---
        if user.user_type in ("salaried",) and day.day == 1:
            rows.append(make_transaction(user, day, "Salary", "income",
                                          user.monthly_income * random.uniform(0.97, 1.05),
                                          "Employer Payroll", is_recurring=True))
        if user.user_type == "student" and day.day == 2:
            rows.append(make_transaction(user, day, "Scholarship", "income",
                                          user.monthly_income * random.uniform(0.9, 1.1),
                                          "University Scholarship Office", is_recurring=True))
        if user.user_type == "freelancer" and day.day in (5, 20):
            rows.append(make_transaction(user, day, "Freelance Income", "income",
                                          user.monthly_income * random.uniform(0.35, 0.65),
                                          random.choice(INCOME_CATEGORIES["Freelance Income"])))

        # --- Recurring fixed payments ---
        for cat, merchant, amount, dom in user.recurring:
            if day.day == dom:
                ttype = "investment" if cat == "Investment" else (
                    "savings" if cat == "Savings" else "expense")
                jitter = amount * random.uniform(0.98, 1.02)
                rows.append(make_transaction(user, day, cat, ttype, jitter, merchant, is_recurring=True))

        # --- Everyday variable spending ---
        n_txns_today = np.random.poisson(1.6)
        weekend_boost = 1.35 if day.weekday() >= 5 else 1.0
        festival_boost = 1.6 if day.month in FESTIVAL_MONTHS else 1.0
        for _ in range(n_txns_today):
            category = weighted_expense_category(user.user_type)
            merchant = random.choice(EXPENSE_CATEGORIES.get(category, ["General Store"]))
            base = user.base_daily_spend * random.uniform(0.08, 0.55)
            amount = base * weekend_boost * festival_boost
            rows.append(make_transaction(user, day, category, "expense", amount, merchant))

        # --- Occasional unexpected large expense ---
        if random.random() < 0.015:
            category = random.choice(["Healthcare", "Shopping", "Travel"])
            merchant = random.choice(EXPENSE_CATEGORIES[category])
            amount = user.base_daily_spend * random.uniform(4, 9)
            rows.append(make_transaction(user, day, category, "expense", amount, merchant))

        day += timedelta(days=1)

    return rows


def compute_running_balance(rows: list[dict], start_balance: float) -> list[dict]:
    rows_sorted = sorted(rows, key=lambda r: r["date"])
    balance = start_balance
    for r in rows_sorted:
        if r["transaction_type"] == "income":
            balance += r["amount"]
        else:
            balance -= r["amount"]
        r["balance"] = round(balance, 2)
    return rows_sorted


def generate_dataset(n_extra_random_users: int = 3) -> pd.DataFrame:
    profiles = build_user_profiles()

    end_date = date.today()
    start_date = end_date - timedelta(days=DAYS_OF_HISTORY)

    all_rows: list[dict] = []
    for user in profiles:
        user_rows = generate_for_user(user, start_date, end_date)
        user_rows = compute_running_balance(user_rows, user.start_balance)
        all_rows.extend(user_rows)

    df = pd.DataFrame(all_rows)
    df = df.sort_values(["user_id", "date"]).reset_index(drop=True)
    return df


def generate_demo_dataset() -> pd.DataFrame:
    """A single, richly-populated fictional demo user, isolated from the
    training population, used only for the app's 'Try Demo' mode."""
    demo_user = UserProfile(
        user_id="demo_user_001",
        name_seed="Demo",
        user_type="salaried",
        monthly_income=72000,
        base_daily_spend=950,
        start_balance=48000.0,
    )
    demo_user.recurring = [
        ("Rent", "Landlord Transfer", 20000, 3),
        ("EMI", "Bank EMI Debit", 8500, 7),
        ("Insurance", "LIC Premium", 2200, 10),
        ("Investment", "SIP - Mutual Fund", 7000, 5),
        ("Subscriptions", "Amazon Prime", 299, 18),
        ("Subscriptions", "Netflix", 199, 20),
        ("Utilities", "Electricity Board", 1900, 8),
        ("Utilities", "Broadband Provider", 999, 9),
    ]
    end_date = date.today()
    start_date = end_date - timedelta(days=DAYS_OF_HISTORY)
    rows = generate_for_user(demo_user, start_date, end_date)
    rows = compute_running_balance(rows, demo_user.start_balance)
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="also generate the demo-mode dataset")
    args = parser.parse_args()

    df = generate_dataset()
    out_path = OUTPUT_DIR / "expensecast_transactions.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df):,} transactions for {df['user_id'].nunique()} users -> {out_path}")
    print(df["user_id"].value_counts())

    if args.demo:
        demo_df = generate_demo_dataset()
        demo_path = OUTPUT_DIR / "expensecast_demo_transactions.csv"
        demo_df.to_csv(demo_path, index=False)
        print(f"Generated {len(demo_df):,} demo transactions -> {demo_path}")


if __name__ == "__main__":
    main()
