"""Authentication utilities for AWS Cognito JWT validation."""
import logging
import time
import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)

# JWKS cache
_jwks_cache: Optional[dict] = None
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


async def get_jwks() -> dict:
    """Fetch and cache Cognito JWKS."""
    global _jwks_cache, _jwks_cache_time

    if _jwks_cache and (time.time() - _jwks_cache_time) < JWKS_CACHE_TTL:
        return _jwks_cache

    if not settings.COGNITO_USER_POOL_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured"
        )

    jwks_url = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = time.time()
        return _jwks_cache


async def verify_token(token: str) -> dict:
    """Verify a Cognito JWT token and return claims."""
    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key = k
                break

        if not key:
            raise JWTError("Key not found in JWKS")

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}",
        )

        # Validate token_use claim
        if claims.get("token_use") != "access":
            raise JWTError("Invalid token type")

        return claims

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    # E2E test mode bypass
    if settings.E2E_TEST_MODE and credentials:
        token = credentials.credentials
        if token.startswith("e2e-test:"):
            cognito_sub = token.replace("e2e-test:", "")
            user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
            if not user:
                user = User(
                    cognito_sub=cognito_sub,
                    email=f"{cognito_sub}@e2e-test.local",
                    display_name="E2E Test User",
                    role="member",
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            return user

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    claims = await verify_token(credentials.credentials)
    cognito_sub = claims.get("sub")
    email = claims.get("email", claims.get("username", ""))

    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )

    # Use upsert to handle race conditions
    stmt = insert(User).values(
        cognito_sub=cognito_sub,
        email=email,
        display_name=email.split("@")[0] if email else "User",
        role="member"
    ).on_conflict_do_nothing(index_elements=['cognito_sub'])
    db.execute(stmt)
    db.commit()

    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()

    # Sync email if changed in Cognito
    if user and user.email != email and email:
        user.email = email
        db.commit()

    return user


def check_ownership(resource, user: User) -> bool:
    """Check if user owns or has access to a resource."""
    if hasattr(resource, 'user_id') and resource.user_id == user.id:
        return True
    if hasattr(resource, 'organization_id') and user.organization_id:
        if resource.organization_id == user.organization_id:
            return True
    return False
