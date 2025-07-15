from celery import Celery
import os

broker_uri = os.getenv('celery_broker_uri')

celery_app = Celery(
    "worker",
    broker=f"{broker_uri}/0",
    backend=f"{broker_uri}/0",
)

celery_app.autodiscover_tasks(["celery_app.tasks"])