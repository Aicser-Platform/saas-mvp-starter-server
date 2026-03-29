from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.lesson_progress import LessonProgressCreate, LessonProgressUpdate, LessonProgressResponse
from app.crud import lesson_progress as crud_lesson_progress

router = APIRouter(prefix="/lesson-progress", tags=["Lesson Progress"])


@router.get("/user/{user_id}", response_model=List[LessonProgressResponse])
def list_lesson_progress_by_user(user_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_lesson_progress.get_lesson_progress_by_user(db, user_id, skip=skip, limit=limit)


@router.get("/user/{user_id}/lesson/{lesson_id}", response_model=LessonProgressResponse)
def get_lesson_progress_by_user_and_lesson(user_id: UUID, lesson_id: UUID, db: Session = Depends(get_db)):
    progress = crud_lesson_progress.get_lesson_progress_by_user_and_lesson(db, user_id, lesson_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress


@router.get("/{progress_id}", response_model=LessonProgressResponse)
def get_lesson_progress(progress_id: UUID, db: Session = Depends(get_db)):
    progress = crud_lesson_progress.get_lesson_progress(db, progress_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress


@router.post("/", response_model=LessonProgressResponse, status_code=201)
def create_lesson_progress(progress: LessonProgressCreate, db: Session = Depends(get_db)):
    return crud_lesson_progress.create_lesson_progress(db, progress)


@router.patch("/{progress_id}", response_model=LessonProgressResponse)
def update_lesson_progress(progress_id: UUID, updates: LessonProgressUpdate, db: Session = Depends(get_db)):
    progress = crud_lesson_progress.update_lesson_progress(db, progress_id, updates)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress
