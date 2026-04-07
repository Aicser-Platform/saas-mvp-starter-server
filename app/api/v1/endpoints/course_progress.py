from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.db.database import get_db
from app.schemas.course_progress import CourseProgressCreate, CourseProgressUpdate, CourseProgressResponse
from app.crud import course_progress as crud_course_progress
from app.core.security import get_current_user, get_current_admin
from app.models.user import User
from app.models.course_progress import CourseProgress

router = APIRouter(prefix="/course-progress", tags=["Course Progress"])


@router.get("/", response_model=List[CourseProgressResponse])
def list_all_course_progress(
    course_id: Optional[UUID] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin: list all progress, optionally filtered by course_id."""
    query = db.query(CourseProgress)
    if course_id:
        query = query.filter(CourseProgress.course_id == course_id)
    return query.offset(skip).limit(limit).all()


@router.get("/user/{user_id}", response_model=List[CourseProgressResponse])
def list_course_progress_by_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Users can see their own; admins can see anyone's
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return crud_course_progress.get_course_progress_by_user(db, user_id, skip=skip, limit=limit)


@router.get("/user/{user_id}/course/{course_id}", response_model=CourseProgressResponse)
def get_course_progress_by_user_and_course(
    user_id: UUID,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    progress = crud_course_progress.get_course_progress_by_user_and_course(db, user_id, course_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress


@router.get("/{progress_id}", response_model=CourseProgressResponse)
def get_course_progress(
    progress_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    progress = crud_course_progress.get_course_progress(db, progress_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    if progress.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return progress


@router.post("/", response_model=CourseProgressResponse, status_code=201)
def create_course_progress(
    progress: CourseProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_course_progress.create_course_progress(db, progress)


@router.patch("/{progress_id}", response_model=CourseProgressResponse)
def update_course_progress(
    progress_id: UUID,
    updates: CourseProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    progress = crud_course_progress.update_course_progress(db, progress_id, updates)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress
