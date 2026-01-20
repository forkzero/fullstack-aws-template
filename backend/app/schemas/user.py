"""User schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class OrganizationResponse(BaseModel):
    """Organization response schema."""
    id: Optional[UUID] = None
    name: Optional[str] = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """User response schema."""
    id: UUID
    email: str
    display_name: Optional[str] = None
    role: str
    organization_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
