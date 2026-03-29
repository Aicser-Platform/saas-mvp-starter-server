from sqlalchemy.orm import Session
from uuid import UUID
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate


def get_lesson(db: Session, lesson_id: UUID):
    return db.query(Lesson).filter(Lesson.id == lesson_id).first()


def get_lessons_by_course(db: Session, course_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.order_index).offset(skip).limit(limit).all()


def create_lesson(db: Session, lesson: LessonCreate):
    db_lesson = Lesson(**lesson.model_dump())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def update_lesson(db: Session, lesson_id: UUID, updates: LessonUpdate):
    db_lesson = get_lesson(db, lesson_id)
    if not db_lesson:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_lesson, field, value)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def delete_lesson(db: Session, lesson_id: UUID):
    db_lesson = get_lesson(db, lesson_id)
    if db_lesson:
        db.delete(db_lesson)
        db.commit()
    return db_lesson
