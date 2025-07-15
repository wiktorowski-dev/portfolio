from fastapi import Depends, HTTPException, APIRouter
from celery_app import celery_app
from celery.result import AsyncResult
from app.models.task import TaskStatus
from app.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/status", response_model=TaskStatus)
async def get_task_status(
        task_id: str,
        _ = Depends(get_current_user)
) -> TaskStatus:
    task_details = AsyncResult(task_id)

    return TaskStatus(
        task_id=task_id,
        status=task_details.status,
    )
