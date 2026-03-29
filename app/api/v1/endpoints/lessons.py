from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse
from app.crud import lesson as crud_lesson

router = APIRouter(prefix="/lessons", tags=["Lessons"])


@router.get("/course/{course_id}", response_model=List[LessonResponse])
def list_lessons_by_course(course_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_lesson.get_lessons_by_course(db, course_id, skip=skip, limit=limit)


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: UUID, db: Session = Depends(get_db)):
    lesson = crud_lesson.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/", response_model=LessonResponse, status_code=201)
def create_lesson(lesson: LessonCreate, db: Session = Depends(get_db)):
    return crud_lesson.create_lesson(db, lesson)


@router.patch("/{lesson_id}", response_model=LessonResponse)
def update_lesson(lesson_id: UUID, updates: LessonUpdate, db: Session = Depends(get_db)):
    lesson = crud_lesson.update_lesson(db, lesson_id, updates)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.delete("/{lesson_id}", response_model=LessonResponse)
def delete_lesson(lesson_id: UUID, db: Session = Depends(get_db)):
    lesson = crud_lesson.delete_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson
