from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = "user"


class UserCreate(UserBase):
    id: UUID  # Supplied by Supabase Auth


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    """
    Core user fields.
    Subscription & billing data is populated by the endpoint
    via joins to the subscriptions and billing_accounts tables
    so the frontend gets a convenient flat view.
    """
    id: UUID
    # Computed from related tables (not stored on users table)
    subscription_tier: Optional[str] = "free"
    subscription_status: Optional[str] = "inactive"
    stripe_customer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True