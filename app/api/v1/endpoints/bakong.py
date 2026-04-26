"""
bakong.py
─────────
Bakong KHQR payment endpoints.

Generates KHQR QR codes for subscription payments, polls the Bakong API
to detect payment confirmation, and activates subscriptions on success.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.payment import Payment
from app.crud import subscription as crud_subscription
from app.crud import plan as crud_plan
from app.crud import payment as crud_payment
from app.schemas.subscription import SubscriptionCreate
from app.schemas.payment import PaymentCreate

router = APIRouter(prefix="/bakong", tags=["Bakong KHQR"])

# ── Constants ──────────────────────────────────────────────────────────────
USD_TO_KHR = 4100  # Fixed exchange rate

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


# ── Request / Response schemas ─────────────────────────────────────────────

class CreateKHQRRequest(BaseModel):
    tier: str  # "pro" | "premium"


class CreateKHQRResponse(BaseModel):
    qr_data: str
    md5: str
    payment_id: str
    amount_khr: float
    amount_usd: float


class CheckPaymentResponse(BaseModel):
    status: str  # "pending" | "paid" | "canceled" | "expired"
    tier: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_khqr():
    """Return a configured KHQR instance, raising 500 if token is missing."""
    settings = get_settings()
    if not settings.BAKONG_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Bakong KHQR is not configured on the server"
        )
    from bakong_khqr import KHQR
    return KHQR(settings.BAKONG_TOKEN)


def _get_plan_by_name(db: Session, tier: str):
    """Find a plan record by tier name."""
    plans = crud_plan.get_plans(db)
    for p in plans:
        if p.name.lower() == tier.lower():
            return p
    return None


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/create-khqr", response_model=CreateKHQRResponse)
async def create_khqr_payment(
    body: CreateKHQRRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a KHQR QR code for the requested tier.
    Returns QR data string, MD5 hash, and a pending payment ID.
    """
    settings = get_settings()
    tier = body.tier.lower()

    if tier not in PLAN_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {tier}. Must be 'pro' or 'premium'."
        )

    # Check if user already has this tier or higher
    from app.core.feature_gate import get_user_tier, TIER_LEVELS
    current_tier = get_user_tier(db, current_user)
    if TIER_LEVELS.get(current_tier, 0) >= TIER_LEVELS.get(tier, 0):
        raise HTTPException(
            status_code=400,
            detail=f"You already have {current_tier} plan which is equal or higher than {tier}."
        )

    plan_cfg = PLAN_CONFIG[tier]
    amount_usd = plan_cfg["price_cents"] / 100  # e.g. 19.99
    amount_khr = round(amount_usd * USD_TO_KHR)  # e.g. 81959

    # Generate a unique bill number for this transaction
    bill_number = f"KHQR-{uuid.uuid4().hex[:12].upper()}"

    # Generate KHQR using the bakong-khqr SDK (sync → run in thread)
    khqr = _get_khqr()

    try:
        qr_data = await asyncio.to_thread(
            khqr.create_qr,
            bank_account=settings.BAKONG_ACCOUNT,
            merchant_name="Dataticon SaaS",
            merchant_city="Phnom Penh",
            amount=amount_khr,
            currency="KHR",
            store_label="Dataticon",
            phone_number="",
            bill_number=bill_number,
            terminal_label=f"sub-{tier}",
            static=False,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate KHQR: {str(e)}"
        )

    # Generate MD5 for transaction tracking
    try:
        md5_hash = await asyncio.to_thread(khqr.generate_md5, qr_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate MD5: {str(e)}"
        )

    # Save pending payment in database
    payment_data = PaymentCreate(
        user_id=current_user.id,
        provider="bakong",
        provider_payment_id=md5_hash,
        amount=amount_khr,
        currency="khr",
        status="pending",
        payment_method="khqr",
    )
    db_payment = crud_payment.create_payment(db, payment_data)

    return CreateKHQRResponse(
        qr_data=qr_data,
        md5=md5_hash,
        payment_id=str(db_payment.id),
        amount_khr=amount_khr,
        amount_usd=amount_usd,
    )


@router.get("/check-payment/{payment_id}", response_model=CheckPaymentResponse)
async def check_khqr_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check the payment status of a pending KHQR transaction.
    If paid, automatically creates the subscription.
    """
    try:
        pid = uuid.UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID")

    payment = crud_payment.get_payment(db, pid)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Already processed
    if payment.status == "succeeded":
        return CheckPaymentResponse(status="paid")
    if payment.status in ("canceled", "failed"):
        return CheckPaymentResponse(status=payment.status)

    # Check with Bakong API
    khqr = _get_khqr()
    md5_hash = payment.provider_payment_id

    try:
        result = await asyncio.to_thread(khqr.check_payment, md5_hash)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check payment status: {str(e)}"
        )

    # The bakong-khqr check_payment returns "PAID" or "UNPAID" as a string
    is_paid = (result == "PAID")

    if not is_paid:
        return CheckPaymentResponse(status="pending")

    # ── Payment confirmed — activate subscription ──────────────────────────

    # Determine tier from payment amount
    tier = None
    for t, cfg in PLAN_CONFIG.items():
        expected_khr = round((cfg["price_cents"] / 100) * USD_TO_KHR)
        if payment.amount == expected_khr:
            tier = t
            break

    if not tier:
        # Fallback: mark as paid but log the issue
        payment.status = "succeeded"
        payment.paid_at = datetime.now(timezone.utc)
        db.commit()
        return CheckPaymentResponse(status="paid")

    # Find plan record
    plan = _get_plan_by_name(db, tier)
    if plan:
        # Create subscription
        sub_data = SubscriptionCreate(
            user_id=current_user.id,
            plan_id=plan.id,
            status="active",
            provider_subscription_id=f"bakong_{md5_hash}",
            current_period_start=datetime.now(timezone.utc),
        )
        crud_subscription.create_subscription(db, sub_data)

    # Update payment to succeeded
    payment.status = "succeeded"
    payment.paid_at = datetime.now(timezone.utc)
    db.commit()

    return CheckPaymentResponse(status="paid", tier=tier)


@router.post("/cancel-payment/{payment_id}", response_model=CheckPaymentResponse)
async def cancel_khqr_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending KHQR payment (user closed the QR dialog)."""
    try:
        pid = uuid.UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID")

    payment = crud_payment.get_payment(db, pid)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if payment.status == "pending":
        payment.status = "canceled"
        db.commit()

    return CheckPaymentResponse(status="canceled")
