from sqlalchemy import Column, Integer, BigInteger, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(Text, nullable=False)  # free, pro, premium
    price = Column(Integer, nullable=False)  # in cents
    currency = Column(Text, nullable=False, default="usd")  # usd, khr
    interval = Column(Text, nullable=False)  # monthly, yearly

    # limits
    max_requests = Column(Integer)
    max_tokens = Column(Integer)
    max_storage_bytes = Column(BigInteger)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
