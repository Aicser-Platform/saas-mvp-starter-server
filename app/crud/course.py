from sqlalchemy.orm import Session
from uuid import UUID
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate


def get_course(db: Session, course_id: UUID):
    return db.query(Course).filter(Course.id == course_id).first()


def get_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Course).offset(skip).limit(limit).all()


def create_course(db: Session, course: CourseCreate):
    db_course = Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(db: Session, course_id: UUID, updates: CourseUpdate):
    db_course = get_course(db, course_id)
    if not db_course:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_course, field, value)
    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: UUID):
    db_course = get_course(db, course_id)
    if db_course:
        db.delete(db_course)
        db.commit()
    return db_course
