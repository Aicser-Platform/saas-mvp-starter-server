from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SubscriptionBase(BaseModel):
    user_id: UUID
    plan_id: UUID
    status: str  # active, canceled, past_due, trialing
    provider_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = False
    canceled_at: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[UUID] = None
    status: Optional[str] = None
    provider_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None
    canceled_at: Optional[datetime] = None


class SubscriptionResponse(SubscriptionBase):
    id: UUID
    # Nested plan name (tier) populated by the endpoint
    plan_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
