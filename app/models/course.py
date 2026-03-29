from sqlalchemy import Column, Text, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    title = Column(Text, nullable=False)
    description = Column(Text)
    content = Column(Text)
    difficulty = Column(Text)  # beginner, intermediate, advanced
    required_plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    thumbnail_url = Column(Text)
    video_url = Column(Text)
    resources = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    required_plan = relationship("Plan")

    __table_args__ = (
        CheckConstraint("difficulty = ANY (ARRAY['beginner', 'intermediate', 'advanced'])", name="ck_courses_difficulty"),
    )
