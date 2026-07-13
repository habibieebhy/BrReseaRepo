from brixta_sdk.context import PipelineContext
from core.enums import JobStatus
from core.plugin_loader import PluginLoader, registry
from runtime.celery_app import celery
from runtime.tasks.flow import dispatch_next
from runtime.tasks.recovery import execute_stage
from runtime.utils.logging import logger


@celery.task(bind=True)
def generate_embeddings_task(self, context_data: dict):
    context = PipelineContext.from_dict(context_data)

    def operation() -> str:
        logger.info("Embedding started | job=%s", context.job_id)
        plugin = PluginLoader.get("embedding", context.plugins)
        profile = registry.resolve_model(
            context.plugins["embedding"],
            context.config.get("embedding_model"),
        )
        context.config["embedding_model"] = profile.id
        context.config["embedding_profile"] = profile.public_dict()
        internal_profile = profile.public_dict()
        internal_profile["trust_remote_code"] = profile.trust_remote_code
        plugin.embed(context, model=profile.id, profile=internal_profile)
        logger.info(
            "Embedding completed | job=%s artifact=%s",
            context.job_id,
            context.embeddings_path,
        )
        dispatch_next(context, "embedding")
        return str(context.embeddings_path)

    return execute_stage(
        self,
        context,
        "embedding",
        JobStatus.EMBEDDING,
        operation,
    )
