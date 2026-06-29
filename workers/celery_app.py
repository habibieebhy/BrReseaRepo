from celery import Celery

from shared.config import REDIS_URL

celery = Celery(
    "brixta",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery.autodiscover_tasks(["workers.tasks"])