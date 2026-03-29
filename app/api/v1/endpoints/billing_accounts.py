from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.billing_account import BillingAccountCreate, BillingAccountUpdate, BillingAccountResponse
from app.crud import billing_account as crud_billing_account

router = APIRouter(prefix="/billing-accounts", tags=["Billing Accounts"])


@router.get("/user/{user_id}", response_model=List[BillingAccountResponse])
def list_billing_accounts_by_user(user_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_billing_account.get_billing_accounts_by_user(db, user_id, skip=skip, limit=limit)


@router.get("/{account_id}", response_model=BillingAccountResponse)
def get_billing_account(account_id: UUID, db: Session = Depends(get_db)):
    account = crud_billing_account.get_billing_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Billing account not found")
    return account


@router.post("/", response_model=BillingAccountResponse, status_code=201)
def create_billing_account(account: BillingAccountCreate, db: Session = Depends(get_db)):
    return crud_billing_account.create_billing_account(db, account)


@router.patch("/{account_id}", response_model=BillingAccountResponse)
def update_billing_account(account_id: UUID, updates: BillingAccountUpdate, db: Session = Depends(get_db)):
    account = crud_billing_account.update_billing_account(db, account_id, updates)
    if not account:
        raise HTTPException(status_code=404, detail="Billing account not found")
    return account


@router.delete("/{account_id}", response_model=BillingAccountResponse)
def delete_billing_account(account_id: UUID, db: Session = Depends(get_db)):
    account = crud_billing_account.delete_billing_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Billing account not found")
    return account
