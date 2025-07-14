from fastapi import Depends, HTTPException, APIRouter, Query, UploadFile, File
from celery.result import AsyncResult

from app.tasks.transaction_tasks import process_transactions_file

router = APIRouter()


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str):
    ...


@router.get("/")
def list_transactions(customer_id: str = None, product_id: str = None,  page: int = Query(default=1, ge=1)):
    ...


@router.post("/upload")
async def upload_transaction_file(
    file: UploadFile = File(...)
):
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

    return {
        "status": "accepted",
        "task_id": task.id,
        "message": "File is being processed in background"
    }

