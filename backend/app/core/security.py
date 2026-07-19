"""Validate Supabase access tokens issued with legacy or modern signing keys."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


@dataclass
class AuthenticatedUser:
    id: str
    email: str | None
    is_demo: bool = False


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
    )


def _supabase_issuer() -> str:
    base_url = settings.SUPABASE_URL.strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("SUPABASE_URL is not configured correctly.")
    return f"{base_url}/auth/v1"


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    response = httpx.get(
        f"{_supabase_issuer()}/.well-known/jwks.json",
        timeout=10.0,
    )
    response.raise_for_status()
    jwks = response.json()
    if not isinstance(jwks.get("keys"), list):
        raise ValueError("Supabase returned an invalid JWKS response.")
    return jwks


def _find_signing_key(key_id: str) -> dict:
    key = next((item for item in _get_jwks()["keys"] if item.get("kid") == key_id), None)
    if key is not None:
        return key

    # Refresh once to handle a recent Supabase signing-key rotation.
    _get_jwks.cache_clear()
    key = next((item for item in _get_jwks()["keys"] if item.get("kid") == key_id), None)
    if key is None:
        raise ValueError("No matching Supabase signing key was found.")
    return key


def decode_supabase_jwt(token: str) -> AuthenticatedUser:
    """Verify a Supabase JWT and return the authenticated user's identity.

    Legacy projects use HS256 and the configured legacy JWT secret. New
    projects normally use ES256 or RS256 and publish their verification keys
    through Supabase's JWKS endpoint.
    """

    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        issuer = _supabase_issuer()

        if algorithm == "HS256":
            if not settings.SUPABASE_JWT_SECRET:
                raise ValueError("SUPABASE_JWT_SECRET is missing.")
            verification_key: str | dict = settings.SUPABASE_JWT_SECRET
        elif algorithm in {"ES256", "RS256"}:
            key_id = header.get("kid")
            if not key_id:
                raise ValueError("Token header is missing its key id.")
            verification_key = _find_signing_key(key_id)
        else:
            raise ValueError("Unsupported JWT signing algorithm.")

        payload = jwt.decode(
            token,
            verification_key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=issuer,
        )
    except (JWTError, httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise _unauthorized() from exc

    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized()

    return AuthenticatedUser(id=user_id, email=payload.get("email"))