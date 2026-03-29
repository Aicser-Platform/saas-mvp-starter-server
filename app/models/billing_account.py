from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class BillingAccount(Base):
    __tablename__ = "billing_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    provider = Column(Text, nullable=False)  # 'stripe', 'aba_payway', 'paypal', etc.
    customer_id = Column(Text, nullable=False)  # cus_xxx (Stripe) OR merchant ref (ABA)
    metadata_info = Column('metadata', JSONB)  # metadata is a reserved attribute in SQLAlchemy Base, so map it

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="billing_accounts")
