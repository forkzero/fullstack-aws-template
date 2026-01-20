"""User API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import User
from app.schemas.user import UserResponse, OrganizationResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return user


@router.get("/me/organization", response_model=OrganizationResponse)
async def get_user_organization(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization."""
    if not user.organization:
        return {"id": None, "name": None}
    return user.organization
