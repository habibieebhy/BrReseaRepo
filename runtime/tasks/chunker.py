from brixta_sdk.context import PipelineContext
from core.enums import JobStatus
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.tasks.flow import dispatch_next
from runtime.tasks.recovery import execute_stage
from runtime.utils.logging import logger


@celery.task(bind=True)
def chunk_document_task(self, context_data: dict):
    context = PipelineContext.from_dict(context_data)

    def operation() -> str:
        logger.info("Chunker started | job=%s", context.job_id)
        PluginLoader.get("chunker", context.plugins).chunk(context)
        logger.info(
            "Chunker completed | job=%s artifact=%s",
            context.job_id,
            context.chunks_path,
        )
        dispatch_next(context, "chunker")
        return str(context.chunks_path)

    return execute_stage(
        self,
        context,
        "chunker",
        JobStatus.CHUNKING,
        operation,
    )
