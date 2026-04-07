from sqlalchemy import Column, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)  # Same as Supabase Auth UID
    email = Column(Text, nullable=False, unique=True)
    full_name = Column(Text)
    avatar_url = Column(Text)
    role = Column(Text, default="user")  # user | admin

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("role = ANY (ARRAY['user', 'admin'])", name="ck_users_role"),
    )