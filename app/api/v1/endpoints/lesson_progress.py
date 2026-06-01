from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.lesson_progress import (
    LessonProgressCreate,
    LessonProgressUpdate,
    LessonProgressResponse,
    LessonProgressUpsert,
    LessonProgressMarkComplete,
)
from app.crud import lesson_progress as crud_lesson_progress
from app.core.security import get_current_user
from app.models.user import User
from app.models.lesson import Lesson

router = APIRouter(prefix="/lesson-progress", tags=["Lesson Progress"])


# ── New write endpoints (registered before /{progress_id} to avoid UUID clash) ──

@router.post("/upsert", response_model=LessonProgressResponse)
def upsert_lesson_progress(
    body: LessonProgressUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.query(Lesson).filter(Lesson.id == body.lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    progress, completion_changed = crud_lesson_progress.upsert_lesson_progress(
        db,
        user_id=current_user.id,
        lesson_id=body.lesson_id,
        watched_seconds=body.watched_seconds,
        total_duration_seconds=body.total_duration_seconds,
    )
    if completion_changed:
        crud_lesson_progress.recalculate_course_progress(db, current_user.id, lesson.course_id)

    return progress


@router.post("/mark-complete", response_model=LessonProgressResponse)
def mark_lesson_complete(
    body: LessonProgressMarkComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.query(Lesson).filter(Lesson.id == body.lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    progress, completion_changed = crud_lesson_progress.upsert_lesson_progress(
        db,
        user_id=current_user.id,
        lesson_id=body.lesson_id,
        watched_seconds=0,
        total_duration_seconds=0,
        force_complete=True,
    )
    if completion_changed:
        crud_lesson_progress.recalculate_course_progress(db, current_user.id, lesson.course_id)

    return progress


# ── Read endpoints (auth fixed) ────────────────────────────────────────────────

@router.get("/user/{user_id}", response_model=List[LessonProgressResponse])
def list_lesson_progress_by_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return crud_lesson_progress.get_lesson_progress_by_user(db, user_id, skip=skip, limit=limit)


@router.get("/user/{user_id}/lesson/{lesson_id}", response_model=LessonProgressResponse)
def get_lesson_progress_by_user_and_lesson(
    user_id: UUID,
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    progress = crud_lesson_progress.get_lesson_progress_by_user_and_lesson(db, user_id, lesson_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress


@router.get("/{progress_id}", response_model=LessonProgressResponse)
def get_lesson_progress(
    progress_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    progress = crud_lesson_progress.get_lesson_progress(db, progress_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    if progress.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return progress


# ── Legacy write endpoints ─────────────────────────────────────────────────────

@router.post("/", response_model=LessonProgressResponse, status_code=201)
def create_lesson_progress(
    progress: LessonProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_lesson_progress.create_lesson_progress(db, progress)


@router.patch("/{progress_id}", response_model=LessonProgressResponse)
def update_lesson_progress(
    progress_id: UUID,
    updates: LessonProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    progress = crud_lesson_progress.update_lesson_progress(db, progress_id, updates)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress
