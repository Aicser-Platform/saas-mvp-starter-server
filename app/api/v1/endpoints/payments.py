from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.crud import payment as crud_payment
from app.core.security import get_current_user, get_current_admin
from app.core.config import get_settings
from app.models.user import User
from app.models.payment import Payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", response_model=List[PaymentResponse])
def list_all_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Admin: list all payments with user info."""
    payments = db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return payments


@router.get("/me", response_model=List[PaymentResponse])
def list_my_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_payment.get_payments_by_user(db, current_user.id, skip=skip, limit=limit)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
):
    """
    Internal endpoint: called by the Stripe webhook route in Next.js.
    Protected by X-Internal-Secret header instead of user JWT.
    """
    settings = get_settings()
    if x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden: invalid internal secret")
    return crud_payment.create_payment(db, payment)
