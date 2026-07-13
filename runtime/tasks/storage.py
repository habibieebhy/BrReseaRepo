from brixta_sdk.context import PipelineContext
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from core.enums import JobStatus
from runtime.utils.logging import logger


@celery.task
def persist_embeddings_task(context_data: dict):

    context = PipelineContext.from_dict(context_data)

    JobRepository.update_status(context.job_id, JobStatus.STORING)

    logger.info(
    "Storage started | job=%s",
    context.job_id,
    )

    context = PluginLoader.get("storage", context.plugins).persist(context)

    JobRepository.update_status(context.job_id, JobStatus.COMPLETED)

    logger.info(
    "Storage completed | job=%s",
    context.job_id,
    )

    return context.job_id
