from sqlalchemy.orm import Session
from uuid import UUID
from app.models.lesson_progress import LessonProgress
from app.schemas.lesson_progress import LessonProgressCreate, LessonProgressUpdate


def get_lesson_progress(db: Session, progress_id: UUID):
    return db.query(LessonProgress).filter(LessonProgress.id == progress_id).first()


def get_lesson_progress_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(LessonProgress).filter(LessonProgress.user_id == user_id).offset(skip).limit(limit).all()


def get_lesson_progress_by_user_and_lesson(db: Session, user_id: UUID, lesson_id: UUID):
    return db.query(LessonProgress).filter(
        LessonProgress.user_id == user_id, 
        LessonProgress.lesson_id == lesson_id
    ).first()


def create_lesson_progress(db: Session, progress: LessonProgressCreate):
    db_progress = LessonProgress(**progress.model_dump())
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def update_lesson_progress(db: Session, progress_id: UUID, updates: LessonProgressUpdate):
    db_progress = get_lesson_progress(db, progress_id)
    if not db_progress:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_progress, field, value)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def delete_lesson_progress(db: Session, progress_id: UUID):
    db_progress = get_lesson_progress(db, progress_id)
    if db_progress:
        db.delete(db_progress)
        db.commit()
    return db_progress
