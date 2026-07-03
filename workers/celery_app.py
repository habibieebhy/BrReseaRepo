from celery import Celery
from kombu import Queue

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

    imports=(
        "workers.tasks.ingestion",
        "workers.tasks.parser",
        "workers.tasks.chunker",
        "workers.tasks.embeddings",
        "workers.tasks.storage",
    ),

    # Explicitly declare queues
    task_queues=(
        Queue("downloader"),
        Queue("parser"),
        Queue("chunker"),
        Queue("embeddings"),
        Queue("storage"),
    ),

    task_default_queue="downloader",

    task_routes={
        "workers.tasks.ingestion.test_ingestion": {
            "queue": "downloader",
        },
        "workers.tasks.parser.parse_document_task": {
            "queue": "parser",
        },
        "workers.tasks.chunker.chunk_document_task": {
            "queue": "chunker",
        },
        "workers.tasks.embeddings.generate_embeddings_task": {
            "queue": "embeddings",
        },
        "workers.tasks.storage.persist_embeddings_task": {
            "queue": "storage",
        },
    },
)