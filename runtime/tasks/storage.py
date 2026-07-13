from brixta_sdk.context import PipelineContext
from core.enums import JobStatus
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from runtime.sources.repository import SourceRepository
from runtime.tasks.recovery import execute_stage
from runtime.utils.logging import logger


@celery.task(bind=True)
def persist_embeddings_task(self, context_data: dict):
    context = PipelineContext.from_dict(context_data)

    def operation() -> str:
        logger.info("Storage started | job=%s", context.job_id)
        PluginLoader.get("storage", context.plugins).persist(context)
        source_id = context.metadata.get("source_id")
        if source_id:
            try:
                SourceRepository.update(source_id, {"last_status": "completed"})
            except Exception:
                logger.exception(
                    "Could not update source completion status | source=%s job=%s",
                    source_id,
                    context.job_id,
                )
        JobRepository.mark_completed(context.job_id)
        logger.info("Storage completed | job=%s", context.job_id)
        return context.job_id

    return execute_stage(
        self,
        context,
        "storage",
        JobStatus.STORING,
        operation,
    )
