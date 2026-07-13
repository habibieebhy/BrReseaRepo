from celery import Celery
from kombu import Exchange, Queue
from celery.signals import task_failure

from core.config import REDIS_URL


celery = Celery(
    "brixta",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

brixta_exchange = Exchange("brixta", type="direct")


def brixta_queue(name: str) -> Queue:
    return Queue(name, exchange=brixta_exchange, routing_key=name)

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
        "runtime.tasks.reconcile",
    ),

    task_queues=(
        brixta_queue("downloader"),
        brixta_queue("parser"),
        brixta_queue("chunker"),
        brixta_queue("embeddings"),
        brixta_queue("storage"),
    ),

    task_default_queue="downloader",
    task_default_exchange="brixta",
    task_default_exchange_type="direct",
    task_default_routing_key="downloader",
    task_track_started=True,
    worker_prefetch_multiplier=1,

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
        "runtime.tasks.reconcile.reconcile_orphaned_jobs": {
            "queue": "downloader",
        },
    },

    beat_schedule={
        "dispatch-due-sources": {
            "task": "runtime.tasks.schedules.dispatch_due_sources",
            "schedule": 60.0,
        },
        "reconcile-orphaned-jobs": {
            "task": "runtime.tasks.reconcile.reconcile_orphaned_jobs",
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
        job = JobRepository.get(job_id)
        if job and not job["terminal"]:
            JobRepository.record_failure(
                job_id,
                f"Unhandled worker failure: {exception.__class__.__name__}: {exception}",
                retryable=True,
            )
        source_id = args[0].get("metadata", {}).get("source_id")
        if source_id:
            from runtime.sources.repository import SourceRepository
            SourceRepository.update(source_id, {"last_status": "failed"})
    except Exception:
        pass
