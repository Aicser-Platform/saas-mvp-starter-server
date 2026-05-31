from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Dict, Any
import hmac, hashlib, json

from app.db.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.crud import user as crud_user
from app.crud import subscription as crud_subscription
from app.crud import billing_account as crud_billing
from app.core.security import get_current_user, get_current_admin, verify_supabase_token
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


def _enrich_user(user: User, db: Session) -> Dict[str, Any]:
    """
    Build the flat UserResponse dict by joining:
    - active Subscription → plan name (tier) and status
    - BillingAccount (provider='stripe') → customer_id
    """
    active_sub = crud_subscription.get_active_subscription_by_user(db, user.id)
    billing = crud_billing.get_billing_account_by_user_and_provider(db, user.id, "stripe")

    data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        # Computed from related tables
        "subscription_tier": (active_sub.plan.name.lower() if active_sub and active_sub.plan else "free"),
        "subscription_status": (active_sub.status if active_sub else "inactive"),
        "stripe_customer_id": (billing.customer_id if billing else None),
    }
    return data


# ── Auth-only endpoints ────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile (with subscription info)."""
    return _enrich_user(current_user, db)


@router.get("/admin/all", response_model=List[UserResponse])
def list_users_admin(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Admin: list all users with subscription info."""
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return [_enrich_user(u, db) for u in users]


# ── Internal secret endpoint (for Stripe webhook) ─────────────────────────

@router.get("/", response_model=List[UserResponse])
def list_users_internal(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
):
    """Internal: list users by X-Internal-Secret (used by Stripe webhook)."""
    settings = get_settings()
    if not x_internal_secret or x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(status_code=401, detail="X-Internal-Secret required")
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return [_enrich_user(u, db) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _enrich_user(user, db)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    existing = crud_user.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    created = crud_user.create_user(db, user)
    return _enrich_user(created, db)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    updates: UserUpdate,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    settings = get_settings()

    # Allow internal secret (Stripe webhook, etc.)
    if x_internal_secret and x_internal_secret == settings.INTERNAL_API_SECRET:
        user = crud_user.update_user(db, user_id, updates)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _enrich_user(user, db)

    # Otherwise require JWT
    from app.core.security import verify_supabase_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = verify_supabase_token(authorization.split(" ", 1)[1])
    requester_id = UUID(payload["sub"])
    requester = crud_user.get_user(db, requester_id)
    if not requester:
        raise HTTPException(status_code=401, detail="User not found")
    if requester.id != user_id and requester.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    user = crud_user.update_user(db, user_id, updates)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _enrich_user(user, db)


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = crud_user.delete_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _enrich_user(user, db)


# ── Self-registration sync (called by frontend after login/signup) ─────────

@router.post("/sync", response_model=UserResponse, status_code=200)
def sync_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Called by the frontend immediately after login or email confirmation.
    Verifies the JWT, then upserts the user into the local DB so they're
    always present before the dashboard tries to load them.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")

    payload = verify_supabase_token(authorization.split(" ", 1)[1])
    uid = UUID(payload["sub"])
    email = payload.get("email", "")
    full_name = (
        payload.get("user_metadata", {}).get("full_name")
        or payload.get("user_metadata", {}).get("name")
        or None
    )

    user = crud_user.get_user(db, uid)
    if not user:
        user = User(id=uid, email=email, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update email / name in case they changed in Supabase
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if changed:
            db.commit()
            db.refresh(user)

    return _enrich_user(user, db)


# ── Supabase Auth Webhook (optional, for proactive server-side sync) ──────────

@router.post("/webhook/supabase", status_code=200)
async def supabase_auth_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_internal_secret: Optional[str] = Header(None),
):
    """
    Supabase Auth webhook — fires on INSERT/UPDATE of auth.users.
    Configure in: Supabase Dashboard → Auth → Webhooks → Add webhook
      URL: https://your-domain.com/api/v1/users/webhook/supabase
      Events: User Created

    Secured via X-Internal-Secret header (same secret Stripe uses).
    """
    settings = get_settings()
    if not x_internal_secret or x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized webhook call")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Supabase sends event type and the user record
    event_type = body.get("type", "")  # "INSERT" | "UPDATE"
    record = body.get("record", {})

    user_id_str = record.get("id")
    email = record.get("email", "")
    raw_meta = record.get("raw_user_meta_data", {})
    full_name = raw_meta.get("full_name") or raw_meta.get("name") or None

    if not user_id_str:
        return {"status": "ignored", "reason": "no user id in payload"}

    try:
        uid = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user UUID")

    user = crud_user.get_user(db, uid)
    if not user:
        user = User(id=uid, email=email, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"status": "created", "user_id": str(uid)}
    else:
        return {"status": "exists", "user_id": str(uid)}