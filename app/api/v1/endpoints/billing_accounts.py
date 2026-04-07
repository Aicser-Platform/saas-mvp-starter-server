from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.db.database import get_db
from app.schemas.billing_account import BillingAccountCreate, BillingAccountUpdate, BillingAccountResponse
from app.crud import billing_account as crud_billing
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/billing-accounts", tags=["Billing Accounts"])


def _is_internal(x_internal_secret: Optional[str]) -> bool:
    return bool(x_internal_secret and x_internal_secret == get_settings().INTERNAL_API_SECRET)


@router.get("/me", response_model=List[BillingAccountResponse])
def get_my_billing_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_billing.get_billing_accounts_by_user(db, current_user.id)


@router.get("/user/{user_id}", response_model=List[BillingAccountResponse])
def list_billing_accounts_by_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return crud_billing.get_billing_accounts_by_user(db, user_id)


@router.post("/upsert", response_model=BillingAccountResponse)
def upsert_billing_account(
    user_id: UUID,
    provider: str,
    customer_id: str,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(lambda: None),
):
    """
    Create or update a billing account for a user/provider pair.
    Accepts admin JWT or X-Internal-Secret (used by Stripe actions).
    """
    if not _is_internal(x_internal_secret):
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        if current_user.id != user_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
    return crud_billing.upsert_billing_account(db, user_id, provider, customer_id)


@router.get("/{account_id}", response_model=BillingAccountResponse)
def get_billing_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = crud_billing.get_billing_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Billing account not found")
    if account.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return account


@router.post("/", response_model=BillingAccountResponse, status_code=201)
def create_billing_account(
    account: BillingAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_billing.create_billing_account(db, account)


@router.patch("/{account_id}", response_model=BillingAccountResponse)
def update_billing_account(
    account_id: UUID,
    updates: BillingAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = crud_billing.update_billing_account(db, account_id, updates)
    if not account:
        raise HTTPException(status_code=404, detail="Billing account not found")
    return account


@router.delete("/{account_id}", response_model=BillingAccountResponse)
def delete_billing_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = crud_billing.delete_billing_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Billing account not found")
    return account
