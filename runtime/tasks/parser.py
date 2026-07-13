from brixta_sdk.context import PipelineContext
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from core.enums import JobStatus
from runtime.utils.logging import logger
from runtime.tasks.flow import dispatch_next


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

    context = PluginLoader.get("parser", context.plugins).parse(context)

    logger.info(
    "Parser completed | job=%s artifact=%s",
    context.job_id,
    context.parsed_path,
    )

    dispatch_next(context, "parser")

    return str(context.parsed_path)
