from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.investment_models import CategoryRule
from app.models.user_models import Category
from app.services.categorization import DEFAULT_KEYWORD_RULES

DEFAULT_EXPENSE_CATEGORIES = [
    "Food", "Groceries", "Transport", "Education", "Rent", "Hostel", "Utilities",
    "Shopping", "Healthcare", "Entertainment", "Subscriptions", "Travel",
    "Personal Care", "Family", "EMI", "Insurance",
]
DEFAULT_TRANSFER_CATEGORIES = ["Investment", "Savings"]
DEFAULT_INCOME_CATEGORIES = ["Salary", "Scholarship", "Freelance Income"]
DEFAULT_OTHER_CATEGORIES = ["Other"]

CATEGORY_ICON_MAP = {
    "Food": "utensils", "Groceries": "shopping-basket", "Transport": "bus", "Education": "graduation-cap",
    "Rent": "home", "Hostel": "building-2", "Utilities": "plug", "Shopping": "shopping-bag",
    "Healthcare": "heart-pulse", "Entertainment": "clapperboard", "Subscriptions": "repeat",
    "Travel": "plane", "Personal Care": "sparkles", "Family": "users", "EMI": "credit-card",
    "Insurance": "shield", "Investment": "trending-up", "Savings": "piggy-bank",
    "Salary": "briefcase", "Scholarship": "award", "Freelance Income": "laptop", "Other": "circle-dot",
}


def seed_default_categories(db: Session) -> dict[str, str]:
    """Idempotent: creates global (user_id=NULL) default categories if
    they don't already exist. Returns a name -> id map."""
    name_to_id: dict[str, str] = {}

    all_defaults = [
        (name, "expense") for name in DEFAULT_EXPENSE_CATEGORIES
    ] + [
        (name, "transfer") for name in DEFAULT_TRANSFER_CATEGORIES
    ] + [
        (name, "income") for name in DEFAULT_INCOME_CATEGORIES
    ] + [
        (name, "expense") for name in DEFAULT_OTHER_CATEGORIES
    ]

    for name, category_type in all_defaults:
        existing = db.query(Category).filter(Category.user_id.is_(None), Category.name == name).first()
        if existing:
            name_to_id[name] = existing.id
            continue
        cat = Category(
            user_id=None, name=name, category_type=category_type,
            icon=CATEGORY_ICON_MAP.get(name, "circle"), is_default=True,
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)
        name_to_id[name] = cat.id

    return name_to_id


def seed_default_category_rules(db: Session) -> None:
    """Idempotent: creates the global keyword -> category rules from
    DEFAULT_KEYWORD_RULES, used by the automatic categorization engine."""
    name_to_id = seed_default_categories(db)

    for keyword, category_name in DEFAULT_KEYWORD_RULES.items():
        category_id = name_to_id.get(category_name)
        if not category_id:
            continue
        existing = db.query(CategoryRule).filter(
            CategoryRule.user_id.is_(None), CategoryRule.keyword == keyword,
        ).first()
        if existing:
            continue
        db.add(CategoryRule(
            user_id=None, keyword=keyword, category_id=category_id,
            match_field="merchant", priority=0, source="system",
        ))
    db.commit()
