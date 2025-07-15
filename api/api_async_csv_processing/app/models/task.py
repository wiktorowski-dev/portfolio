from pydantic import BaseModel
from typing import Literal
from celery.states import ALL_STATES


class TaskStatus(BaseModel):
    task_id: str
    status: Literal[*ALL_STATES]
