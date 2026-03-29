from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CourseProgressBase(BaseModel):
    user_id: UUID
    course_id: UUID
    progress_percentage: Optional[int] = 0
    completed: Optional[bool] = False
    last_accessed: Optional[datetime] = None


class CourseProgressCreate(CourseProgressBase):
    pass


class CourseProgressUpdate(BaseModel):
    user_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    progress_percentage: Optional[int] = None
    completed: Optional[bool] = None
    last_accessed: Optional[datetime] = None


class CourseProgressResponse(CourseProgressBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
