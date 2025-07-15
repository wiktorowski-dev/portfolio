from fastapi import Depends, HTTPException, APIRouter, Query, UploadFile, File

from app.models.task import TaskStatus
from app.tasks.transaction_tasks import process_transactions_file
from app.crud import transactions

router = APIRouter()


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str):
    return await transactions.get_transaction_details(transaction_id)


@router.get("/")
def list_transactions(customer_id: str = None, product_id: str = None,  page: int = Query(default=1, ge=1)):
    ...


@router.post("/upload", response_model=TaskStatus)
async def upload_transaction_file(
    file: UploadFile = File(...)
) -> TaskStatus:
    """
    Upload a CSV file containing transaction data.
    The file should contain columns for transaction details.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()  # Read uploaded file into memory

    # Trigger Celery background task
    task = process_transactions_file(content.decode())
    # task = process_transactions_file(content.decode())

    return TaskStatus(
        task_id=task.task_id,
        status=task.status,
    )
