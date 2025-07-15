from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid
import datetime


class Transaction(Base):
    __tablename__ = "reports"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)

    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    quantity = Column(Integer, nullable=False)
