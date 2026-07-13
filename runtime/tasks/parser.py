from brixta_sdk.context import PipelineContext
from core.enums import JobStatus
from core.plugin_loader import PluginLoader
from runtime.celery_app import celery
from runtime.tasks.flow import dispatch_next
from runtime.tasks.recovery import execute_stage
from runtime.utils.logging import logger


@celery.task(bind=True)
def parse_document_task(self, context_data: dict):
    context = PipelineContext.from_dict(context_data)

    def operation() -> str:
        logger.info("Parser started | job=%s", context.job_id)
        PluginLoader.get("parser", context.plugins).parse(context)
        logger.info(
            "Parser completed | job=%s artifact=%s",
            context.job_id,
            context.parsed_path,
        )
        dispatch_next(context, "parser")
        return str(context.parsed_path)

    return execute_stage(
        self,
        context,
        "parser",
        JobStatus.PARSING,
        operation,
    )
