from sqlalchemy.orm import Session
from uuid import UUID
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate


def get_payment(db: Session, payment_id: UUID):
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payments_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Payment).filter(Payment.user_id == user_id).offset(skip).limit(limit).all()


def get_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Payment).offset(skip).limit(limit).all()


def create_payment(db: Session, payment: PaymentCreate):
    db_payment = Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment
