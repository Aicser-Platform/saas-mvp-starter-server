from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, database

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.create_user(db, user)
    return db_user

@router.get("/", response_model=list[schemas.User])
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    return crud.get_users(db, skip=skip, limit=limit)