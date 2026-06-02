from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.db.database import get_db
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.crud import subscription as crud_subscription
from app.core.security import get_current_user, get_current_admin
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def _enrich_sub(sub) -> dict:
    """Add plan_name to the subscription response."""
    d = {c.name: getattr(sub, c.name) for c in sub.__table__.columns}
    d["plan_name"] = sub.plan.name if sub.plan else None
    return d


@router.get("/user/{user_id}", response_model=List[SubscriptionResponse])
def list_subscriptions_by_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    subs = crud_subscription.get_subscriptions_by_user(db, user_id, skip=skip, limit=limit)
    return [_enrich_sub(s) for s in subs]


@router.get("/me/active", response_model=SubscriptionResponse)
def get_my_active_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = crud_subscription.get_active_subscription_by_user(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    return _enrich_sub(sub)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = crud_subscription.get_subscription(db, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return _enrich_sub(sub)


@router.post("/", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(lambda: None),
):
    """Create a subscription. Accepts both admin JWT and X-Internal-Secret (webhook)."""
    settings = get_settings()
    if not (x_internal_secret and x_internal_secret == settings.INTERNAL_API_SECRET):
        if not current_user or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin or internal secret required")
    sub = crud_subscription.create_subscription(db, subscription)
    return _enrich_sub(sub)


@router.post("/cancel-active")
def cancel_active_subscription(
    body: dict,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
):
    """
    Cancel all active subscriptions for a user by user_id.
    Used as a fallback by the webhook when no provider_subscription_id match is found.
    """
    settings = get_settings()
    if not x_internal_secret or x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(status_code=403, detail="X-Internal-Secret required")

    from uuid import UUID as _UUID
    from app.schemas.subscription import SubscriptionUpdate
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    subs = crud_subscription.get_subscriptions_by_user(db, _UUID(str(user_id)))
    active = [s for s in subs if s.status in ("active", "trialing", "past_due")]
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for sub in active:
        crud_subscription.update_subscription(
            db, sub.id, SubscriptionUpdate(status="canceled", canceled_at=now)
        )
    return {"canceled": len(active)}


@router.patch("/by-provider-id/{provider_subscription_id}", response_model=SubscriptionResponse)
def update_subscription_by_provider_id(
    provider_subscription_id: str,
    updates: SubscriptionUpdate,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
):
    """
    Update a subscription by its Stripe sub_xxx ID.
    Used exclusively by the Stripe webhook (X-Internal-Secret auth).
    """
    settings = get_settings()
    if not x_internal_secret or x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(status_code=403, detail="X-Internal-Secret required")
    sub = crud_subscription.get_subscription_by_provider_id(db, provider_subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    updated = crud_subscription.update_subscription(db, sub.id, updates)
    return _enrich_sub(updated)


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: UUID,
    updates: SubscriptionUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    sub = crud_subscription.update_subscription(db, subscription_id, updates)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return _enrich_sub(sub)


@router.delete("/{subscription_id}", response_model=SubscriptionResponse)
def delete_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    sub = crud_subscription.delete_subscription(db, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return _enrich_sub(sub)
