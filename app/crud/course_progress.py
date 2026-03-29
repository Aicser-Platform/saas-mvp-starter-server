from sqlalchemy.orm import Session
from uuid import UUID
from app.models.course_progress import CourseProgress
from app.schemas.course_progress import CourseProgressCreate, CourseProgressUpdate


def get_course_progress(db: Session, progress_id: UUID):
    return db.query(CourseProgress).filter(CourseProgress.id == progress_id).first()


def get_course_progress_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(CourseProgress).filter(CourseProgress.user_id == user_id).offset(skip).limit(limit).all()


def get_course_progress_by_user_and_course(db: Session, user_id: UUID, course_id: UUID):
    return db.query(CourseProgress).filter(
        CourseProgress.user_id == user_id, 
        CourseProgress.course_id == course_id
    ).first()


def create_course_progress(db: Session, progress: CourseProgressCreate):
    db_progress = CourseProgress(**progress.model_dump())
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def update_course_progress(db: Session, progress_id: UUID, updates: CourseProgressUpdate):
    db_progress = get_course_progress(db, progress_id)
    if not db_progress:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_progress, field, value)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def delete_course_progress(db: Session, progress_id: UUID):
    db_progress = get_course_progress(db, progress_id)
    if db_progress:
        db.delete(db_progress)
        db.commit()
    return db_progress
