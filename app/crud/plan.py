from sqlalchemy.orm import Session
from uuid import UUID
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate


def get_plan(db: Session, plan_id: UUID):
    return db.query(Plan).filter(Plan.id == plan_id).first()


def get_plans(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Plan).offset(skip).limit(limit).all()


def create_plan(db: Session, plan: PlanCreate):
    db_plan = Plan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def update_plan(db: Session, plan_id: UUID, updates: PlanUpdate):
    db_plan = get_plan(db, plan_id)
    if not db_plan:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_plan, field, value)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def delete_plan(db: Session, plan_id: UUID):
    db_plan = get_plan(db, plan_id)
    if db_plan:
        db.delete(db_plan)
        db.commit()
    return db_plan
