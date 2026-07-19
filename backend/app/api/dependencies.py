from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import AuthenticatedUser, decode_supabase_jwt
from app.database.session import get_db
from app.models.user_models import User

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates the Supabase-issued bearer token, then ensures a matching row
    exists in our local `users` table (creating a lightweight one on first
    sight so foreign keys always resolve). This is the single dependency
    every protected route relies on for user-data isolation: every query a
    route makes is filtered by `current_user.id`, which guarantees a user
    can only ever see or modify their own records.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token.")

    auth_user: AuthenticatedUser = decode_supabase_jwt(credentials.credentials)

    db_user = db.get(User, auth_user.id)
    if db_user is None:
        db_user = User(
            id=auth_user.id,
            email=auth_user.email or f"{auth_user.id}@unknown.local",
            full_name="",
            is_demo_user=(auth_user.id == settings.DEMO_USER_ID),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    if not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    return db_user


def get_current_demo_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Used by routes that must only ever be reachable in Demo Mode."""
    if not settings.ENABLE_DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo Mode is disabled.")
    if not current_user.is_demo_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This endpoint is Demo Mode only.")
    return current_user
