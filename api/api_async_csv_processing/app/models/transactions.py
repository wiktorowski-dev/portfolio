from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime
from pydantic import BaseModel, UUID4

from .base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)

    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    quantity = Column(Integer, nullable=False)


class TransactionResponse(BaseModel):
    transaction_id: UUID4
    timestamp: datetime.datetime
    amount: float
    currency: str
    customer_id: UUID4
    product_id: UUID4
    quantity: int

    class Config:
        from_attributes = True


class PaginatedTransactionResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[TransactionResponse]
