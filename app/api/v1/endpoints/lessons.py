from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List
from pydantic import BaseModel
import os
import shutil

from app.db.database import get_db
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse
from app.crud import lesson as crud_lesson
from app.crud import course as crud_course
from app.core.security import get_current_user, get_current_admin
from app.core.feature_gate import get_user_tier, TIER_LEVELS
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
    """List lessons for a course. Gated by the parent course's required tier."""
    course = crud_course.get_course(db, course_id)
    if course:
        required_tier = course.get("required_tier", "free") if isinstance(course, dict) else "free"
        required_level = TIER_LEVELS.get(required_tier.lower(), 0)
        if required_level > 0:
            user_tier = get_user_tier(db, current_user)
            user_level = TIER_LEVELS.get(user_tier, 0)
            if user_level < required_level:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Lessons for this course require a {required_tier} plan.",
                        "required_tier": required_tier,
                        "current_tier": user_tier,
                    },
                )
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

    # Feature gate: check parent course tier
    course = crud_course.get_course(db, lesson.course_id)
    if course:
        required_tier = course.get("required_tier", "free") if isinstance(course, dict) else "free"
        required_level = TIER_LEVELS.get(required_tier.lower(), 0)
        if required_level > 0:
            user_tier = get_user_tier(db, current_user)
            user_level = TIER_LEVELS.get(user_tier, 0)
            if user_level < required_level:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"This lesson requires a {required_tier} plan.",
                        "required_tier": required_tier,
                        "current_tier": user_tier,
                    },
                )
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


# ── Batch reorder (for drag-and-drop) ────────────────────────────────────────

class ReorderRequest(BaseModel):
    course_id: UUID
    lesson_ids: List[UUID]  # ordered list


@router.post("/reorder", summary="Batch-reorder lessons for a course")
def reorder_lessons(
    payload: ReorderRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """
    Accept an ordered list of lesson IDs and set their order_index accordingly.
    """
    for index, lesson_id in enumerate(payload.lesson_ids):
        lesson = crud_lesson.get_lesson(db, lesson_id)
        if lesson and str(lesson.course_id) == str(payload.course_id):
            lesson.order_index = index
    db.commit()
    return {"status": "ok", "order": [str(lid) for lid in payload.lesson_ids]}


# ── File upload ──────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload video, document, or image for a lesson")
async def upload_lesson_file(
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
):
    """
    Upload a video (.mp4, .webm, .ogg, .mov, .wmv), document (.pdf, .doc, .docx),
    or image (.jpg, .png, .webp, .gif) for a lesson.
    Returns the file URL that can be stored in lesson fields.
    """
    allowed_types = {
        # Video
        "video/mp4", "video/webm", "video/ogg",
        "video/quicktime",       # .mov
        "video/x-ms-wmv",        # .wmv
        # Documents
        "application/pdf",
        "application/msword",    # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        # Images
        "image/jpeg", "image/png", "image/webp", "image/gif",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. "
                   f"Supported: MP4, WebM, OGG, MOV, WMV, PDF, DOC, DOCX, JPG, PNG, WebP, GIF."
        )

    from app.core.storage import get_storage_backend, AzureBlobStorageBackend
    storage = get_storage_backend()
    result = await storage.upload(file)

    # For Azure: return a proxy URL that goes through our signed-URL endpoint
    # so the browser never hits the raw blob URL (which requires public access)
    if isinstance(storage, AzureBlobStorageBackend) and "blob_name" in result:
        result["url"] = f"/api/v1/files/{result['blob_name']}"

    return JSONResponse(result)
