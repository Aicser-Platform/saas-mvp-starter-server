"""
stripe.py
─────────
Stripe Checkout & Billing Portal endpoints.

Centralises Stripe logic in the backend so any frontend (web, mobile)
can trigger payments via a simple REST call.
"""

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.crud import subscription as crud_subscription
from app.crud import billing_account as crud_billing
from app.crud import plan as crud_plan
from app.schemas.subscription import SubscriptionUpdate

router = APIRouter(prefix="/stripe", tags=["Stripe"])


# ── Request / Response schemas ─────────────────────────────────────────────

class CreateCheckoutRequest(BaseModel):
    tier: str  # "pro" | "premium"


class CreateCheckoutResponse(BaseModel):
    checkout_url: str


class CreatePortalResponse(BaseModel):
    portal_url: str


class InvoiceResponse(BaseModel):
    id: str
    number: Optional[str] = None
    created: Optional[str] = None  # ISO timestamp
    amount_paid: int
    currency: str
    status: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    invoice_pdf: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_stripe():
    """Return a configured Stripe module, raising 500 if key is missing."""
    settings = get_settings()
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured on the server")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _get_or_create_customer(
    stripe_mod, user: User, db: Session
) -> str:
    """Get existing Stripe customer ID or create one, upserting the billing account."""
    billing = crud_billing.get_billing_account_by_user_and_provider(db, user.id, "stripe")

    if billing and billing.customer_id:
        # Verify the customer still exists in Stripe
        try:
            stripe_mod.Customer.retrieve(billing.customer_id)
            return billing.customer_id
        except stripe_mod.error.InvalidRequestError:
            pass  # Customer was deleted — create a new one

    # Create a new Stripe customer
    customer = stripe_mod.Customer.create(
        email=user.email,
        name=user.full_name or user.email,
        metadata={"user_id": str(user.id)},
    )

    # Upsert billing account so we remember the mapping
    crud_billing.upsert_billing_account(db, user.id, "stripe", customer.id)

    return customer.id


# ── Products config (matches frontend SUBSCRIPTION_PRODUCTS) ──────────────

PLAN_CONFIG = {
    "pro": {
        "name": "Pro Plan",
        "description": "For serious learners who want more",
        "price_cents": 1999,
        "currency": "usd",
    },
    "premium": {
        "name": "Premium Plan",
        "description": "Ultimate learning experience with everything unlocked",
        "price_cents": 4999,
        "currency": "usd",
    },
}


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/create-checkout", response_model=CreateCheckoutResponse)
def create_checkout_session(
    body: CreateCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe Checkout session for the requested tier.
    Returns the checkout URL — the frontend should redirect the user there.
    """
    s = _get_stripe()
    settings = get_settings()

    tier = body.tier.lower()
    if tier not in PLAN_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Must be 'pro' or 'premium'.")

    plan_cfg = PLAN_CONFIG[tier]

    # Check if user already has this tier or higher
    from app.core.feature_gate import get_user_tier, TIER_LEVELS
    current_tier = get_user_tier(db, current_user)
    if TIER_LEVELS.get(current_tier, 0) >= TIER_LEVELS.get(tier, 0):
        raise HTTPException(
            status_code=400,
            detail=f"You already have {current_tier} plan which is equal or higher than {tier}."
        )

    customer_id = _get_or_create_customer(s, current_user, db)

    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"

    session = s.checkout.Session.create(
        customer=customer_id,
        line_items=[
            {
                "price_data": {
                    "currency": plan_cfg["currency"],
                    "product_data": {
                        "name": plan_cfg["name"],
                        "description": plan_cfg["description"],
                    },
                    "unit_amount": plan_cfg["price_cents"],
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            },
        ],
        mode="subscription",
        success_url=f"{frontend_url}/dashboard/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend_url}/dashboard/subscription?canceled=true",
        metadata={
            "userId": str(current_user.id),
            "tier": tier,
        },
    )

    return CreateCheckoutResponse(checkout_url=session.url)


@router.post("/create-portal", response_model=CreatePortalResponse)
def create_portal_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe Billing Portal session so users can manage
    their subscription (cancel, change payment method, etc.).
    """
    s = _get_stripe()
    settings = get_settings()

    billing = crud_billing.get_billing_account_by_user_and_provider(db, current_user.id, "stripe")
    if not billing or not billing.customer_id:
        raise HTTPException(
            status_code=404,
            detail="No Stripe billing account found. Please subscribe to a plan first."
        )

    # Verify customer exists
    try:
        s.Customer.retrieve(billing.customer_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe customer. Please contact support."
        )

    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"

    session = s.billing_portal.Session.create(
        customer=billing.customer_id,
        return_url=f"{frontend_url}/dashboard/billing",
    )

    return CreatePortalResponse(portal_url=session.url)


@router.get("/invoices", response_model=list[InvoiceResponse])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List the current user's Stripe invoices (live from Stripe) so the Billing
    page can show date / total / status and link to the hosted invoice + PDF.
    """
    from datetime import datetime, timezone

    billing = crud_billing.get_billing_account_by_user_and_provider(db, current_user.id, "stripe")
    if not billing or not billing.customer_id:
        return []

    s = _get_stripe()
    invoices = s.Invoice.list(customer=billing.customer_id, limit=50)

    result = []
    for inv in invoices.auto_paging_iter():
        created_iso = (
            datetime.fromtimestamp(inv.created, tz=timezone.utc).isoformat()
            if getattr(inv, "created", None)
            else None
        )
        result.append(
            InvoiceResponse(
                id=inv.id,
                number=getattr(inv, "number", None),
                created=created_iso,
                amount_paid=getattr(inv, "amount_paid", 0) or 0,
                currency=getattr(inv, "currency", "usd") or "usd",
                status=getattr(inv, "status", None),
                hosted_invoice_url=getattr(inv, "hosted_invoice_url", None),
                invoice_pdf=getattr(inv, "invoice_pdf", None),
            )
        )

    return result


@router.post("/cancel-subscription")
def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Schedule the user's active subscription to cancel at the end of the current
    billing period. The user keeps full access until that date, then reverts to free.
    """
    sub = crud_subscription.get_active_subscription_by_user(db, current_user.id)
    if not sub or not sub.provider_subscription_id:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found."
        )

    from datetime import datetime, timezone

    s = _get_stripe()
    stripe_sub = s.Subscription.modify(sub.provider_subscription_id, cancel_at_period_end=True)

    period_end = None
    if getattr(stripe_sub, "current_period_end", None):
        period_end = datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.utc)

    crud_subscription.update_subscription(
        db, sub.id, SubscriptionUpdate(
            cancel_at_period_end=True,
            current_period_end=period_end,
        )
    )
    return {"message": "Subscription will cancel at the end of the billing period."}


@router.post("/resume-subscription")
def resume_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove the scheduled cancellation and keep the subscription renewing normally.
    """
    sub = crud_subscription.get_active_subscription_by_user(db, current_user.id)
    if not sub or not sub.provider_subscription_id:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found."
        )

    s = _get_stripe()
    s.Subscription.modify(sub.provider_subscription_id, cancel_at_period_end=False)

    crud_subscription.update_subscription(
        db, sub.id, SubscriptionUpdate(cancel_at_period_end=False)
    )
    return {"message": "Subscription renewal resumed."}
