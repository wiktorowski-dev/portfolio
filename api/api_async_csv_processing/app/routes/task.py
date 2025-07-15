from fastapi import Depends, HTTPException, APIRouter, Query
from celery_app import celery_app
from celery.result import AsyncResult

from app.models.task import TaskStatusResponse, TaskStatus, TaskDetailsResponse
from app.dependencies.auth import get_current_user
from app.crud import task as task_crud
from app.dependencies import db_session as db_session_dependency
from app import exceptions

router = APIRouter()


@router.get("/status", response_model=TaskStatusResponse)
async def get_task_status(
        task_id: str,
        db_session = Depends(db_session_dependency.get_db_session),
        _ = Depends(get_current_user)
) -> TaskStatusResponse:
    task_details = AsyncResult(task_id)
    task_sql_details = await task_crud.get_task_details(task_id, db_session)

    if task_sql_details is None:
        raise exceptions.MISSING_TASK

    return TaskStatusResponse(
        task_id=task_id,
        task_status=TaskStatus(
            task_id=task_details.task_id,
            status=task_details.status,
        ),
        task_details=TaskDetailsResponse.model_validate(task_sql_details)
    )


@router.get("/tasks", response_model=list[TaskDetailsResponse])
async def get_all_tasks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=5, le=100),
    db_session = Depends(db_session_dependency.get_db_session),
    _ = Depends(get_current_user)
) -> list[TaskDetailsResponse]:
    tasks = await task_crud.list_tasks(
        db_session,
        page=page,
        limit=limit
    )
    return [
        TaskDetailsResponse.model_validate(t) for t in tasks
    ]
