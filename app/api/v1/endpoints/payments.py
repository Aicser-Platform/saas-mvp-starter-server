from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.crud import payment as crud_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", response_model=List[PaymentResponse])
def list_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_payment.get_payments(db, skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=List[PaymentResponse])
def list_payments_by_user(user_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_payment.get_payments_by_user(db, user_id, skip=skip, limit=limit)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: UUID, db: Session = Depends(get_db)):
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    return crud_payment.create_payment(db, payment)
