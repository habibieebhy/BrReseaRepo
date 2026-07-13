from brixta_sdk.context import PipelineContext
from core.plugin_loader import PluginLoader, registry
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from core.enums import JobStatus
from runtime.utils.logging import logger
from runtime.tasks.flow import dispatch_next


@celery.task
def generate_embeddings_task(context_data: dict):

    context = PipelineContext.from_dict(context_data)

    JobRepository.update_status(
    context.job_id,
    JobStatus.EMBEDDING,
    )

    logger.info(
    "Embedding started | job=%s",
    context.job_id,
    )


    plugin = PluginLoader.get("embedding", context.plugins)
    model = context.config.get("embedding_model")
    profile = registry.resolve_model(context.plugins["embedding"], model)
    context.config["embedding_model"] = profile.id
    context.config["embedding_profile"] = profile.public_dict()
    internal_profile = profile.public_dict()
    internal_profile["trust_remote_code"] = profile.trust_remote_code
    context = plugin.embed(context, model=profile.id, profile=internal_profile)

    logger.info(
    "Embedding completed | job=%s artifact=%s",
    context.job_id,
    context.embeddings_path,
    )

    dispatch_next(context, "embedding")

    return str(context.embeddings_path)
