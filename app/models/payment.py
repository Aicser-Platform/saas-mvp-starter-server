from sqlalchemy import Column, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"))

    provider = Column(Text, nullable=False)  # stripe, aba_payway
    provider_payment_id = Column(Text, unique=True, nullable=False)

    amount = Column(Integer, nullable=False)
    currency = Column(Text, nullable=False, default="usd")

    status = Column(Text, nullable=False)  # pending, succeeded, failed, refunded
    payment_method = Column(Text)  # card, qr, bank_transfer

    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="payments")
    subscription = relationship("Subscription", backref="payments")

