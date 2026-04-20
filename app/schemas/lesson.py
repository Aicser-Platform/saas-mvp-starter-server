from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class LessonBase(BaseModel):
    course_id: UUID
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    order_index: Optional[int] = 0
    resources: Optional[List[Any]] = []


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    course_id: Optional[UUID] = None
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    order_index: Optional[int] = None
    resources: Optional[List[Any]] = None


class LessonResponse(LessonBase):
    id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
