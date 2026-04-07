from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse
from app.crud import course as crud_course
from app.core.security import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=List[CourseResponse])
def list_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_course.get_courses(db, skip=skip, limit=limit)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = crud_course.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/", response_model=CourseResponse, status_code=201)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return crud_course.create_course(db, course)


@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: UUID,
    updates: CourseUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    course = crud_course.update_course(db, course_id, updates)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.delete("/{course_id}", response_model=CourseResponse)
def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    course = crud_course.delete_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
