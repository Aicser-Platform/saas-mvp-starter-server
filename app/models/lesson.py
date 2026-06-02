from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)

    title = Column(Text, nullable=False)
    content = Column(Text)
    video_url = Column(Text)
    transcript = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    resources = Column(JSONB, default=list)  # [{title, url, type}]

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    course = relationship("Course", backref="lessons")
