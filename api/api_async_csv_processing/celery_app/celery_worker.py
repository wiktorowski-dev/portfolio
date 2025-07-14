from celery_app import celery_app
from celery_app.tasks import transaction_tasks


if __name__ == '__main__':
    celery_app.start()
