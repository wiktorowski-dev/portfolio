from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from pydantic import UUID4
from typing import Literal, Optional
import datetime
import uuid
from celery.states import ALL_STATES

from .base import Base


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    correct_records_count = Column(Integer, default=0, nullable=False)
    incorrect_records_count = Column(Integer, default=0, nullable=False)


class TaskStatus(BaseModel):
    task_id: str
    status: Literal[*ALL_STATES]


class TaskDetailsResponse(BaseModel):
    task_id: UUID4
    timestamp: datetime.datetime
    correct_records_count: int
    incorrect_records_count: int

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    task_id: str
    task_status: TaskStatus
    task_details: Optional[TaskDetailsResponse] = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
