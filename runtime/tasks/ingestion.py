from brixta_sdk.context import PipelineContext
from core.enums import JobStatus
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from runtime.tasks.flow import dispatch_next
from runtime.tasks.recovery import execute_stage
from runtime.utils.logging import logger


@celery.task(bind=True)
def test_ingestion(self, context_data: dict):
    context = PipelineContext.from_dict(context_data)
    # Keeps older producers compatible while the API now creates jobs before
    # publishing so broker-orphaned jobs are visible immediately.
    JobRepository.create(context)

    def operation() -> str:
        logger.info("Downloader started | job=%s", context.job_id)
        context.plugins = PluginLoader.resolve(context.plugins)
        PluginLoader.get("downloader", context.plugins).download(context)
        logger.info(
            "Downloader completed | job=%s artifact=%s",
            context.job_id,
            context.raw_path,
        )
        dispatch_next(context, "downloader")
        return str(context.raw_path)

    return execute_stage(
        self,
        context,
        "downloader",
        JobStatus.DOWNLOADING,
        operation,
    )
