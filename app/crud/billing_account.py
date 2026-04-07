from sqlalchemy.orm import Session
from uuid import UUID
from app.models.billing_account import BillingAccount
from app.schemas.billing_account import BillingAccountCreate, BillingAccountUpdate


def get_billing_account(db: Session, billing_account_id: UUID):
    return db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()


def get_billing_accounts_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(BillingAccount).filter(BillingAccount.user_id == user_id).offset(skip).limit(limit).all()


def get_billing_account_by_user_and_provider(db: Session, user_id: UUID, provider: str):
    """Return the billing account for a user/provider combo (e.g. user + 'stripe')."""
    return (
        db.query(BillingAccount)
        .filter(BillingAccount.user_id == user_id, BillingAccount.provider == provider)
        .first()
    )


def get_billing_account_by_customer_id(db: Session, customer_id: str):
    """Find a billing account by provider customer ID (e.g. Stripe cus_xxx)."""
    return db.query(BillingAccount).filter(BillingAccount.customer_id == customer_id).first()


def upsert_billing_account(db: Session, user_id: UUID, provider: str, customer_id: str):
    """Create or update a billing account for a user/provider pair."""
    existing = get_billing_account_by_user_and_provider(db, user_id, provider)
    if existing:
        existing.customer_id = customer_id
        db.commit()
        db.refresh(existing)
        return existing
    new_account = BillingAccount(user_id=user_id, provider=provider, customer_id=customer_id)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


def create_billing_account(db: Session, billing_account: BillingAccountCreate):
    db_billing_account = BillingAccount(**billing_account.model_dump())
    db.add(db_billing_account)
    db.commit()
    db.refresh(db_billing_account)
    return db_billing_account


def update_billing_account(db: Session, billing_account_id: UUID, updates: BillingAccountUpdate):
    db_billing_account = get_billing_account(db, billing_account_id)
    if not db_billing_account:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_billing_account, field, value)
    db.commit()
    db.refresh(db_billing_account)
    return db_billing_account


def delete_billing_account(db: Session, billing_account_id: UUID):
    db_billing_account = get_billing_account(db, billing_account_id)
    if db_billing_account:
        db.delete(db_billing_account)
        db.commit()
    return db_billing_account
