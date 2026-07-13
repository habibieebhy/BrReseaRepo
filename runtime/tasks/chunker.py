from brixta_sdk.context import PipelineContext
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from core.enums import JobStatus
from runtime.utils.logging import logger
from runtime.tasks.flow import dispatch_next


@celery.task
def chunk_document_task(context_data: dict):

    context = PipelineContext.from_dict(context_data)

    JobRepository.update_status(
       context.job_id,
       JobStatus.CHUNKING,
    )

    context = PluginLoader.get("chunker", context.plugins).chunk(context)

    logger.info(
    "Chunker started | job=%s",
    context.job_id,
    )

    logger.info(
    "Chunker completed | job=%s artifact=%s",
    context.job_id,
    context.chunks_path,
    )

    dispatch_next(context, "chunker")

    return str(context.chunks_path)
