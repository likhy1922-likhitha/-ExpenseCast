from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.investment_models import CategoryRule
from app.models.user_models import Category, User
from app.schemas.schemas_budget import CategoryCreate, CategoryOut
from app.services.audit import log_action
from app.services.categorization import save_user_correction

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns global default categories plus this user's custom ones."""
    cats = (
        db.query(Category)
        .filter((Category.user_id.is_(None)) | (Category.user_id == current_user.id))
        .order_by(Category.is_default.desc(), Category.name.asc())
        .all()
    )
    return cats


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Category).filter(Category.user_id == current_user.id, Category.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists.")
    cat = Category(
        user_id=current_user.id,
        name=payload.name,
        category_type=payload.category_type,
        icon=payload.icon,
        color=payload.color,
        is_default=False,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    log_action(db, current_user.id, "category.create", "category", cat.id)
    return cat


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: str,
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found or not editable.")
    cat.name = payload.name
    cat.category_type = payload.category_type
    cat.icon = payload.icon
    cat.color = payload.color
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found or not editable.")
    db.delete(cat)
    db.commit()
    log_action(db, current_user.id, "category.delete", "category", category_id)
    return None


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_categorization_rule(
    keyword: str,
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(
        Category.id == category_id,
        (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
    ).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    rule = save_user_correction(db, current_user.id, keyword, category_id)
    log_action(db, current_user.id, "category_rule.create", "category_rule", rule.id)
    return {"id": rule.id, "keyword": rule.keyword, "category_id": rule.category_id}
