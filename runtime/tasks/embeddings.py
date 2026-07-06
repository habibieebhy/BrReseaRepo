from brixta_sdk.context import PipelineContext
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from core.enums import JobStatus
from runtime.utils.logging import logger


@celery.task
def generate_embeddings_task(context_data: dict):

    context = PipelineContext.from_dict(context_data)

    JobRepository.update_status(
    context.job_id,
    JobStatus.EMBEDDING,
    )

    logger.info(
    "Embedding started | job=%s",
    context.job_id,
    )

    logger.info(
    "Embedding completed | job=%s artifact=%s",
    context.job_id,
    context.embeddings_path,
    )

    context = PluginLoader.embedding.embed(context)

    logger.info(
    "Embedding completed | job=%s artifact=%s",
    context.job_id,
    context.embeddings_path,
    )

    celery.send_task(
        "runtime.tasks.storage.persist_embeddings_task",
        args=[context.to_dict()],
        queue="storage",
    )

    return str(context.embeddings_path)