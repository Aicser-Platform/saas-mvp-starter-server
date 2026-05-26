from sqlalchemy.orm import Session
from uuid import UUID
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.course_progress import CourseProgress
from app.models.plan import Plan
from app.schemas.course import CourseCreate, CourseUpdate


def get_plan_id_by_name(db: Session, tier_name: str):
    if not tier_name or tier_name.lower() == "free":
        return None
    plan = db.query(Plan).filter(Plan.name.ilike(tier_name)).first()
    return plan.id if plan else None


def _enrich_course(course: Course):
    """Map required_plan.name back to required_tier for the response."""
    d = {c.name: getattr(course, c.name) for c in course.__table__.columns}
    # Always return lowercase so frontend tier maps (free/pro/premium) match
    d["required_tier"] = course.required_plan.name.lower() if course.required_plan else "free"
    # Ensure category is included (may be None if not set)
    d["category"] = course.category
    return d



def get_course(db: Session, course_id: UUID):
    course = db.query(Course).filter(Course.id == course_id).first()
    return _enrich_course(course) if course else None


def get_courses(db: Session, skip: int = 0, limit: int = 100):
    courses = db.query(Course).offset(skip).limit(limit).all()
    return [_enrich_course(c) for c in courses]


def create_course(db: Session, course: CourseCreate):
    data = course.model_dump()
    tier = data.pop("required_tier", "free")
    data["required_plan_id"] = get_plan_id_by_name(db, tier)

    db_course = Course(**data)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return _enrich_course(db_course)


def update_course(db: Session, course_id: UUID, updates: CourseUpdate):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        return None

    data = updates.model_dump(exclude_unset=True)
    if "required_tier" in data:
        tier = data.pop("required_tier")
        db_course.required_plan_id = get_plan_id_by_name(db, tier)

    for field, value in data.items():
        setattr(db_course, field, value)

    db.commit()
    db.refresh(db_course)
    return _enrich_course(db_course)


def delete_course(db: Session, course_id: UUID):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        return None

    enriched = _enrich_course(db_course)

    # Delete in FK-dependency order to avoid constraint violations:
    # 1. lesson_progress → lessons → course
    # 2. course_progress → course
    lesson_ids = db.query(Lesson.id).filter(Lesson.course_id == course_id).subquery()
    db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
    db.query(Lesson).filter(Lesson.course_id == course_id).delete(synchronize_session=False)
    db.query(CourseProgress).filter(CourseProgress.course_id == course_id).delete(synchronize_session=False)

    db.delete(db_course)
    db.commit()
    return enriched
