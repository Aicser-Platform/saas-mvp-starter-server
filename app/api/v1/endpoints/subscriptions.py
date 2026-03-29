from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.crud import subscription as crud_subscription

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/user/{user_id}", response_model=List[SubscriptionResponse])
def list_subscriptions_by_user(user_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_subscription.get_subscriptions_by_user(db, user_id, skip=skip, limit=limit)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: UUID, db: Session = Depends(get_db)):
    subscription = crud_subscription.get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.post("/", response_model=SubscriptionResponse, status_code=201)
def create_subscription(subscription: SubscriptionCreate, db: Session = Depends(get_db)):
    return crud_subscription.create_subscription(db, subscription)


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(subscription_id: UUID, updates: SubscriptionUpdate, db: Session = Depends(get_db)):
    subscription = crud_subscription.update_subscription(db, subscription_id, updates)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.delete("/{subscription_id}", response_model=SubscriptionResponse)
def delete_subscription(subscription_id: UUID, db: Session = Depends(get_db)):
    subscription = crud_subscription.delete_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription
