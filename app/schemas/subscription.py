from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SubscriptionBase(BaseModel):
    user_id: UUID
    plan_id: UUID
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = False
    canceled_at: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    user_id: Optional[UUID] = None
    plan_id: Optional[UUID] = None
    status: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None
    canceled_at: Optional[datetime] = None


class SubscriptionResponse(SubscriptionBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
