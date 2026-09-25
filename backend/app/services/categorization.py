from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.investment_models import CategoryRule
from app.models.user_models import Category

# Default global keyword -> category rules, seeded once at startup (see
# app/seed/seed_defaults.py). This is intentionally rule-based, not ML --
# the LSTM in this project is used exclusively for expense forecasting.
DEFAULT_KEYWORD_RULES: dict[str, str] = {
    "swiggy": "Food", "zomato": "Food", "restaurant": "Food", "cafe": "Food", "canteen": "Food",
    "dominos": "Food", "pizza": "Food",
    "bigbasket": "Groceries", "dmart": "Groceries", "kirana": "Groceries", "reliance fresh": "Groceries",
    "blinkit": "Groceries",
    "uber": "Transport", "ola": "Transport", "metro": "Transport", "railway": "Transport", "bus": "Transport",
    "irctc": "Transport", "petrol": "Transport", "fuel": "Transport",
    "amazon": "Shopping", "flipkart": "Shopping", "myntra": "Shopping",
    "netflix": "Subscriptions", "spotify": "Subscriptions", "hotstar": "Subscriptions", "prime": "Subscriptions",
    "college": "Education", "exam": "Education", "course": "Education", "tuition": "Education", "udemy": "Education",
    "byju": "Education",
    "salary": "Salary", "payroll": "Salary", "stipend": "Salary", "scholarship": "Scholarship",
    "sip": "Investment", "mutual fund": "Investment", "stock": "Investment", "gold etf": "Investment", "ppf": "Investment",
    "landlord": "Rent", "hostel": "Hostel",
    "electricity": "Utilities", "water board": "Utilities", "broadband": "Utilities", "piped gas": "Utilities",
    "pharmacy": "Healthcare", "clinic": "Healthcare", "diagnostics": "Healthcare", "practo": "Healthcare",
    "bookmyshow": "Entertainment", "pvr": "Entertainment", "gaming": "Entertainment",
    "makemytrip": "Travel", "redbus": "Travel", "airbnb": "Travel",
    "salon": "Personal Care", "gym": "Personal Care",
    "lic": "Insurance", "insurance premium": "Insurance",
    "emi": "EMI",
}


def suggest_category_id(db: Session, user_id: str, merchant: str | None, description: str | None) -> str | None:
    """
    Suggests a category for a new transaction using, in priority order:
      1. The user's own saved correction rules (highest priority -- they
         explicitly told the app "this merchant belongs in this category").
      2. Global default keyword rules.
    Returns a Category.id or None if nothing matches (falls back to "Other").
    """
    haystack = f"{merchant or ''} {description or ''}".lower()
    if not haystack.strip():
        return None

    user_rules = (
        db.query(CategoryRule)
        .filter(CategoryRule.user_id == user_id, CategoryRule.source == "user_correction")
        .order_by(CategoryRule.priority.desc())
        .all()
    )
    for rule in user_rules:
        if rule.keyword.lower() in haystack:
            return rule.category_id

    global_rules = (
        db.query(CategoryRule)
        .filter(CategoryRule.user_id.is_(None), CategoryRule.source == "system")
        .all()
    )
    for rule in global_rules:
        if rule.keyword.lower() in haystack:
            return rule.category_id

    return None


def save_user_correction(db: Session, user_id: str, keyword: str, category_id: str) -> CategoryRule:
    """Called when a user manually re-categorizes a transaction; the
    correction is saved so future transactions from that merchant are
    categorized correctly automatically."""
    existing = (
        db.query(CategoryRule)
        .filter(
            CategoryRule.user_id == user_id,
            CategoryRule.keyword == keyword.lower(),
            CategoryRule.source == "user_correction",
        )
        .first()
    )
    if existing:
        existing.category_id = category_id
        db.commit()
        db.refresh(existing)
        return existing

    rule = CategoryRule(
        user_id=user_id,
        keyword=keyword.lower(),
        category_id=category_id,
        match_field="merchant",
        priority=10,
        source="user_correction",
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
