from brixta_sdk.context import PipelineContext
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from core.enums import JobStatus
from runtime.utils.logging import logger


@celery.task
def parse_document_task(context_data: dict):

    context = PipelineContext.from_dict(context_data)

    JobRepository.update_status(
    context.job_id,
    JobStatus.PARSING,
    )

    logger.info(
    "Parser started | job=%s",
    context.job_id,
    )

    logger.info(
    "Parser completed | job=%s artifact=%s",
    context.job_id,
    context.parsed_path,
    )

    context = PluginLoader.parser.parse(context)

    logger.info(
    "Parser completed | job=%s artifact=%s",
    context.job_id,
    context.parsed_path,
    )

    celery.send_task(
        "runtime.tasks.chunker.chunk_document_task",
        args=[context.to_dict()],
        queue="chunker",
    )

    return str(context.parsed_path)