from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class PaymentBase(BaseModel):
    user_id: UUID
    subscription_id: Optional[UUID] = None
    provider: str
    provider_payment_id: str
    amount: int
    currency: Optional[str] = "usd"
    status: str
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None



class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
