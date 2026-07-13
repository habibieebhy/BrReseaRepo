from brixta_sdk.context import PipelineContext
from core.enums import JobStatus
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from runtime.utils.logging import logger
from runtime.tasks.flow import dispatch_next


@celery.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def test_ingestion(context_data: dict):

    context = PipelineContext.from_dict(context_data)

    JobRepository.create(context)

    JobRepository.update_status(
        context.job_id,
        JobStatus.DOWNLOADING,
    )

    logger.info(
    "Downloader started | job=%s",
    context.job_id,
    )

    context.plugins = PluginLoader.resolve(context.plugins)
    context = PluginLoader.get("downloader", context.plugins).download(context)

    logger.info(
    "Downloader completed | job=%s artifact=%s",
    context.job_id,
    context.raw_path,
    )

    dispatch_next(context, "downloader")

    return str(context.raw_path)
