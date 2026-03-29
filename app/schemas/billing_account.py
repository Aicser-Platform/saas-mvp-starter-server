from pydantic import BaseModel
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime


class BillingAccountBase(BaseModel):
    user_id: UUID
    provider: str
    customer_id: str
    metadata_info: Optional[Dict[str, Any]] = None


class BillingAccountCreate(BillingAccountBase):
    pass


class BillingAccountUpdate(BaseModel):
    user_id: Optional[UUID] = None
    provider: Optional[str] = None
    customer_id: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None


class BillingAccountResponse(BillingAccountBase):
    id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
