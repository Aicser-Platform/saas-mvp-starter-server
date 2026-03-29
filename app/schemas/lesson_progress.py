from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class LessonProgressBase(BaseModel):
    user_id: UUID
    lesson_id: UUID
    completed: Optional[bool] = False
    watched_seconds: Optional[int] = 0
    last_accessed: Optional[datetime] = None


class LessonProgressCreate(LessonProgressBase):
    pass


class LessonProgressUpdate(BaseModel):
    user_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    completed: Optional[bool] = None
    watched_seconds: Optional[int] = None
    last_accessed: Optional[datetime] = None


class LessonProgressResponse(LessonProgressBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
