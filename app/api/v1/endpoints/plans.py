from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.crud import plan as crud_plan

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("/", response_model=List[PlanResponse])
def list_plans(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_plan.get_plans(db, skip=skip, limit=limit)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: UUID, db: Session = Depends(get_db)):
    plan = crud_plan.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/", response_model=PlanResponse, status_code=201)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    return crud_plan.create_plan(db, plan)


@router.patch("/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: UUID, updates: PlanUpdate, db: Session = Depends(get_db)):
    plan = crud_plan.update_plan(db, plan_id, updates)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.delete("/{plan_id}", response_model=PlanResponse)
def delete_plan(plan_id: UUID, db: Session = Depends(get_db)):
    plan = crud_plan.delete_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan
