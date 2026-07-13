from celery import Celery
from kombu import Queue
from celery.signals import task_failure

from core.config import REDIS_URL


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

    imports=(
        "runtime.tasks.ingestion",
        "runtime.tasks.parser",
        "runtime.tasks.chunker",
        "runtime.tasks.embeddings",
        "runtime.tasks.storage",
        "runtime.tasks.schedules",
    ),

    task_queues=(
        Queue("downloader"),
        Queue("parser"),
        Queue("chunker"),
        Queue("embeddings"),
        Queue("storage"),
    ),

    task_default_queue="downloader",

    task_routes={
        "runtime.tasks.ingestion.test_ingestion": {
            "queue": "downloader",
        },
        "runtime.tasks.parser.parse_document_task": {
            "queue": "parser",
        },
        "runtime.tasks.chunker.chunk_document_task": {
            "queue": "chunker",
        },
        "runtime.tasks.embeddings.generate_embeddings_task": {
            "queue": "embeddings",
        },
        "runtime.tasks.storage.persist_embeddings_task": {
            "queue": "storage",
        },
        "runtime.tasks.schedules.dispatch_due_sources": {
            "queue": "downloader",
        },
    },

    beat_schedule={
        "dispatch-due-sources": {
            "task": "runtime.tasks.schedules.dispatch_due_sources",
            "schedule": 60.0,
        },
    },
)


@task_failure.connect
def record_pipeline_failure(sender=None, exception=None, args=None, **kwargs):
    if not args or not isinstance(args[0], dict):
        return
    job_id = args[0].get("job_id")
    if not job_id:
        return
    try:
        from runtime.jobs.repository import JobRepository
        JobRepository.record_failure(job_id, str(exception))
    except Exception:
        pass
