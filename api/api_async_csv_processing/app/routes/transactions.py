from fastapi import Depends, HTTPException, APIRouter, Query, UploadFile, File
from pydantic import UUID4
from typing import Optional

from app.models.task import TaskStatus
from app.tasks.transaction_tasks import process_transactions_file
from app.models.transactions import TransactionResponse, PaginatedTransactionResponse
from app.crud import transactions
from app.dependencies import db_session as db_session_dependency
from app import exceptions
from app.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/{transaction_id}")
async def get_transaction(
        transaction_id: UUID4,
        db_session = Depends(db_session_dependency.get_db_session),
        _ = Depends(get_current_user)
) -> TransactionResponse:
    details = await transactions.get_transaction_details(transaction_id, db_session)
    if not details:
        raise exceptions.MISSING_TRANSACTION

    return TransactionResponse.model_validate(details)


@router.get("", response_model=PaginatedTransactionResponse)
async def list_transactions(
    customer_id: Optional[UUID4] = Query(default=None),
    product_id: Optional[UUID4] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=5, le=100),
    db_session=Depends(db_session_dependency.get_db_session),
    _ = Depends(get_current_user)
):
    total, items = await transactions.list_transactions(db_session, customer_id, product_id, page, limit)

    return PaginatedTransactionResponse(
        total=total,
        page=page,
        limit=limit,
        items=[TransactionResponse.model_validate(x) for x in items],
    )


@router.post("/upload", response_model=TaskStatus)
async def upload_transaction_file(
    file: UploadFile = File(...),
    _ = Depends(get_current_user)
) -> TaskStatus:
    """
    Upload a CSV file containing transaction data.
    The file should contain columns for transaction details.
    """
    if not file.filename.endswith('.csv'):
        raise exceptions.INCORRECT_FILE_TYPE

    content = await file.read()

    task = process_transactions_file(content.decode())

    return TaskStatus(
        task_id=task.task_id,
        status=task.status,
    )
