from fastapi import Depends, HTTPException, APIRouter
from celery_app import celery_app
from celery.result import AsyncResult
from app.models.task import TaskStatus

router = APIRouter()


@router.get("/status", response_model=TaskStatus)
async def get_task_status(task_id: str) -> TaskStatus:
    task_details = AsyncResult(task_id)

    return TaskStatus(
        task_id=task_id,
        status=task_details.status,
    )
