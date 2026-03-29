from sqlalchemy.orm import Session
from uuid import UUID
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


def get_subscription(db: Session, subscription_id: UUID):
    return db.query(Subscription).filter(Subscription.id == subscription_id).first()


def get_subscriptions_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Subscription).filter(Subscription.user_id == user_id).offset(skip).limit(limit).all()


def create_subscription(db: Session, subscription: SubscriptionCreate):
    db_subscription = Subscription(**subscription.model_dump())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def update_subscription(db: Session, subscription_id: UUID, updates: SubscriptionUpdate):
    db_subscription = get_subscription(db, subscription_id)
    if not db_subscription:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_subscription, field, value)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def delete_subscription(db: Session, subscription_id: UUID):
    db_subscription = get_subscription(db, subscription_id)
    if db_subscription:
        db.delete(db_subscription)
        db.commit()
    return db_subscription
