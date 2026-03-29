from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class PlanBase(BaseModel):
    name: str
    price: int
    currency: Optional[str] = "usd"
    interval: str
    max_requests: Optional[int] = None
    max_tokens: Optional[int] = None
    max_storage_bytes: Optional[int] = None


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    currency: Optional[str] = None
    interval: Optional[str] = None
    max_requests: Optional[int] = None
    max_tokens: Optional[int] = None
    max_storage_bytes: Optional[int] = None


class PlanResponse(PlanBase):
    id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
