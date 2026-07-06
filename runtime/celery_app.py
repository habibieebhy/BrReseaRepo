from celery import Celery
from kombu import Queue

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
    },
)