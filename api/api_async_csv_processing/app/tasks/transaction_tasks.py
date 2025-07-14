from celery import AsyncResult

from celery_app.celery_worker import celery_app


def process_transactions_file(csv_content: str) -> Task:
    task = celery_app.send_task("transaction_tasks.process_transactions_file", args=[csv_content])
    return task

