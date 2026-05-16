from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = None
    # We accept and return required_tier for frontend convenience.
    # The CRUD layer handles mapping this to plans.id
    required_tier: Optional[str] = "free"
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = None
    required_tier: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None


class CourseResponse(CourseBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
