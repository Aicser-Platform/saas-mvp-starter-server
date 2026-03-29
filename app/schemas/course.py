from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = None
    required_plan_id: Optional[UUID] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    resources: Optional[List[Any]] = []


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = None
    required_plan_id: Optional[UUID] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    resources: Optional[List[Any]] = None


class CourseResponse(CourseBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
