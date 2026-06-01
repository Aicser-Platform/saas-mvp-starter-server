from datetime import datetime, timezone
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


def upsert_lesson_progress(
    db: Session,
    user_id: UUID,
    lesson_id: UUID,
    watched_seconds: int,
    total_duration_seconds: int,
    force_complete: bool = False,
) -> tuple[LessonProgress, bool]:
    """Create or update lesson progress. Returns (progress, completion_changed)."""
    progress = get_lesson_progress_by_user_and_lesson(db, user_id, lesson_id)
    was_completed = progress.completed if progress else False

    if not progress:
        progress = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            watched_seconds=0,
            completed=False,
        )
        db.add(progress)

    # Only advance watched_seconds — never go backwards
    progress.watched_seconds = max(progress.watched_seconds or 0, watched_seconds)
    progress.last_accessed = datetime.now(timezone.utc)

    if force_complete:
        progress.completed = True
    elif total_duration_seconds > 0 and progress.watched_seconds / total_duration_seconds >= 0.9:
        progress.completed = True

    completion_changed = (not was_completed) and progress.completed

    db.commit()
    db.refresh(progress)
    return progress, completion_changed


def recalculate_course_progress(db: Session, user_id: UUID, course_id: UUID):
    """Recompute and upsert CourseProgress based on completed lessons."""
    from app.models.lesson import Lesson
    from app.models.course_progress import CourseProgress

    total = db.query(Lesson).filter(Lesson.course_id == course_id).count()

    completed = (
        db.query(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .filter(
            LessonProgress.user_id == user_id,
            Lesson.course_id == course_id,
            LessonProgress.completed == True,
        )
        .count()
    )

    percentage = round(completed / total * 100) if total > 0 else 0

    course_prog = (
        db.query(CourseProgress)
        .filter(CourseProgress.user_id == user_id, CourseProgress.course_id == course_id)
        .first()
    )

    if not course_prog:
        course_prog = CourseProgress(user_id=user_id, course_id=course_id)
        db.add(course_prog)

    course_prog.progress_percentage = percentage
    course_prog.completed = percentage == 100
    course_prog.last_accessed = datetime.now(timezone.utc)

    db.commit()
    db.refresh(course_prog)
