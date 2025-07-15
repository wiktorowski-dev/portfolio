from celery.result import AsyncResult

from celery_app.celery_worker import celery_app


async def process_transactions_file(csv_content: str) -> AsyncResult:
    result = await celery_app.send_task("transaction_tasks.process_transactions_file", args=[csv_content])
    return result

