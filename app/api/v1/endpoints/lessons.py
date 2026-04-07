from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List
import os
import shutil

from app.db.database import get_db
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse
from app.crud import lesson as crud_lesson
from app.core.security import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/lessons", tags=["Lessons"])

# Directory for uploaded files
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/course/{course_id}", response_model=List[LessonResponse])
def list_lessons_by_course(
    course_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_lesson.get_lessons_by_course(db, course_id, skip=skip, limit=limit)


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = crud_lesson.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/", response_model=LessonResponse, status_code=201)
def create_lesson(
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return crud_lesson.create_lesson(db, lesson)


@router.patch("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: UUID,
    updates: LessonUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    lesson = crud_lesson.update_lesson(db, lesson_id, updates)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.delete("/{lesson_id}", response_model=LessonResponse)
def delete_lesson(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    lesson = crud_lesson.delete_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/upload", summary="Upload video or PDF for a lesson")
async def upload_lesson_file(
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
):
    """
    Upload a video (.mp4, .webm) or PDF file for a lesson.
    Returns the file URL that can be stored in lesson.video_url or lesson.pdf_url.
    """
    allowed_types = {
        "video/mp4", "video/webm", "video/ogg",
        "application/pdf",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use MP4, WebM, OGG video or PDF."
        )

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Return a URL that can be served via FastAPI's static files
    file_url = f"/uploads/{unique_filename}"
    return JSONResponse({"url": file_url, "filename": unique_filename, "content_type": file.content_type})
