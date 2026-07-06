from brixta_sdk.context import PipelineContext
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from core.enums import JobStatus
from runtime.utils.logging import logger


@celery.task
def chunk_document_task(context_data: dict):

    context = PipelineContext.from_dict(context_data)

    JobRepository.update_status(
       context.job_id,
       JobStatus.CHUNKING,
    )

    context = PluginLoader.chunker.chunk(context)

    logger.info(
    "Chunker started | job=%s",
    context.job_id,
    )

    logger.info(
    "Chunker completed | job=%s artifact=%s",
    context.job_id,
    context.chunks_path,
    )

    celery.send_task(
        "runtime.tasks.embeddings.generate_embeddings_task",
        args=[context.to_dict()],
        queue="embeddings",
    )

    return str(context.chunks_path)