"""
feature_gate.py
───────────────
FastAPI dependency factories for plan-based feature gating.

Usage in endpoints:

    from app.core.feature_gate import require_plan

    @router.get("/premium-stuff")
    def protected(user: User = Depends(require_plan("pro"))):
        ...
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.crud import subscription as crud_subscription
from app.models.user import User


# Tier hierarchy — higher number = more access
TIER_LEVELS = {
    "free": 0,
    "pro": 1,
    "premium": 2,
}


def get_user_tier(db: Session, user: User) -> str:
    """Resolve the user's current subscription tier (plan name)."""
    active_sub = crud_subscription.get_active_subscription_by_user(db, user.id)
    if active_sub and active_sub.plan:
        return active_sub.plan.name.lower()
    return "free"


def require_plan(minimum_tier: str):
    """
    Return a FastAPI dependency that checks the current user's
    subscription tier against *minimum_tier*.

    Raises 403 if the user's tier is below the required level.
    """
    min_level = TIER_LEVELS.get(minimum_tier.lower(), 0)

    def _dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_tier = get_user_tier(db, current_user)
        user_level = TIER_LEVELS.get(user_tier, 0)

        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"This content requires a {minimum_tier} plan or higher.",
                    "required_tier": minimum_tier,
                    "current_tier": user_tier,
                },
            )
        return current_user

    return _dependency


def check_course_access(course, db: Session, user: User) -> None:
    """
    Check if a user can access a specific course based on its required_tier.
    Raises 403 if the user's tier is insufficient.
    """
    required_tier = getattr(course, "required_tier", "free") or "free"
    required_level = TIER_LEVELS.get(required_tier.lower(), 0)

    if required_level == 0:
        return  # Free courses are always accessible

    user_tier = get_user_tier(db, user)
    user_level = TIER_LEVELS.get(user_tier, 0)

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": f"This course requires a {required_tier} plan or higher.",
                "required_tier": required_tier,
                "current_tier": user_tier,
            },
        )
